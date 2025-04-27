import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime
from dateutil.relativedelta import relativedelta
import time

from weather_service import WeatherService
from data_processor import DataProcessor
from ai_analyzer import WeatherPatternAnalyzer
from crop_recommender import CropRecommender
from utils import get_state_coordinates, cache_data, load_cached_data
import database as db

# Set page configuration
st.set_page_config(
    page_title="FarmWeather AI Advisor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2E7D32;
    }
    .subheader {
        font-size: 1.5rem;
        font-weight: 600;
        color: #388E3C;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .success-box {
        background-color: #EDF7ED;
        border-left: 6px solid #4CAF50;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    .warning-box {
        background-color: #FFF8E1;
        border-left: 6px solid #FFC107;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    .danger-box {
        background-color: #FDEDED;
        border-left: 6px solid #F44336;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'user_id' not in st.session_state:
    # Create anonymous user
    user = db.get_or_create_user()
    st.session_state.user_id = user.id

if 'location' not in st.session_state:
    # Try to load default location from DB
    default_loc = db.get_default_location(st.session_state.user_id)
    if default_loc:
        st.session_state.location = {
            "lat": default_loc.latitude,
            "lon": default_loc.longitude,
            "name": default_loc.name
        }
    else:
        st.session_state.location = None

if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = None
if 'forecast_data' not in st.session_state:
    st.session_state.forecast_data = None
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'show_advanced' not in st.session_state:
    st.session_state.show_advanced = False

# Initialize services
weather_service = WeatherService()
data_processor = DataProcessor()
pattern_analyzer = WeatherPatternAnalyzer()
crop_recommender = CropRecommender()

# Header section
st.markdown('<p class="main-header">🌱 FarmWeather AI Advisor</p>', unsafe_allow_html=True)
st.markdown("### Your personal AI assistant for agricultural planning and weather analysis")

# Create two main tabs for the application
main_tab, settings_tab = st.tabs(["FarmWeather Dashboard", "Settings"])

with settings_tab:
    st.markdown('<p class="subheader">📍 Location Settings</p>', unsafe_allow_html=True)
    
    # Get saved locations from database
    saved_locations = db.get_saved_locations(st.session_state.user_id)
    saved_location_names = ["Select a saved location"] + [loc.name for loc in saved_locations]
    
    # Let user select from saved locations
    if saved_locations:
        st.markdown("### Your Saved Locations")
        selected_saved_loc = st.selectbox("Choose from your saved locations:", 
                                         saved_location_names)
        
        if selected_saved_loc != "Select a saved location":
            selected_loc = next((loc for loc in saved_locations if loc.name == selected_saved_loc), None)
            if selected_loc and st.button("Use This Location"):
                st.session_state.location = {
                    "lat": selected_loc.latitude,
                    "lon": selected_loc.longitude,
                    "name": selected_loc.name
                }
                # Clear weather data to force refresh
                st.session_state.weather_data = None
                st.session_state.historical_data = None
                st.session_state.forecast_data = None
                st.success(f"Location set to {selected_loc.name}!")
                st.rerun()
    
    # Add a new location
    st.markdown("### Add New Location")
    location_type = st.radio("Find location by:", ("Country/Region", "Coordinates"))
    
    if location_type == "Country/Region":
        country = st.selectbox("Select Country", ["United States", "India", "Other"])
        
        if country == "United States":
            region = st.selectbox("Select State", 
                                ["Alabama", "Alaska", "Arizona", "Arkansas", "California", 
                                 "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", 
                                 "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", 
                                 "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", 
                                 "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
                                 "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", 
                                 "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", 
                                 "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", 
                                 "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", 
                                 "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"])
            subregion = st.text_input("Enter County or City (optional)")
        
        elif country == "India":
            region = st.selectbox("Select State", 
                               ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", 
                                "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", 
                                "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", 
                                "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", 
                                "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", 
                                "Uttar Pradesh", "Uttarakhand", "West Bengal",
                                "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry"])
            subregion = st.text_input("Enter District/City (optional)")
        
        else:  # Other countries
            region = st.text_input("Enter Region/Province/State")
            subregion = st.text_input("Enter City/District (optional)")
        
        location_name = st.text_input("Save this location as (e.g. 'My Farm', 'Home Field')")
        make_default = st.checkbox("Set as default location")
        
        if st.button("Add Location"):
            with st.spinner("Finding coordinates..."):
                location_query = f"{subregion + ', ' if subregion else ''}{region}, {country}"
                lat, lon = get_state_coordinates(location_query)
                if lat and lon:
                    # Save to database
                    display_name = location_name if location_name else location_query
                    db.save_location(
                        user_id=st.session_state.user_id,
                        name=display_name,
                        latitude=lat,
                        longitude=lon,
                        is_default=make_default
                    )
                    
                    # Update session state
                    st.session_state.location = {"lat": lat, "lon": lon, "name": display_name}
                    
                    # Clear weather data to force refresh
                    st.session_state.weather_data = None
                    st.session_state.historical_data = None
                    st.session_state.forecast_data = None
                    
                    st.success(f"Location saved and set to {display_name}!")
                    st.rerun()
                else:
                    st.error("Could not find coordinates for this location. Please try again with a different location name.")
    
    else:  # Coordinates option
        col1, col2 = st.columns(2)
        with col1:
            lat = st.text_input("Latitude", placeholder="e.g. 37.7749")
        with col2:
            lon = st.text_input("Longitude", placeholder="e.g. -122.4194")
        
        location_name = st.text_input("Location Name", placeholder="e.g. My Farm")
        make_default = st.checkbox("Set as default location")
        
        if st.button("Add Location"):
            try:
                lat_val = float(lat)
                lon_val = float(lon)
                name = location_name if location_name else f"Lat: {lat_val}, Lon: {lon_val}"
                
                # Save to database
                db.save_location(
                    user_id=st.session_state.user_id,
                    name=name,
                    latitude=lat_val,
                    longitude=lon_val,
                    is_default=make_default
                )
                
                # Update session state
                st.session_state.location = {"lat": lat_val, "lon": lon_val, "name": name}
                
                # Clear weather data to force refresh
                st.session_state.weather_data = None
                st.session_state.historical_data = None
                st.session_state.forecast_data = None
                
                st.success(f"Location saved and set to {name}!")
                st.rerun()
            except ValueError:
                st.error("Please enter valid coordinates (numbers only)")
    
    # Advanced settings section
    st.markdown("### Advanced Settings")
    
    show_advanced = st.checkbox("Show advanced options", value=st.session_state.show_advanced)
    st.session_state.show_advanced = show_advanced
    
    if show_advanced:
        st.markdown("##### Data Refresh Settings")
        if st.button("Clear Cache and Refresh Data"):
            if st.session_state.location:
                with st.spinner("Fetching fresh weather data..."):
                    # Clear cached data to force refresh
                    st.session_state.weather_data = None
                    st.session_state.historical_data = None
                    st.session_state.forecast_data = None
                    st.session_state.last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success("Data refreshed successfully!")
                    st.rerun()
            else:
                st.warning("Please set a location first")

with main_tab:
    if not st.session_state.location:
        # Show welcome screen with instructions
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.info("👋 Welcome to FarmWeather AI Advisor! Please set your location in the Settings tab to get started.")
        
        st.markdown("### How FarmWeather AI Advisor helps you:")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### Weather Analysis
            - Current conditions and 5-day forecasts
            - Historical weather patterns and trends
            - Extreme weather event alerts
            - Temperature and precipitation tracking
            """)
        
        with col2:
            st.markdown("""
            #### Agricultural Planning
            - Crop recommendations for your location
            - Planting and harvesting timing guidance
            - Irrigation planning based on rainfall patterns
            - Personalized farming insights
            """)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Add an image or illustration
        st.image("https://images.unsplash.com/photo-1464226184884-fa280b87c399?ixlib=rb-1.2.1&auto=format&fit=crop&w=1000&q=80", 
                caption="Growing crops with data-driven insights")
    
    else:
        # Location is set, show weather dashboard
        location = st.session_state.location
        
        try:
            # Fetch or load weather data
            if st.session_state.weather_data is None:
                # Try to load from cache first
                cached_data = load_cached_data(f"{location['lat']}_{location['lon']}_current")
                
                if cached_data:
                    st.session_state.weather_data = cached_data
                    st.session_state.last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    with st.spinner("Fetching current weather data..."):
                        current_weather = weather_service.get_current_weather(location['lat'], location['lon'])
                        st.session_state.weather_data = current_weather
                        # Cache the data
                        cache_data(f"{location['lat']}_{location['lon']}_current", current_weather)
                        st.session_state.last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Record in database for historical tracking
                        db.record_weather(
                            latitude=location['lat'],
                            longitude=location['lon'],
                            location_name=location['name'],
                            temperature=current_weather['temperature'],
                            humidity=current_weather['humidity'],
                            rainfall=current_weather.get('rain', 0),
                            description=current_weather['description']
                        )
            
            if st.session_state.forecast_data is None:
                # Try to load from cache first
                cached_forecast = load_cached_data(f"{location['lat']}_{location['lon']}_forecast")
                
                if cached_forecast:
                    st.session_state.forecast_data = cached_forecast
                else:
                    with st.spinner("Fetching forecast data..."):
                        forecast = weather_service.get_forecast(location['lat'], location['lon'])
                        st.session_state.forecast_data = forecast
                        # Cache the data
                        cache_data(f"{location['lat']}_{location['lon']}_forecast", forecast)
            
            if st.session_state.historical_data is None:
                # Try to load from cache first
                cached_historical = load_cached_data(f"{location['lat']}_{location['lon']}_historical")
                
                if cached_historical:
                    st.session_state.historical_data = cached_historical
                else:
                    with st.spinner("Fetching historical weather data..."):
                        # Get data for the past year
                        end_date = datetime.datetime.now()
                        start_date = end_date - relativedelta(years=1)
                        
                        historical = weather_service.get_historical_data(
                            location['lat'], 
                            location['lon'],
                            start_date.timestamp(),
                            end_date.timestamp()
                        )
                        
                        st.session_state.historical_data = historical
                        # Cache the data
                        cache_data(f"{location['lat']}_{location['lon']}_historical", historical)
            
            # Generate weather alerts if we have forecast data
            if st.session_state.forecast_data and not st.session_state.alerts:
                st.session_state.alerts = weather_service.get_weather_alerts(
                    location['lat'], 
                    location['lon'], 
                    st.session_state.forecast_data
                )
            
            # Show last update time
            if st.session_state.last_update:
                st.caption(f"Last updated: {st.session_state.last_update}")
            
            # Display weather information in a user-friendly format
            st.markdown(f"<p class='subheader'>Current Weather for {location['name']}</p>", unsafe_allow_html=True)
            
            # Current weather section
            current = st.session_state.weather_data
            
            # Create a multi-column layout for current weather
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Right Now")
                st.markdown(f"**Temperature:** {current['temperature']}°C")
                st.markdown(f"**Feels Like:** {current['feels_like']}°C")
                st.markdown(f"**Weather:** {current['description'].title()}")
                st.markdown(f"**Humidity:** {current['humidity']}%")
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Wind & Precipitation")
                st.markdown(f"**Wind:** {current['wind_speed']} m/s")
                
                if 'rain' in current:
                    st.markdown(f"**Rain (1h):** {current['rain']} mm")
                else:
                    st.markdown("**Rain (1h):** None")
                    
                if 'snow' in current:
                    st.markdown(f"**Snow (1h):** {current['snow']} mm")
                else:
                    st.markdown("**Snow (1h):** None")
                    
                st.markdown(f"**Cloud Cover:** {current['clouds']}%")
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col3:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Today's Range")
                st.markdown(f"**High:** {current.get('temp_max', '—')}°C")
                st.markdown(f"**Low:** {current.get('temp_min', '—')}°C")
                
                # Format sunrise and sunset times
                sunrise = datetime.datetime.fromtimestamp(current['sunrise'])
                sunset = datetime.datetime.fromtimestamp(current['sunset'])
                st.markdown(f"**Sunrise:** {sunrise.strftime('%H:%M')}")
                st.markdown(f"**Sunset:** {sunset.strftime('%H:%M')}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Display weather alerts if any
            if st.session_state.alerts:
                st.markdown("### ⚠️ Weather Alerts")
                
                for i, alert in enumerate(st.session_state.alerts):
                    severity_class = "warning-box"
                    if alert['severity'] == 'Severe':
                        severity_class = "danger-box"
                    elif alert['severity'] == 'Mild':
                        severity_class = "success-box"
                    
                    st.markdown(f"""
                    <div class="{severity_class}">
                        <h4>{alert['title']}</h4>
                        <p><strong>When:</strong> {alert['time_range']}</p>
                        <p><strong>Details:</strong> {alert['description']}</p>
                        <p><strong>Impact on Farming:</strong> {alert['agricultural_impact']}</p>
                        <p><strong>Recommendation:</strong> {alert['recommended_action']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Forecast section
            st.markdown('<p class="subheader">5-Day Forecast</p>', unsafe_allow_html=True)
            
            # Process forecast data
            forecast_data = st.session_state.forecast_data
            forecast_df = data_processor.process_forecast_data(forecast_data)
            
            # Create a line chart for temperature forecast
            st.markdown('<div class="card">', unsafe_allow_html=True)
            temp_fig = px.line(
                forecast_df, 
                x='time', 
                y=['temp', 'feels_like'], 
                title="Temperature Forecast (°C)",
                labels={'value': 'Temperature (°C)', 'time': 'Date & Time', 'variable': 'Measure'},
                color_discrete_map={'temp': 'red', 'feels_like': 'orange'}
            )
            temp_fig.update_layout(hovermode="x unified", height=400)
            st.plotly_chart(temp_fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Rain forecast in separate card
            st.markdown('<div class="card">', unsafe_allow_html=True)
            precip_fig = px.bar(
                forecast_df, 
                x='time', 
                y=['rain', 'snow'], 
                title="Precipitation Forecast (mm)",
                labels={'value': 'Precipitation (mm)', 'time': 'Date & Time', 'variable': 'Type'},
                color_discrete_map={'rain': 'blue', 'snow': 'skyblue'}
            )
            precip_fig.update_layout(hovermode="x unified", height=300)
            st.plotly_chart(precip_fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Crop recommendations section
            st.markdown('<p class="subheader">🌾 Crop Recommendations</p>', unsafe_allow_html=True)
            
            if st.session_state.historical_data:
                historical_df = data_processor.process_historical_data(st.session_state.historical_data)
                
                # Get crop recommendations based on location and weather data
                with st.spinner("Generating crop recommendations..."):
                    recommendations = crop_recommender.recommend_crops(
                        historical_df,
                        forecast_df,
                        location['lat'],
                        location['lon']
                    )
                
                if recommendations:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("### Best Crops for Your Location")
                    
                    # Create columns for each recommendation (up to 3 per row)
                    cols = st.columns(min(3, len(recommendations)))
                    
                    # Display each recommendation in a column
                    for i, rec in enumerate(recommendations[:min(6, len(recommendations))]):
                        col_idx = i % len(cols)
                        with cols[col_idx]:
                            st.markdown(f"#### {rec['crop']}")
                            st.markdown(f"**Match Score:** {rec['confidence']:.1f}%")
                            st.markdown(f"**Why:** {rec['reasons']}")
                            
                            # Add buttons to save crop preference
                            if st.button(f"Save as Favorite", key=f"fav_{rec['crop']}"):
                                db.save_crop_preference(
                                    user_id=st.session_state.user_id,
                                    crop_name=rec['crop'],
                                    is_favorite=True
                                )
                                st.success(f"Added {rec['crop']} to your favorites!")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Weather insights from AI analysis
                st.markdown('<p class="subheader">🧠 AI Weather Insights</p>', unsafe_allow_html=True)
                
                with st.spinner("Analyzing weather patterns..."):
                    analysis_results = pattern_analyzer.analyze_patterns(historical_df, forecast_df)
                
                if analysis_results and 'summary' in analysis_results:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("### Weather Pattern Analysis")
                    st.markdown(analysis_results['summary'])
                    
                    # Display trends if available
                    if 'trends' in analysis_results and analysis_results['trends']:
                        st.markdown("#### Detected Weather Trends")
                        for trend in analysis_results['trends']:
                            st.markdown(f"- {trend}")
                    
                    # Display anomalies if available
                    if 'anomalies' in analysis_results and analysis_results['anomalies']:
                        st.markdown("#### Weather Anomalies")
                        for anomaly in analysis_results['anomalies']:
                            st.markdown(f"- {anomaly}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Show some agricultural tips based on current season
                current_month = datetime.datetime.now().month
                is_northern = location['lat'] > 0
                
                if is_northern:
                    if 3 <= current_month <= 5:
                        current_season = "Spring"
                    elif 6 <= current_month <= 8:
                        current_season = "Summer"
                    elif 9 <= current_month <= 11:
                        current_season = "Fall"
                    else:
                        current_season = "Winter"
                else:
                    # Southern hemisphere seasons are opposite
                    if 3 <= current_month <= 5:
                        current_season = "Fall"
                    elif 6 <= current_month <= 8:
                        current_season = "Winter"
                    elif 9 <= current_month <= 11:
                        current_season = "Spring"
                    else:
                        current_season = "Summer"
                
                # Get seasonal recommendations
                seasonal_recommendations = pattern_analyzer.get_seasonal_recommendations(
                    current_season,
                    analysis_results.get('trends', []),
                    historical_df
                )
                
                if seasonal_recommendations:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown(f"### {current_season} Agricultural Tips")
                    
                    if 'general' in seasonal_recommendations:
                        st.markdown("#### General Recommendations")
                        for tip in seasonal_recommendations['general']:
                            st.markdown(f"- {tip}")
                    
                    if 'crops' in seasonal_recommendations:
                        st.markdown("#### Crop-Specific Advice")
                        for crop, tips in seasonal_recommendations['crops'].items():
                            st.markdown(f"**{crop}:**")
                            for tip in tips:
                                st.markdown(f"- {tip}")
                                
                    st.markdown("</div>", unsafe_allow_html=True)
                    
            else:
                st.warning("Historical weather data is being loaded. Please wait a moment for crop recommendations.")
                
        except Exception as e:
            st.error(f"An error occurred while loading weather data: {str(e)}")
            if st.button("Try Again"):
                st.session_state.weather_data = None
                st.session_state.historical_data = None
                st.session_state.forecast_data = None
                st.rerun()

# Add footer
st.markdown("""---""")
st.markdown("""
<div style="text-align: center">
    <p style="font-size: 0.8rem; color: #666;">
        FarmWeather AI Advisor | Helping farmers make data-driven decisions
    </p>
</div>
""", unsafe_allow_html=True)