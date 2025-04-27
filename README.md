# FarmWeather AI Advisor

An AI-powered weather analysis application for farmers that processes climate data to provide agricultural planning insights and crop yield optimization recommendations.

## Overview

FarmWeather AI Advisor helps farmers make data-driven decisions by analyzing weather patterns and providing tailored agricultural recommendations. The application fetches weather data, processes historical patterns, and uses artificial intelligence to identify trends and provide actionable insights.

## Features

- **Current & Forecast Weather**: Display current conditions and 5-day weather forecasts
- **Historical Weather Analysis**: Analyze climate patterns and trends
- **AI Insights & Recommendations**: Get crop recommendations and agricultural planning advice
- **Weather Alerts & Notifications**: Monitor potential weather risks and get actionable recommendations

## Technical Details

### Dependencies

- Python 3.7+
- Streamlit for web interface
- Pandas for data manipulation
- Plotly for data visualization
- Scikit-learn for machine learning
- NumPy for numerical operations
- Requests for API access

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/farmweather-ai-advisor.git
   cd farmweather-ai-advisor
   ```

2. Install required packages:
   ```
   pip install streamlit pandas plotly scikit-learn numpy requests
   ```

3. Set up API key:
   - Get an API key from OpenWeatherMap (https://openweathermap.org/)
   - Set it as an environment variable:
     ```
     export OPENWEATHER_API_KEY="your_api_key_here"
     ```

### Running the Application

Run the Streamlit application:
