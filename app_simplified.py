import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime
from dateutil.relativedelta import relativedelta
import time
import json
import random
from streamlit_chat import message

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
    st.session_state.user_id = user['id']  # Access as dictionary

if 'location' not in st.session_state:
    # Try to load default location from DB
    default_loc = db.get_default_location(st.session_state.user_id)
    if default_loc:
        st.session_state.location = {
            "lat": default_loc['latitude'],  # Access as dictionary
            "lon": default_loc['longitude'],  # Access as dictionary
            "name": default_loc['name']  # Access as dictionary
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

# Initialize chat session variables
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Create a function for the chatbot responses
def get_chatbot_response(user_input, location_data=None, weather_data=None):
    farming_tips = [
        "Remember to monitor soil moisture regularly for optimal crop growth.",
        "Crop rotation helps prevent soil depletion and reduces pest problems.",
        "Early morning is the best time to water plants to minimize evaporation.",
        "Consider using mulch to conserve soil moisture and suppress weeds.",
        "Regular pruning promotes healthier plant growth and better yields.",
        "Integrated pest management can reduce the need for chemical pesticides.",
        "Companion planting can enhance growth and naturally repel pests.",
        "Adding organic matter improves soil structure and fertility.",
        "Proper spacing between plants ensures good air circulation and reduces disease.",
        "Harvesting at the right time is crucial for flavor and storage life."
    ]
    
    weather_phrases = [
        "Let me check the weather data for you.",
        "Based on the current forecast, you should plan accordingly.",
        "The weather conditions seem favorable for fieldwork.",
        "Keep an eye on the forecast for planning your farm activities.",
        "Weather patterns suggest you might want to adjust your irrigation schedule."
    ]
    
    greeting_inputs = ["hello", "hi", "greetings", "hey", "howdy", "hola"]
    greeting_responses = [
        "Hello! How can I help with your farming needs today?",
        "Hi there! What farming information are you looking for?",
        "Greetings! I'm your FarmWeather assistant. How can I help?",
        "Hey! What farming questions do you have today?"
    ]
    
    weather_queries = ["weather", "forecast", "rain", "temperature", "humidity", "wind", "precipitation"]
    crop_queries = ["crop", "plant", "grow", "seed", "harvest", "yield", "sow"]
    
    # Normalize input
    user_input_lower = user_input.lower()
    
    # Check for greetings
    if any(greeting in user_input_lower for greeting in greeting_inputs):
        return random.choice(greeting_responses)
    
    # Check for weather-related queries
    elif any(query in user_input_lower for query in weather_queries):
        if location_data and weather_data:
            temp = weather_data.get('temperature', 'unknown')
            desc = weather_data.get('description', 'unknown conditions')
            return f"The current weather in {location_data['name']} shows {temp}°C with {desc}. Would you like more detailed weather information?"
        else:
            return "To provide weather information, please set your location first in the Settings tab."
    
    # Check for crop-related queries
    elif any(query in user_input_lower for query in crop_queries):
        if location_data:
            return f"For your location in {location_data['name']}, I can provide crop recommendations. Would you like to see them in the main dashboard?"
        else:
            return "I can provide crop recommendations based on your location. Please set your location first in the Settings tab."
    
    # Default responses with farming tips
    else:
        if "tip" in user_input_lower or "advice" in user_input_lower:
            return f"Here's a farming tip: {random.choice(farming_tips)}"
        else:
            return f"I'm here to help with weather and farming information. You can ask about weather, crops, or request farming tips. If you need to set your location, please go to the Settings tab."

# Create main tabs for the application
main_tab, profile_tab, chat_tab, settings_tab = st.tabs(["FarmWeather Dashboard", "Profile & Menu", "Chat Assistant", "Settings"])

# Profile & Menu tab
with profile_tab:
    st.markdown('<p class="subheader">👨‍🌾 Farmer Profile & Quick Navigation</p>', unsafe_allow_html=True)
    
    # User profile section
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Your Farming Profile")
    
    # Basic profile information
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://img.icons8.com/color/96/000000/farm.png", width=100)
    
    with col2:
        # Get user name or let them set it
        user_name = st.text_input("Your Name", 
                                 value="Farmer" if not db.get_or_create_user(user_id=st.session_state.user_id).get('name') else 
                                 db.get_or_create_user(user_id=st.session_state.user_id).get('name'))
        
        if st.button("Update Profile"):
            # Update user profile
            db.get_or_create_user(name=user_name)
            st.success("Profile updated successfully!")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Quick navigation menu
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Quick Navigation")
    
    menu_cols = st.columns(2)
    with menu_cols[0]:
        if st.button("📊 Weather Dashboard", use_container_width=True):
            # Use Streamlit's URL parameters to switch tabs
            st.session_state.active_tab = "main_tab"
            st.rerun()
        
        if st.button("🌱 Crop Recommendations", use_container_width=True):
            # Set state to scroll to crop section
            st.session_state.scroll_to_crops = True
            st.session_state.active_tab = "main_tab"
            st.rerun()
    
    with menu_cols[1]:
        if st.button("💬 Chat Assistant", use_container_width=True):
            st.session_state.active_tab = "chat_tab"
            st.rerun()
        
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.active_tab = "settings_tab"
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Recent activity or saved items
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Recent Activity")
    
    # Show saved locations
    st.markdown("#### Your Saved Locations")
    saved_locations = db.get_saved_locations(st.session_state.user_id)
    
    if saved_locations:
        for i, loc in enumerate(saved_locations):
            if i < 3:  # Show only 3 most recent
                st.markdown(f"- **{loc['name']}** ({loc['latitude']:.4f}, {loc['longitude']:.4f})")
        
        if len(saved_locations) > 3:
            st.markdown(f"*...and {len(saved_locations)-3} more*")
    else:
        st.info("No saved locations yet. Add locations in the Settings tab.")
    
    # Show recently searched crops
    crop_preferences = db.get_crop_preferences(st.session_state.user_id)
    if crop_preferences:
        st.markdown("#### Recent Crops")
        for i, crop in enumerate(crop_preferences):
            if i < 3:  # Show only 3 most recent
                st.markdown(f"- **{crop['crop_name']}**" + (" ⭐" if crop['is_favorite'] else ""))
    
    st.markdown("</div>", unsafe_allow_html=True)

# Chat Assistant tab
with chat_tab:
    st.markdown('<p class="subheader">💬 FarmWeather Chat Assistant</p>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
    Ask me anything about:
    - Weather forecasts and conditions
    - Crop recommendations for your location
    - Farming tips and best practices
    - Seasonal planning advice
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Container for chat messages
    chat_container = st.container()
    
    # Input field for user messages
    user_input = st.text_input("Type your message here...", key="user_message")
    
    # Handle user input
    if st.button("Send") or user_input:
        if user_input:
            # Add user input to past messages
            st.session_state.past.append(user_input)
            
            # Generate response
            response = get_chatbot_response(user_input, 
                                           location_data=st.session_state.location, 
                                           weather_data=st.session_state.weather_data)
            
            # Add response to generated messages
            st.session_state.generated.append(response)
            
            # Add to chat history
            st.session_state.chat_history.append((user_input, response))
            
            # Clear input field
            st.session_state.user_message = ""
    
    # Display chat messages
    with chat_container:
        if st.session_state['generated']:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state['past'][i], is_user=True, key=f"user_{i}")
                message(st.session_state['generated'][i], key=f"bot_{i}")
        else:
            st.info("Send a message to start chatting with the FarmWeather Assistant!")

# Settings tab
with settings_tab:
    st.markdown('<p class="subheader">📍 Location Settings</p>', unsafe_allow_html=True)
    
    # Get saved locations from database
    saved_locations = db.get_saved_locations(st.session_state.user_id)
    saved_location_names = ["Select a saved location"] + [loc['name'] for loc in saved_locations]
    
    # Let user select from saved locations
    if saved_locations:
        st.markdown("### Your Saved Locations")
        selected_saved_loc = st.selectbox("Choose from your saved locations:", 
                                         saved_location_names)
        
        if selected_saved_loc != "Select a saved location":
            selected_loc = next((loc for loc in saved_locations if loc['name'] == selected_saved_loc), None)
            if selected_loc and st.button("Use This Location"):
                st.session_state.location = {
                    "lat": selected_loc['latitude'],
                    "lon": selected_loc['longitude'],
                    "name": selected_loc['name']
                }
                # Clear weather data to force refresh
                st.session_state.weather_data = None
                st.session_state.historical_data = None
                st.session_state.forecast_data = None
                st.success(f"Location set to {selected_loc['name']}!")
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