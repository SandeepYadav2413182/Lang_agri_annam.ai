import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import datetime
from dateutil.relativedelta import relativedelta
import time

from weather_service import WeatherService
from data_processor import DataProcessor
from ai_analyzer import WeatherPatternAnalyzer
from crop_recommender import CropRecommender
from utils import get_state_coordinates, cache_data, load_cached_data

# Set page configuration
st.set_page_config(
    page_title="FarmWeather AI Advisor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'location' not in st.session_state:
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

# Initialize services
weather_service = WeatherService()
data_processor = DataProcessor()
pattern_analyzer = WeatherPatternAnalyzer()
crop_recommender = CropRecommender()

# Header section
st.title("🌱 FarmWeather AI Advisor")
st.markdown("### AI-powered weather insights for agricultural planning")

# Sidebar for location selection and data refresh
with st.sidebar:
    st.header("Location Settings")
    
    # Location selection
    location_type = st.radio("Select location by:", ("State/County", "Coordinates"))
    
    if location_type == "State/County":
        state = st.selectbox("Select State", 
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
        
        county = st.text_input("Enter County (optional)")
        
        if st.button("Set Location"):
            with st.spinner("Getting coordinates..."):
                lat, lon = get_state_coordinates(state, county)
                if lat and lon:
                    st.session_state.location = {"lat": lat, "lon": lon, "name": f"{county + ', ' if county else ''}{state}"}
                    st.success(f"Location set to {st.session_state.location['name']}")
                else:
                    st.error("Could not find coordinates for this location")
    
    else:  # Coordinates option
        col1, col2 = st.columns(2)
        with col1:
            lat = st.text_input("Latitude", placeholder="e.g. 37.7749")
        with col2:
            lon = st.text_input("Longitude", placeholder="e.g. -122.4194")
            
        location_name = st.text_input("Location Name (optional)", placeholder="e.g. My Farm")
        
        if st.button("Set Coordinates"):
            try:
                lat = float(lat)
                lon = float(lon)
                name = location_name if location_name else f"Lat: {lat}, Lon: {lon}"
                st.session_state.location = {"lat": lat, "lon": lon, "name": name}
                st.success(f"Location set to {st.session_state.location['name']}")
            except ValueError:
                st.error("Please enter valid coordinates")
    
    # Data refresh button
    st.header("Data Controls")
    if st.button("Refresh Weather Data"):
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
    
    # Show last update time if available
    if st.session_state.last_update:
        st.info(f"Last updated: {st.session_state.last_update}")
    
    # About section in sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("About")
    st.sidebar.info(
        """
        **FarmWeather AI Advisor** helps farmers make data-driven decisions by analyzing 
        weather patterns and providing agricultural recommendations.
        
        This application uses weather data from OpenWeatherMap and machine learning 
        to identify patterns relevant to agricultural planning.
        """
    )

# Main content area
if not st.session_state.location:
    # Show welcome screen with instructions
    st.info("👈 Please select a location from the sidebar to get started")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("What FarmWeather AI Advisor offers:")
        st.markdown("""
        - Current weather conditions and forecasts
        - Historical weather pattern analysis
        - AI-powered weather trend detection
        - Crop recommendations based on climate data
        - Weather alerts and notifications
        - Simple data visualizations for agricultural planning
        """)
    
    with col2:
        st.subheader("How it works:")
        st.markdown("""
        1. Select your location from the sidebar
        2. View current weather conditions and forecasts
        3. Check historical weather patterns analysis
        4. Get AI-powered crop recommendations
        5. Monitor alerts for extreme weather events
        6. Refresh data as needed for the latest information
        """)

else:
    # Location is set, show data and insights
    
    # Fetch or load weather data
    location = st.session_state.location
    
    try:
        # Check if we already have data or need to fetch it
        if st.session_state.weather_data is None:
            # Try to load from cache first
            cached_data = load_cached_data(f"{location['lat']}_{location['lon']}_current")
            
            if cached_data:
                st.session_state.weather_data = cached_data
            else:
                with st.spinner("Fetching current weather data..."):
                    current_weather = weather_service.get_current_weather(location['lat'], location['lon'])
                    st.session_state.weather_data = current_weather
                    # Cache the data
                    cache_data(f"{location['lat']}_{location['lon']}_current", current_weather)
        
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
                with st.spinner("Fetching historical weather data. This may take a moment..."):
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
        
        # Tab-based interface for different features
        tab1, tab2, tab3, tab4 = st.tabs([
            "Current & Forecast", 
            "Historical Analysis", 
            "AI Insights & Recommendations",
            "Weather Alerts"
        ])
        
        with tab1:
            st.header(f"Weather for {location['name']}")
            
            # Current weather section
            current = st.session_state.weather_data
            
            # Create a multi-column layout for current weather
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.subheader("Current Conditions")
                st.markdown(f"**Temperature:** {current['temperature']}°C")
                st.markdown(f"**Feels Like:** {current['feels_like']}°C")
                st.markdown(f"**Humidity:** {current['humidity']}%")
                st.markdown(f"**Wind:** {current['wind_speed']} m/s, {current['wind_direction']}°")
                
            with col2:
                st.subheader("Additional Info")
                st.markdown(f"**Pressure:** {current['pressure']} hPa")
                st.markdown(f"**Cloud Cover:** {current['clouds']}%")
                st.markdown(f"**Visibility:** {current['visibility']/1000:.1f} km")
                st.markdown(f"**Weather:** {current['description'].title()}")
                
            with col3:
                st.subheader("Sun & Precipitation")
                if 'rain' in current:
                    st.markdown(f"**Rain (1h):** {current['rain']} mm")
                else:
                    st.markdown("**Rain (1h):** None")
                    
                if 'snow' in current:
                    st.markdown(f"**Snow (1h):** {current['snow']} mm")
                else:
                    st.markdown("**Snow (1h):** None")
                    
                # Format sunrise and sunset times
                sunrise = datetime.datetime.fromtimestamp(current['sunrise'])
                sunset = datetime.datetime.fromtimestamp(current['sunset'])
                st.markdown(f"**Sunrise:** {sunrise.strftime('%H:%M')}")
                st.markdown(f"**Sunset:** {sunset.strftime('%H:%M')}")
            
            # Forecast section
            st.subheader("5-Day Forecast")
            
            # Process forecast data for plotting
            forecast_data = st.session_state.forecast_data
            forecast_df = data_processor.process_forecast_data(forecast_data)
            
            # Create a line chart for temperature forecast
            temp_fig = px.line(
                forecast_df, 
                x='time', 
                y=['temp', 'feels_like'], 
                title="Temperature Forecast (°C)",
                labels={'value': 'Temperature (°C)', 'time': 'Date & Time', 'variable': 'Measure'},
                color_discrete_map={'temp': 'red', 'feels_like': 'orange'}
            )
            temp_fig.update_layout(hovermode="x unified")
            st.plotly_chart(temp_fig, use_container_width=True)
            
            # Create a line chart for precipitation forecast
            precip_fig = px.line(
                forecast_df, 
                x='time', 
                y=['rain', 'snow'], 
                title="Precipitation Forecast (mm)",
                labels={'value': 'Precipitation (mm)', 'time': 'Date & Time', 'variable': 'Type'},
                color_discrete_map={'rain': 'blue', 'snow': 'skyblue'}
            )
            precip_fig.update_layout(hovermode="x unified")
            st.plotly_chart(precip_fig, use_container_width=True)
            
            # Create a line chart for humidity and cloud cover
            humid_cloud_fig = px.line(
                forecast_df, 
                x='time', 
                y=['humidity', 'clouds'], 
                title="Humidity & Cloud Cover (%)",
                labels={'value': 'Percentage (%)', 'time': 'Date & Time', 'variable': 'Measure'},
                color_discrete_map={'humidity': 'green', 'clouds': 'gray'}
            )
            humid_cloud_fig.update_layout(hovermode="x unified")
            st.plotly_chart(humid_cloud_fig, use_container_width=True)
            
        with tab2:
            st.header("Historical Weather Analysis")
            
            if st.session_state.historical_data:
                # Process historical data
                historical_df = data_processor.process_historical_data(st.session_state.historical_data)
                
                # Time period selector for historical data
                time_period = st.radio(
                    "Select time period:",
                    ["Past Month", "Past 3 Months", "Past 6 Months", "Past Year"],
                    horizontal=True
                )
                
                # Filter data based on selected time period
                now = datetime.datetime.now()
                if time_period == "Past Month":
                    start_date = now - relativedelta(months=1)
                elif time_period == "Past 3 Months":
                    start_date = now - relativedelta(months=3)
                elif time_period == "Past 6 Months":
                    start_date = now - relativedelta(months=6)
                else:  # Past Year
                    start_date = now - relativedelta(years=1)
                
                filtered_df = historical_df[historical_df['date'] >= start_date]
                
                # Monthly aggregation for better visualization
                monthly_df = filtered_df.resample('M', on='date').agg({
                    'temp_max': 'max',
                    'temp_min': 'min',
                    'temp_avg': 'mean',
                    'rain_sum': 'sum',
                    'humidity_avg': 'mean'
                }).reset_index()
                
                # Temperature trends
                st.subheader("Temperature Trends")
                temp_trends = px.line(
                    filtered_df, 
                    x='date', 
                    y=['temp_max', 'temp_min', 'temp_avg'],
                    title="Temperature Trends",
                    labels={'value': 'Temperature (°C)', 'date': 'Date', 'variable': 'Measure'},
                    color_discrete_map={
                        'temp_max': 'red',
                        'temp_min': 'blue',
                        'temp_avg': 'green'
                    }
                )
                temp_trends.update_layout(hovermode="x unified")
                st.plotly_chart(temp_trends, use_container_width=True)
                
                # Precipitation analysis
                st.subheader("Precipitation Analysis")
                
                # Monthly precipitation bar chart
                monthly_rain = px.bar(
                    monthly_df,
                    x='date',
                    y='rain_sum',
                    title="Monthly Precipitation",
                    labels={'rain_sum': 'Total Rainfall (mm)', 'date': 'Month'}
                )
                st.plotly_chart(monthly_rain, use_container_width=True)
                
                # Calculate and display statistics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Temperature Statistics")
                    st.markdown(f"**Average Temperature:** {filtered_df['temp_avg'].mean():.1f}°C")
                    st.markdown(f"**Maximum Temperature:** {filtered_df['temp_max'].max():.1f}°C")
                    st.markdown(f"**Minimum Temperature:** {filtered_df['temp_min'].min():.1f}°C")
                    st.markdown(f"**Temperature Range:** {filtered_df['temp_max'].max() - filtered_df['temp_min'].min():.1f}°C")
                
                with col2:
                    st.subheader("Precipitation Statistics")
                    st.markdown(f"**Total Rainfall:** {filtered_df['rain_sum'].sum():.1f} mm")
                    st.markdown(f"**Average Monthly Rainfall:** {monthly_df['rain_sum'].mean():.1f} mm")
                    st.markdown(f"**Maximum Daily Rainfall:** {filtered_df['rain_sum'].max():.1f} mm")
                    st.markdown(f"**Rainy Days:** {(filtered_df['rain_sum'] > 0).sum()} days")
                
                # Humidity analysis
                st.subheader("Humidity Analysis")
                humidity_fig = px.line(
                    filtered_df,
                    x='date',
                    y='humidity_avg',
                    title="Average Humidity Trends",
                    labels={'humidity_avg': 'Humidity (%)', 'date': 'Date'}
                )
                st.plotly_chart(humidity_fig, use_container_width=True)
                
                # Calculate seasonal averages if we have enough data
                if len(filtered_df) > 30:
                    st.subheader("Seasonal Analysis")
                    
                    # Add season column to the dataframe
                    filtered_df['season'] = filtered_df['date'].dt.month.apply(
                        lambda month: 'Winter' if month in [12, 1, 2] 
                        else 'Spring' if month in [3, 4, 5]
                        else 'Summer' if month in [6, 7, 8]
                        else 'Fall'
                    )
                    
                    # Group by season
                    seasonal_df = filtered_df.groupby('season').agg({
                        'temp_avg': 'mean',
                        'rain_sum': 'sum',
                        'humidity_avg': 'mean'
                    }).reset_index()
                    
                    # Ensure seasons are in correct order
                    season_order = {'Winter': 0, 'Spring': 1, 'Summer': 2, 'Fall': 3}
                    seasonal_df['season_order'] = seasonal_df['season'].map(season_order)
                    seasonal_df = seasonal_df.sort_values('season_order').drop('season_order', axis=1)
                    
                    # Create a multi-measure bar chart for seasonal comparison
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=seasonal_df['season'],
                        y=seasonal_df['temp_avg'],
                        name='Avg. Temperature (°C)',
                        marker_color='crimson'
                    ))
                    
                    fig.add_trace(go.Bar(
                        x=seasonal_df['season'],
                        y=seasonal_df['humidity_avg'],
                        name='Avg. Humidity (%)',
                        marker_color='royalblue'
                    ))
                    
                    # Add rainfall with secondary y-axis
                    fig.add_trace(go.Bar(
                        x=seasonal_df['season'],
                        y=seasonal_df['rain_sum'],
                        name='Total Rainfall (mm)',
                        marker_color='lightgreen',
                        yaxis='y2'
                    ))
                    
                    # Set titles and layout
                    fig.update_layout(
                        title='Seasonal Weather Comparison',
                        xaxis_title='Season',
                        yaxis_title='Temperature (°C) / Humidity (%)',
                        yaxis2=dict(
                            title='Rainfall (mm)',
                            overlaying='y',
                            side='right'
                        ),
                        barmode='group'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Historical data is being loaded. Please wait or check your internet connection.")
            
        with tab3:
            st.header("AI Insights & Crop Recommendations")
            
            # Weather pattern analysis
            if st.session_state.historical_data and st.session_state.forecast_data:
                # Process data for AI analysis
                historical_df = data_processor.process_historical_data(st.session_state.historical_data)
                forecast_df = data_processor.process_forecast_data(st.session_state.forecast_data)
                
                with st.spinner("AI analyzing weather patterns..."):
                    # Get weather pattern insights
                    pattern_insights = pattern_analyzer.analyze_patterns(historical_df, forecast_df)
                    
                    # Display pattern insights
                    st.subheader("Weather Pattern Insights")
                    st.markdown(pattern_insights['summary'])
                    
                    # Display detected anomalies if any
                    if pattern_insights['anomalies']:
                        st.warning("**Detected Weather Anomalies:**")
                        for anomaly in pattern_insights['anomalies']:
                            st.markdown(f"- {anomaly}")
                    
                    # Display weather trends
                    st.subheader("Detected Weather Trends")
                    for trend in pattern_insights['trends']:
                        st.markdown(f"- {trend}")
                    
                # Crop recommendations
                st.subheader("Crop Recommendations")
                
                # Let user choose existing crops or get recommendations
                recommendation_type = st.radio(
                    "Select recommendation type:",
                    ["Get crop suggestions for my region", "Optimize for specific crops"],
                    horizontal=True
                )
                
                if recommendation_type == "Get crop suggestions for my region":
                    with st.spinner("Generating crop recommendations based on weather patterns..."):
                        # Get top crop recommendations
                        crop_recs = crop_recommender.recommend_crops(
                            historical_df, 
                            forecast_df,
                            location['lat'], 
                            location['lon']
                        )
                        
                        # Display recommendations
                        st.markdown("**Top recommended crops for your region:**")
                        
                        # Create a table for crop recommendations
                        rec_df = pd.DataFrame(crop_recs)
                        
                        # Format the confidence scores as percentages
                        rec_df['confidence'] = rec_df['confidence'].apply(lambda x: f"{x:.0f}%")
                        
                        # Style the dataframe
                        st.dataframe(
                            rec_df,
                            column_config={
                                "crop": "Crop",
                                "confidence": "Confidence",
                                "reasons": "Reasoning"
                            },
                            hide_index=True
                        )
                
                else:  # Optimize for specific crops
                    # Let user select specific crops
                    selected_crops = st.multiselect(
                        "Select crops you're interested in:",
                        crop_recommender.available_crops
                    )
                    
                    if selected_crops:
                        with st.spinner("Analyzing optimal conditions for selected crops..."):
                            # Get optimization recommendations for selected crops
                            crop_insights = crop_recommender.get_crop_insights(
                                selected_crops,
                                historical_df,
                                forecast_df
                            )
                            
                            # Display insights for each crop
                            for crop, insight in crop_insights.items():
                                with st.expander(f"Insights for {crop}", expanded=True):
                                    st.markdown(f"**Overall suitability:** {insight['suitability']}")
                                    st.markdown(f"**Key insights:** {insight['summary']}")
                                    
                                    # Create two columns for challenges and recommendations
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("**Potential challenges:**")
                                        for challenge in insight['challenges']:
                                            st.markdown(f"- {challenge}")
                                    
                                    with col2:
                                        st.markdown("**Recommendations:**")
                                        for rec in insight['recommendations']:
                                            st.markdown(f"- {rec}")
                    else:
                        st.info("Please select at least one crop to get insights")
                
                # Additional agricultural planning insights
                st.subheader("Agricultural Planning Calendar")
                
                # Get current month and season
                current_month = datetime.datetime.now().month
                current_season = "Winter" if current_month in [12, 1, 2] else "Spring" if current_month in [3, 4, 5] else "Summer" if current_month in [6, 7, 8] else "Fall"
                
                # Generate seasonal planning recommendations
                seasonal_recs = pattern_analyzer.get_seasonal_recommendations(
                    current_season,
                    pattern_insights['trends'],
                    historical_df
                )
                
                # Display seasonal recommendations
                st.markdown(f"**Current season: {current_season}**")
                st.markdown(seasonal_recs['summary'])
                
                # Create a multi-column layout for monthly tasks
                cols = st.columns(3)
                for i, (month, tasks) in enumerate(seasonal_recs['monthly_tasks'].items()):
                    with cols[i % 3]:
                        st.markdown(f"**{month} Tasks:**")
                        for task in tasks:
                            st.markdown(f"- {task}")
            else:
                st.info("Weather data is still loading. AI insights will be available once the data is loaded.")
            
        with tab4:
            st.header("Weather Alerts & Notifications")
            
            # Generate alerts based on forecast and historical data
            if st.session_state.forecast_data:
                # Process alerts
                alerts = weather_service.get_weather_alerts(
                    location['lat'], 
                    location['lon'], 
                    st.session_state.forecast_data
                )
                
                if alerts:
                    st.session_state.alerts = alerts
                
                # Display alerts
                if st.session_state.alerts:
                    # Count alerts by severity
                    severe_count = sum(1 for alert in st.session_state.alerts if alert['severity'] == 'Severe')
                    moderate_count = sum(1 for alert in st.session_state.alerts if alert['severity'] == 'Moderate')
                    mild_count = sum(1 for alert in st.session_state.alerts if alert['severity'] == 'Mild')
                    
                    # Create alert summary
                    st.subheader("Active Weather Alerts")
                    
                    # Alert counters in columns
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if severe_count > 0:
                            st.error(f"⚠️ Severe Alerts: {severe_count}")
                        else:
                            st.success("✅ No Severe Alerts")
                    
                    with col2:
                        if moderate_count > 0:
                            st.warning(f"⚠️ Moderate Alerts: {moderate_count}")
                        else:
                            st.success("✅ No Moderate Alerts")
                    
                    with col3:
                        if mild_count > 0:
                            st.info(f"ℹ️ Mild Alerts: {mild_count}")
                        else:
                            st.success("✅ No Mild Alerts")
                    
                    # Show each alert with appropriate styling based on severity
                    for alert in st.session_state.alerts:
                        if alert['severity'] == 'Severe':
                            with st.error():
                                st.markdown(f"**{alert['title']}**")
                                st.markdown(f"**Time Period:** {alert['time_range']}")
                                st.markdown(f"**Description:** {alert['description']}")
                                st.markdown(f"**Agricultural Impact:** {alert['agricultural_impact']}")
                                st.markdown(f"**Recommended Action:** {alert['recommended_action']}")
                        
                        elif alert['severity'] == 'Moderate':
                            with st.warning():
                                st.markdown(f"**{alert['title']}**")
                                st.markdown(f"**Time Period:** {alert['time_range']}")
                                st.markdown(f"**Description:** {alert['description']}")
                                st.markdown(f"**Agricultural Impact:** {alert['agricultural_impact']}")
                                st.markdown(f"**Recommended Action:** {alert['recommended_action']}")
                        
                        else:  # Mild
                            with st.info():
                                st.markdown(f"**{alert['title']}**")
                                st.markdown(f"**Time Period:** {alert['time_range']}")
                                st.markdown(f"**Description:** {alert['description']}")
                                st.markdown(f"**Agricultural Impact:** {alert['agricultural_impact']}")
                                st.markdown(f"**Recommended Action:** {alert['recommended_action']}")
                else:
                    st.success("✅ No active weather alerts for your location")
                
                # Alert settings
                st.subheader("Alert Settings")
                
                # Allow users to set threshold preferences
                st.markdown("Set thresholds for when you want to receive alerts:")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    temp_high = st.slider("High Temperature Alert (°C)", 
                                         min_value=25, max_value=50, value=35,
                                         help="Alert when temperature exceeds this value")
                    
                    temp_low = st.slider("Low Temperature Alert (°C)",
                                        min_value=-20, max_value=15, value=0,
                                        help="Alert when temperature falls below this value")
                
                with col2:
                    rain_threshold = st.slider("Heavy Rain Alert (mm/day)",
                                             min_value=10, max_value=100, value=25,
                                             help="Alert when daily rainfall exceeds this value")
                    
                    wind_threshold = st.slider("Strong Wind Alert (m/s)",
                                             min_value=5, max_value=30, value=10,
                                             help="Alert when wind speed exceeds this value")
                
                # Save settings button
                if st.button("Save Alert Settings"):
                    st.success("Alert settings saved successfully!")
                    # In a real app, this would save to a database or user profile
            else:
                st.info("Weather data is still loading. Alerts will be available once data is loaded.")
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try selecting a different location or refreshing the data")
