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
from soil_moisture_service import soil_moisture_service

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

# Language setting - default to English
if 'language' not in st.session_state:
    st.session_state.language = "English"  # Options: "English", "中文" (Chinese), "हिंदी" (Hindi)

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

# Initialize soil moisture variables if they don't exist
if 'soil_moisture_simulation_running' not in st.session_state:
    st.session_state.soil_moisture_simulation_running = False
if 'soil_moisture_readings' not in st.session_state:
    st.session_state.soil_moisture_readings = []
if 'last_soil_update' not in st.session_state:
    st.session_state.last_soil_update = None

# Create main tabs for the application
main_tab, soil_tab, profile_tab, chat_tab, settings_tab = st.tabs([
    "FarmWeather Dashboard", 
    "Soil Moisture IoT", 
    "Profile & Menu", 
    "Chat Assistant", 
    "Settings"
])

# Soil Moisture IoT Dashboard tab
with soil_tab:
    st.markdown('<p class="subheader">💧 Soil Moisture IoT Dashboard</p>', unsafe_allow_html=True)
    
    # Check if user has location set
    if not st.session_state.location:
        st.warning("Please set your location in the Settings tab first to use the soil moisture dashboard.")
    else:
        # Control panel for simulation
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Real-Time Soil Moisture Monitoring")
        
        # Explanation text
        st.markdown("""
        This dashboard displays real-time data from your soil moisture sensors deployed in the field.
        Monitor soil conditions, receive alerts, and optimize irrigation based on live sensor data.
        """)
        
        # Simulation controls
        sim_col1, sim_col2 = st.columns([3, 1])
        with sim_col1:
            if not st.session_state.soil_moisture_simulation_running:
                if st.button("Start Real-Time Monitoring", type="primary", use_container_width=True):
                    # Start the simulation in a background thread
                    soil_moisture_service.start_simulation(st.session_state.user_id)
                    st.session_state.soil_moisture_simulation_running = True
                    st.session_state.last_soil_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.rerun()
            else:
                if st.button("Stop Monitoring", type="secondary", use_container_width=True):
                    # Stop the simulation
                    soil_moisture_service.stop_simulation()
                    st.session_state.soil_moisture_simulation_running = False
                    st.rerun()
        
        with sim_col2:
            # Refresh button to manually update data
            if st.button("Refresh Data", use_container_width=True):
                st.session_state.last_soil_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
        # Display the last update time
        if st.session_state.last_soil_update:
            st.caption(f"Last updated: {st.session_state.last_soil_update}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Get sensor data
        sensors = db.get_soil_moisture_sensors(st.session_state.user_id)
        
        # If simulation is running, get the latest readings
        if st.session_state.soil_moisture_simulation_running:
            latest_readings = soil_moisture_service.get_latest_readings(max_items=10)
            if latest_readings:
                st.session_state.soil_moisture_readings = latest_readings + st.session_state.soil_moisture_readings
                # Keep only the most recent 100 readings to avoid memory issues
                st.session_state.soil_moisture_readings = st.session_state.soil_moisture_readings[:100]
        
        # Display sensor cards if we have sensors
        if sensors:
            # Summary stats at the top
            st.markdown("### Field Overview")
            
            # Create metrics for average moisture, temperature, etc.
            metric_cols = st.columns(4)
            
            # Calculate average values if we have readings
            avg_moisture = None
            avg_temp = None
            avg_battery = None
            critical_sensors = 0
            
            if st.session_state.soil_moisture_readings:
                # Group readings by sensor
                sensor_readings = {}
                for reading in st.session_state.soil_moisture_readings:
                    sensor_id = reading['sensor_id']
                    if sensor_id not in sensor_readings:
                        sensor_readings[sensor_id] = []
                    sensor_readings[sensor_id].append(reading)
                
                # Get the most recent reading for each sensor
                latest_by_sensor = []
                for sensor_id, readings in sensor_readings.items():
                    if readings:
                        # Sort by recorded_at in descending order
                        sorted_readings = sorted(readings, key=lambda r: r['recorded_at'], reverse=True)
                        latest_by_sensor.append(sorted_readings[0])
                
                # Calculate averages from the latest readings
                if latest_by_sensor:
                    avg_moisture = sum(r['moisture_percentage'] for r in latest_by_sensor) / len(latest_by_sensor)
                    
                    # Some readings might not have temperature data
                    temps = [r['temperature'] for r in latest_by_sensor if r['temperature'] is not None]
                    if temps:
                        avg_temp = sum(temps) / len(temps)
                    
                    # Count sensors with critical moisture levels
                    for reading in latest_by_sensor:
                        status = soil_moisture_service.get_moisture_status(reading['moisture_percentage'])
                        if status['condition'] == 'danger':
                            critical_sensors += 1
                    
                    # Calculate average battery level
                    batteries = [r['battery_level'] for r in latest_by_sensor if r['battery_level'] is not None]
                    if batteries:
                        avg_battery = sum(batteries) / len(batteries)
            
            # Display metrics
            with metric_cols[0]:
                if avg_moisture is not None:
                    st.metric("Avg. Soil Moisture", f"{avg_moisture:.1f}%")
                else:
                    st.metric("Avg. Soil Moisture", "N/A")
            
            with metric_cols[1]:
                if avg_temp is not None:
                    st.metric("Avg. Soil Temperature", f"{avg_temp:.1f}°C")
                else:
                    st.metric("Avg. Soil Temperature", "N/A")
            
            with metric_cols[2]:
                st.metric("Sensors Needing Attention", f"{critical_sensors}")
            
            with metric_cols[3]:
                if avg_battery is not None:
                    st.metric("Avg. Battery Level", f"{avg_battery:.1f}%")
                else:
                    st.metric("Avg. Battery Level", "N/A")
            
            # Individual sensor cards
            st.markdown("### Soil Moisture Sensors")
            
            # Create a grid of sensor cards
            sensor_rows = [sensors[i:i + 2] for i in range(0, len(sensors), 2)]
            
            for row in sensor_rows:
                cols = st.columns(2)
                for i, sensor in enumerate(row):
                    with cols[i]:
                        # Find the latest reading for this sensor
                        latest_reading = None
                        if st.session_state.soil_moisture_readings:
                            # Filter readings for this sensor and sort by time
                            sensor_readings = [r for r in st.session_state.soil_moisture_readings 
                                            if r['sensor_id'] == sensor['id']]
                            if sensor_readings:
                                # Get the most recent reading
                                sensor_readings.sort(key=lambda r: r['recorded_at'], reverse=True)
                                latest_reading = sensor_readings[0]
                        
                        # Display the sensor card
                        st.markdown(f'<div class="card">', unsafe_allow_html=True)
                        
                        # Sensor header with name and location
                        st.markdown(f"#### {sensor['name']}")
                        st.caption(f"Location: {sensor['location_name']} | Field: {sensor['field_area'] or 'Unknown'}")
                        st.caption(f"Depth: {sensor['depth'] or 'Unknown'} cm | Type: {sensor['sensor_type'] or 'Standard'}")
                        
                        # Display data from latest reading if available
                        if latest_reading:
                            # Format timestamp
                            if isinstance(latest_reading['recorded_at'], str):
                                timestamp_str = latest_reading['recorded_at']
                            else:
                                timestamp_str = latest_reading['recorded_at'].strftime("%Y-%m-%d %H:%M:%S")
                            
                            st.caption(f"Last updated: {timestamp_str}")
                            
                            # Check soil moisture status
                            moisture = latest_reading['moisture_percentage']
                            status = soil_moisture_service.get_moisture_status(moisture)
                            
                            # Display the moisture value with appropriate styling
                            if status['condition'] == 'danger':
                                st.markdown(f'<div class="danger-box">', unsafe_allow_html=True)
                            elif status['condition'] == 'warning':
                                st.markdown(f'<div class="warning-box">', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="success-box">', unsafe_allow_html=True)
                            
                            st.markdown(f"**Moisture:** {moisture:.1f}% - **{status['status']}**")
                            st.markdown(f"*{status['recommendation']}*")
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Display additional sensor data
                            data_cols = st.columns(3)
                            with data_cols[0]:
                                if latest_reading['temperature'] is not None:
                                    st.metric("Soil Temp", f"{latest_reading['temperature']:.1f}°C")
                                else:
                                    st.metric("Soil Temp", "N/A")
                            
                            with data_cols[1]:
                                if latest_reading['electrical_conductivity'] is not None:
                                    st.metric("EC", f"{latest_reading['electrical_conductivity']:.0f} µS/cm")
                                else:
                                    st.metric("EC", "N/A")
                            
                            with data_cols[2]:
                                if latest_reading['battery_level'] is not None:
                                    st.metric("Battery", f"{latest_reading['battery_level']:.0f}%")
                                else:
                                    st.metric("Battery", "N/A")
                        else:
                            st.info("No readings available for this sensor yet. Start monitoring to collect data.")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
            
            # Historical data visualization
            st.markdown("### Historical Moisture Trends")
            
            # Only show historical data if we have readings
            if st.session_state.soil_moisture_readings:
                # Prepare data for plotting
                plot_data = pd.DataFrame(st.session_state.soil_moisture_readings)
                
                # Convert recorded_at to datetime if it's a string
                if 'recorded_at' in plot_data.columns and plot_data['recorded_at'].dtype == 'object':
                    plot_data['recorded_at'] = pd.to_datetime(plot_data['recorded_at'])
                
                # Sort by time
                plot_data = plot_data.sort_values('recorded_at')
                
                # Get sensors for filtering
                sensor_names = {sensor['id']: sensor['name'] for sensor in sensors}
                plot_data['sensor_name'] = plot_data['sensor_id'].map(sensor_names)
                
                # Add a selector for which sensors to display
                selected_sensors = st.multiselect(
                    "Select sensors to display",
                    options=list(sensor_names.values()),
                    default=list(sensor_names.values())[:min(3, len(sensor_names))]
                )
                
                # Filter data for selected sensors
                if selected_sensors:
                    plot_filtered = plot_data[plot_data['sensor_name'].isin(selected_sensors)]
                    
                    # Create the time series plot
                    if not plot_filtered.empty and 'recorded_at' in plot_filtered.columns:
                        fig = px.line(
                            plot_filtered,
                            x='recorded_at',
                            y='moisture_percentage',
                            color='sensor_name',
                            labels={
                                'recorded_at': 'Time',
                                'moisture_percentage': 'Soil Moisture (%)',
                                'sensor_name': 'Sensor'
                            },
                            title='Soil Moisture Trends Over Time'
                        )
                        
                        # Add horizontal lines for critical thresholds
                        fig.add_shape(
                            type="line",
                            x0=plot_filtered['recorded_at'].min(),
                            x1=plot_filtered['recorded_at'].max(),
                            y0=20,
                            y1=20,
                            line=dict(color="red", width=2, dash="dash"),
                            name="Critical Dry"
                        )
                        
                        fig.add_shape(
                            type="line",
                            x0=plot_filtered['recorded_at'].min(),
                            x1=plot_filtered['recorded_at'].max(),
                            y0=80,
                            y1=80,
                            line=dict(color="red", width=2, dash="dash"),
                            name="Over-Saturated"
                        )
                        
                        # Update layout
                        fig.update_layout(
                            height=500,
                            xaxis_title="Time",
                            yaxis_title="Soil Moisture (%)",
                            legend_title="Sensor",
                            hovermode="x unified"
                        )
                        
                        # Display the plot
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Create a temperature plot if we have temperature data
                        temp_data = plot_filtered[plot_filtered['temperature'].notna()]
                        if not temp_data.empty:
                            temp_fig = px.line(
                                temp_data,
                                x='recorded_at',
                                y='temperature',
                                color='sensor_name',
                                labels={
                                    'recorded_at': 'Time',
                                    'temperature': 'Soil Temperature (°C)',
                                    'sensor_name': 'Sensor'
                                },
                                title='Soil Temperature Trends'
                            )
                            
                            # Update layout
                            temp_fig.update_layout(
                                height=400,
                                xaxis_title="Time",
                                yaxis_title="Temperature (°C)",
                                legend_title="Sensor",
                                hovermode="x unified"
                            )
                            
                            # Display the plot
                            st.plotly_chart(temp_fig, use_container_width=True)
                    else:
                        st.info("Not enough data to generate plots. Continue monitoring to collect more data.")
                else:
                    st.warning("Please select at least one sensor to display data.")
            else:
                st.info("No historical data available yet. Start the real-time monitoring to collect data.")
        else:
            # No sensors available
            st.info("No soil moisture sensors registered yet. Start real-time monitoring to automatically register sensors based on your saved locations.")
            
            # Explain what soil moisture sensors do
            st.markdown("### What are Soil Moisture Sensors?")
            st.markdown("""
            Soil moisture sensors are IoT devices that measure the water content in soil. They help farmers:
            
            - Optimize irrigation schedules and reduce water usage
            - Prevent over-watering and under-watering of crops
            - Monitor field conditions remotely without physical inspection
            - Detect irrigation system failures or leaks
            - Improve crop yield and quality through precise water management
            
            This dashboard simulates real-time IoT sensor data to demonstrate how you can monitor soil conditions 
            across your fields using FarmWeather AI Advisor.
            """)
        
        # Sensor management section
        st.markdown("### Sensor Management")
        
        # Allow manual registration of sensors
        with st.expander("Register a New Soil Moisture Sensor"):
            # Form to register a new sensor
            with st.form("sensor_registration_form"):
                sensor_name = st.text_input("Sensor Name", placeholder="e.g., North Field Sensor 1")
                sensor_id = st.text_input("Sensor ID/Serial Number", placeholder="e.g., SM12345")
                
                # Get locations for dropdown
                locations = db.get_saved_locations(st.session_state.user_id)
                location_options = [f"{loc['name']} ({loc['latitude']:.4f}, {loc['longitude']:.4f})" for loc in locations]
                
                selected_location = st.selectbox("Sensor Location", options=["Select a location"] + location_options)
                
                field_area = st.text_input("Field/Area", placeholder="e.g., North Field")
                
                sensor_type = st.selectbox(
                    "Sensor Type", 
                    options=["Capacitive", "Resistive", "Time Domain Reflectometry (TDR)", "Other"]
                )
                
                depth = st.number_input("Installation Depth (cm)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
                
                # Submit button
                submit_button = st.form_submit_button("Register Sensor")
                
                if submit_button:
                    if sensor_name and sensor_id and selected_location != "Select a location":
                        # Get the selected location data
                        location_idx = location_options.index(selected_location) if selected_location in location_options else -1
                        
                        if location_idx >= 0:
                            location = locations[location_idx]
                            
                            # Register the sensor
                            result = db.register_soil_moisture_sensor(
                                user_id=st.session_state.user_id,
                                name=sensor_name,
                                sensor_id=sensor_id,
                                location_name=location['name'],
                                latitude=location['latitude'],
                                longitude=location['longitude'],
                                field_area=field_area,
                                depth=depth,
                                sensor_type=sensor_type if sensor_type != "Other" else None
                            )
                            
                            if result:
                                st.success(f"Sensor '{sensor_name}' registered successfully!")
                                # Refresh the page to show the new sensor
                                st.rerun()
                            else:
                                st.error("Failed to register sensor. This sensor ID may already be in use.")
                        else:
                            st.error("Invalid location selected.")
                    else:
                        st.error("Please fill in all required fields (Sensor Name, Sensor ID, and Location).")

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
        # Use session_state to store current user info if not already there
        if 'user_name' not in st.session_state:
            user_data = db.get_or_create_user()
            st.session_state.user_name = user_data.get('name', 'Farmer')
        
        # Let user update their name
        user_name = st.text_input("Your Name", value=st.session_state.user_name)
        
        # Language selection
        selected_language = st.selectbox("Language / 语言 / भाषा / ภาษา / 言語 / 언어", 
                                      ["English", "中文 (Chinese)", "हिंदी (Hindi)", 
                                       "ไทย (Thai)", "日本語 (Japanese)", "한국어 (Korean)", 
                                       "Tiếng Việt (Vietnamese)", "Bahasa Indonesia", 
                                       "Bahasa Malaysia", "မြန်မာ (Myanmar)", "नेपाली (Nepali)", 
                                       "ভাষা (Bengali)", "ភាសាខ្មែរ (Khmer)", "Монгол (Mongolian)"],
                                      index=0 if st.session_state.language == "English" else 
                                           (1 if st.session_state.language == "中文" else 
                                           (2 if st.session_state.language == "हिंदी" else 
                                           (3 if st.session_state.language == "ไทย" else 
                                           (4 if st.session_state.language == "日本語" else 
                                           (5 if st.session_state.language == "한국어" else 
                                           (6 if st.session_state.language == "Tiếng Việt" else 
                                           (7 if st.session_state.language == "Bahasa Indonesia" else 
                                           (8 if st.session_state.language == "Bahasa Malaysia" else 
                                           (9 if st.session_state.language == "မြန်မာ" else 
                                           (10 if st.session_state.language == "नेपाली" else 
                                           (11 if st.session_state.language == "ভাষা" else 
                                           (12 if st.session_state.language == "ភាសាខ្មែរ" else 
                                           (13 if st.session_state.language == "Монгол" else 0))))))))))))))
        
        if st.button("Update Profile"):
            # Update user profile (we create a new user here, but in a real app, we'd update)
            updated_user = db.get_or_create_user(name=user_name)
            st.session_state.user_name = user_name
            
            # Update language preference
            language_map = {
                "English": "English",
                "中文 (Chinese)": "中文",
                "हिंदी (Hindi)": "हिंदी",
                "ไทย (Thai)": "ไทย",
                "日本語 (Japanese)": "日本語",
                "한국어 (Korean)": "한국어",
                "Tiếng Việt (Vietnamese)": "Tiếng Việt",
                "Bahasa Indonesia": "Bahasa Indonesia",
                "Bahasa Malaysia": "Bahasa Malaysia",
                "မြန်မာ (Myanmar)": "မြန်မာ",
                "नेपाली (Nepali)": "नेपाली",
                "ভাষা (Bengali)": "ভাষা",
                "ភាសាខ្មែរ (Khmer)": "ភាសាខ្មែរ",
                "Монгол (Mongolian)": "Монгол"
            }
            
            language_code = language_map.get(selected_language, "English")
            st.session_state.language = language_code
            
            st.success("Profile updated successfully!")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Quick navigation menu
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Quick Navigation")
    
    menu_cols = st.columns(3)
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
        if st.button("💧 Soil Moisture IoT", use_container_width=True):
            st.session_state.active_tab = "soil_tab"
            st.rerun()
            
        if st.button("💬 Chat Assistant", use_container_width=True):
            st.session_state.active_tab = "chat_tab"
            st.rerun()
    
    with menu_cols[2]:
        if st.button("👨‍🌾 My Profile", use_container_width=True):
            st.session_state.active_tab = "profile_tab"
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
        country = st.selectbox("Select Country", ["United States", "India", "China", 
                                       "Thailand", "Japan", "South Korea", "Vietnam", 
                                       "Indonesia", "Malaysia", "Myanmar", "Nepal", 
                                       "Bhutan", "Bangladesh", "Cambodia", "Taiwan", 
                                       "Mongolia", "Kazakhstan", "Kyrgyzstan", "Uzbekistan", 
                                       "Singapore", "Hong Kong", "Laos", "Other"])
        
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
        
        elif country == "China":
            region = st.selectbox("Select Province/Region", 
                              ["Beijing (北京)", "Shanghai (上海)", "Tianjin (天津)", "Chongqing (重庆)",
                               "Anhui (安徽省)", "Fujian (福建省)", "Gansu (甘肃省)", "Guangdong (广东省)",
                               "Guangxi (广西壮族自治区)", "Guizhou (贵州省)", "Hainan (海南省)", 
                               "Hebei (河北省)", "Heilongjiang (黑龙江省)", "Henan (河南省)",
                               "Hubei (湖北省)", "Hunan (湖南省)", "Inner Mongolia (内蒙古自治区)",
                               "Jiangsu (江苏省)", "Jiangxi (江西省)", "Jilin (吉林省)",
                               "Liaoning (辽宁省)", "Ningxia (宁夏回族自治区)", "Qinghai (青海省)",
                               "Shaanxi (陕西省)", "Shandong (山东省)", "Shanxi (山西省)",
                               "Sichuan (四川省)", "Tibet (西藏自治区)", "Xinjiang (新疆维吾尔自治区)",
                               "Yunnan (云南省)", "Zhejiang (浙江省)",
                               "Hong Kong (香港)", "Macau (澳门)", "Taiwan (台湾)"])
            subregion = st.text_input("Enter City/Prefecture (城市/地区) (optional)")
            
        elif country == "Thailand":
            region = st.selectbox("Select Province", 
                              ["Bangkok (กรุงเทพมหานคร)", "Chiang Mai (เชียงใหม่)", "Chiang Rai (เชียงราย)", 
                               "Phuket (ภูเก็ต)", "Krabi (กระบี่)", "Ayutthaya (พระนครศรีอยุธยา)", 
                               "Pattaya (พัทยา)", "Hua Hin (หัวหิน)", "Koh Samui (เกาะสมุย)", 
                               "Chonburi (ชลบุรี)", "Songkhla (สงขลา)", "Hat Yai (หาดใหญ่)", 
                               "Sukhothai (สุโขทัย)", "Khon Kaen (ขอนแก่น)", "Udon Thani (อุดรธานี)", 
                               "Nakhon Ratchasima (นครราชสีมา)", "Nonthaburi (นนทบุรี)", 
                               "Samut Prakan (สมุทรปราการ)", "Lopburi (ลพบุรี)", "Kanchanaburi (กาญจนบุรี)"])
            subregion = st.text_input("Enter District/City (อำเภอ/เมือง) (optional)")
            
        elif country == "Japan":
            region = st.selectbox("Select Prefecture", 
                              ["Tokyo (東京)", "Osaka (大阪)", "Kyoto (京都)", "Hokkaido (北海道)", 
                               "Fukuoka (福岡)", "Okinawa (沖縄)", "Aichi (愛知)", "Hiroshima (広島)", 
                               "Kanagawa (神奈川)", "Hyogo (兵庫)", "Shizuoka (静岡)", "Chiba (千葉)", 
                               "Saitama (埼玉)", "Miyagi (宮城)", "Nagano (長野)", "Kumamoto (熊本)", 
                               "Kagoshima (鹿児島)", "Niigata (新潟)", "Nara (奈良)", "Yamaguchi (山口)"])
            subregion = st.text_input("Enter City (市区町村) (optional)")
            
        elif country == "South Korea":
            region = st.selectbox("Select Province/Metropolitan City", 
                              ["Seoul (서울)", "Busan (부산)", "Incheon (인천)", "Daegu (대구)", 
                               "Daejeon (대전)", "Gwangju (광주)", "Ulsan (울산)", "Sejong (세종)", 
                               "Gyeonggi (경기도)", "Gangwon (강원도)", "Chungbuk (충청북도)", 
                               "Chungnam (충청남도)", "Jeonbuk (전라북도)", "Jeonnam (전라남도)", 
                               "Gyeongbuk (경상북도)", "Gyeongnam (경상남도)", "Jeju (제주도)"])
            subregion = st.text_input("Enter City/District (시/구) (optional)")
            
        elif country == "Vietnam":
            region = st.selectbox("Select Province/City", 
                              ["Hanoi (Hà Nội)", "Ho Chi Minh City (Thành phố Hồ Chí Minh)", 
                               "Da Nang (Đà Nẵng)", "Hai Phong (Hải Phòng)", "Can Tho (Cần Thơ)", 
                               "Quang Ninh (Quảng Ninh)", "Khanh Hoa (Khánh Hòa)", "Lao Cai (Lào Cai)", 
                               "Thua Thien Hue (Thừa Thiên Huế)", "Quang Nam (Quảng Nam)", 
                               "Binh Duong (Bình Dương)", "Dong Nai (Đồng Nai)", "Ba Ria-Vung Tau (Bà Rịa-Vũng Tàu)"])
            subregion = st.text_input("Enter District (Quận/Huyện) (optional)")
            
        elif country in ["Indonesia", "Malaysia", "Myanmar", "Nepal", "Bhutan", "Bangladesh", 
                         "Cambodia", "Taiwan", "Mongolia", "Kazakhstan", "Kyrgyzstan", 
                         "Uzbekistan", "Singapore", "Hong Kong", "Laos"]:
            region = st.text_input(f"Enter Province/Region in {country}")
            subregion = st.text_input("Enter City/District (optional)")
        
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