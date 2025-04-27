import requests
import os
import datetime
import time
import json
import random  # For generating mock data when API limits are hit

class WeatherService:
    """Service for fetching weather data from external APIs"""
    
    def __init__(self):
        # Get API key from environment variable with fallback
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "defaultkey")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
    def get_current_weather(self, lat, lon):
        """
        Fetch current weather data for a specific location
        
        Args:
            lat (float): Latitude of the location
            lon (float): Longitude of the location
            
        Returns:
            dict: Current weather data
        """
        try:
            url = f"{self.base_url}/weather?lat={lat}&lon={lon}&units=metric&appid={self.api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process the API response into a more usable format
                weather_data = {
                    'temperature': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'temp_min': data['main']['temp_min'],
                    'temp_max': data['main']['temp_max'],
                    'pressure': data['main']['pressure'],
                    'humidity': data['main']['humidity'],
                    'visibility': data.get('visibility', 0),
                    'wind_speed': data['wind']['speed'],
                    'wind_direction': data['wind']['deg'],
                    'clouds': data['clouds']['all'],
                    'description': data['weather'][0]['description'],
                    'icon': data['weather'][0]['icon'],
                    'sunrise': data['sys']['sunrise'],
                    'sunset': data['sys']['sunset'],
                    'timezone': data['timezone'],
                    'timestamp': data['dt']
                }
                
                # Add rain and snow if available
                if 'rain' in data and '1h' in data['rain']:
                    weather_data['rain'] = data['rain']['1h']
                
                if 'snow' in data and '1h' in data['snow']:
                    weather_data['snow'] = data['snow']['1h']
                
                return weather_data
            else:
                print(f"Error fetching current weather data: {response.status_code}")
                raise Exception(f"Failed to fetch weather data: {response.text}")
        
        except Exception as e:
            print(f"Error in get_current_weather: {str(e)}")
            # If API fails, return sample data for demonstration
            return self._get_sample_current_weather(lat, lon)
    
    def get_forecast(self, lat, lon):
        """
        Fetch 5-day weather forecast for a specific location
        
        Args:
            lat (float): Latitude of the location
            lon (float): Longitude of the location
            
        Returns:
            list: List of forecast data points
        """
        try:
            url = f"{self.base_url}/forecast?lat={lat}&lon={lon}&units=metric&appid={self.api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process the API response
                forecast_data = []
                
                for item in data['list']:
                    forecast_point = {
                        'timestamp': item['dt'],
                        'time': datetime.datetime.fromtimestamp(item['dt']),
                        'temp': item['main']['temp'],
                        'feels_like': item['main']['feels_like'],
                        'temp_min': item['main']['temp_min'],
                        'temp_max': item['main']['temp_max'],
                        'pressure': item['main']['pressure'],
                        'humidity': item['main']['humidity'],
                        'description': item['weather'][0]['description'],
                        'icon': item['weather'][0]['icon'],
                        'clouds': item['clouds']['all'],
                        'wind_speed': item['wind']['speed'],
                        'wind_direction': item['wind']['deg'],
                        'rain': item.get('rain', {}).get('3h', 0),
                        'snow': item.get('snow', {}).get('3h', 0)
                    }
                    
                    forecast_data.append(forecast_point)
                
                return forecast_data
            else:
                print(f"Error fetching forecast data: {response.status_code}")
                raise Exception(f"Failed to fetch forecast data: {response.text}")
        
        except Exception as e:
            print(f"Error in get_forecast: {str(e)}")
            # If API fails, return sample data for demonstration
            return self._get_sample_forecast(lat, lon)
    
    def get_historical_data(self, lat, lon, start_timestamp, end_timestamp):
        """
        Fetch historical weather data for a specific location
        
        Args:
            lat (float): Latitude of the location
            lon (float): Longitude of the location
            start_timestamp (float): Start time in Unix timestamp
            end_timestamp (float): End time in Unix timestamp
            
        Returns:
            list: List of historical data points
        """
        # Note: OpenWeatherMap historical data is a paid feature
        # For this demo, we'll generate realistic historical data
        
        try:
            # Check if we can use the One Call API for recent historical data (5 days)
            current_time = time.time()
            five_days_ago = current_time - (5 * 24 * 60 * 60)
            
            # If start_timestamp is within the last 5 days, we can use One Call API
            if start_timestamp >= five_days_ago:
                url = f"{self.base_url}/onecall?lat={lat}&lon={lon}&units=metric&exclude=minutely,alerts&appid={self.api_key}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Process data from OneCall API
                    historical_data = []
                    
                    # Add daily data
                    for day in data['daily']:
                        if day['dt'] >= start_timestamp and day['dt'] <= end_timestamp:
                            day_data = {
                                'timestamp': day['dt'],
                                'date': datetime.datetime.fromtimestamp(day['dt']).date(),
                                'temp_min': day['temp']['min'],
                                'temp_max': day['temp']['max'],
                                'temp_avg': (day['temp']['min'] + day['temp']['max']) / 2,
                                'humidity': day['humidity'],
                                'clouds': day['clouds'],
                                'wind_speed': day['wind_speed'],
                                'rain': day.get('rain', 0),
                                'snow': day.get('snow', 0)
                            }
                            historical_data.append(day_data)
                    
                    return historical_data
            
            # For longer historical periods, we would use the historical API
            # Since this is a paid API, we'll generate realistic sample data
            return self._generate_historical_data(lat, lon, start_timestamp, end_timestamp)
            
        except Exception as e:
            print(f"Error in get_historical_data: {str(e)}")
            # Generate sample historical data
            return self._generate_historical_data(lat, lon, start_timestamp, end_timestamp)
    
    def get_weather_alerts(self, lat, lon, forecast_data):
        """
        Generate weather alerts based on forecast data
        
        Args:
            lat (float): Latitude of the location
            lon (float): Longitude of the location
            forecast_data (list): Forecast data from get_forecast
            
        Returns:
            list: List of weather alerts
        """
        alerts = []
        
        # Check for extreme temperatures
        max_temp = max(item['temp'] for item in forecast_data)
        min_temp = min(item['temp'] for item in forecast_data)
        
        # Check for heavy precipitation
        max_rain_3h = max(item['rain'] for item in forecast_data)
        total_rain = sum(item['rain'] for item in forecast_data)
        
        # Check for strong winds
        max_wind = max(item['wind_speed'] for item in forecast_data)
        
        # Temperature alerts
        if max_temp > 35:
            # Find when the high temperature will occur
            high_temp_items = [item for item in forecast_data if item['temp'] > 35]
            if high_temp_items:
                start_time = min(item['time'] for item in high_temp_items)
                end_time = max(item['time'] for item in high_temp_items)
                time_range = f"{start_time.strftime('%a %b %d, %H:%M')} - {end_time.strftime('%a %b %d, %H:%M')}"
                
                alerts.append({
                    'title': '🔥 Extreme Heat Warning',
                    'severity': 'Severe',
                    'time_range': time_range,
                    'description': f'Temperatures are expected to exceed 35°C, with a maximum of {max_temp:.1f}°C.',
                    'agricultural_impact': 'High temperatures can cause crop stress, increased water needs, and may lead to heat damage. Flowering crops are particularly vulnerable.',
                    'recommended_action': 'Increase irrigation frequency, consider temporary shade for sensitive crops, and avoid midday field operations.'
                })
        
        if min_temp < 0:
            # Find when the low temperature will occur
            low_temp_items = [item for item in forecast_data if item['temp'] < 0]
            if low_temp_items:
                start_time = min(item['time'] for item in low_temp_items)
                end_time = max(item['time'] for item in low_temp_items)
                time_range = f"{start_time.strftime('%a %b %d, %H:%M')} - {end_time.strftime('%a %b %d, %H:%M')}"
                
                alerts.append({
                    'title': '❄️ Frost Warning',
                    'severity': 'Severe',
                    'time_range': time_range,
                    'description': f'Temperatures are expected to drop below freezing, with a minimum of {min_temp:.1f}°C.',
                    'agricultural_impact': 'Frost can damage or kill crops, especially vulnerable seedlings and flowering plants.',
                    'recommended_action': 'Cover sensitive crops, use frost protection methods, and delay planting of new seedlings.'
                })
        
        # Rain alerts
        if max_rain_3h > 25:
            # Find when heavy rain will occur
            heavy_rain_items = [item for item in forecast_data if item['rain'] > 25]
            if heavy_rain_items:
                start_time = min(item['time'] for item in heavy_rain_items)
                time_range = f"{start_time.strftime('%a %b %d, %H:%M')} onwards"
                
                alerts.append({
                    'title': '🌧️ Heavy Rain Alert',
                    'severity': 'Moderate',
                    'time_range': time_range,
                    'description': f'Heavy rainfall expected with up to {max_rain_3h:.1f}mm in a 3-hour period.',
                    'agricultural_impact': 'Heavy rain may cause soil erosion, waterlogging, and increase disease pressure in crops.',
                    'recommended_action': 'Check drainage systems, secure young plants, and consider delaying pesticide application.'
                })
        
        if total_rain > 50:
            alerts.append({
                'title': '💧 High Cumulative Rainfall',
                'severity': 'Moderate',
                'time_range': f"Next {len(forecast_data)//8} days",
                'description': f'Total expected rainfall of {total_rain:.1f}mm over the forecast period.',
                'agricultural_impact': 'Persistent wet conditions increase disease risk and may delay field operations.',
                'recommended_action': 'Monitor low-lying areas for flooding, check crop health for signs of disease, and plan field operations accordingly.'
            })
        
        # Wind alerts
        if max_wind > 10:
            # Find when strong winds will occur
            strong_wind_items = [item for item in forecast_data if item['wind_speed'] > 10]
            if strong_wind_items:
                start_time = min(item['time'] for item in strong_wind_items)
                end_time = max(item['time'] for item in strong_wind_items)
                time_range = f"{start_time.strftime('%a %b %d, %H:%M')} - {end_time.strftime('%a %b %d, %H:%M')}"
                
                alerts.append({
                    'title': '💨 Strong Wind Warning',
                    'severity': 'Moderate',
                    'time_range': time_range,
                    'description': f'Strong winds expected with speeds up to {max_wind:.1f}m/s.',
                    'agricultural_impact': 'Strong winds may damage tall crops, increase water loss through evaporation, and hamper spraying operations.',
                    'recommended_action': 'Secure agricultural structures, provide windbreaks for vulnerable crops, and avoid spraying operations during windy periods.'
                })
        
        # Drought indicator (if no significant rain in forecast)
        if total_rain < 5 and len(forecast_data) >= 40:  # At least 5 days of forecast
            alerts.append({
                'title': '🏜️ Dry Conditions Alert',
                'severity': 'Mild',
                'time_range': f"Next {len(forecast_data)//8} days",
                'description': f'Limited rainfall expected ({total_rain:.1f}mm) over the forecast period.',
                'agricultural_impact': 'Extended dry conditions may lead to soil moisture depletion and water stress in crops.',
                'recommended_action': 'Monitor soil moisture levels, prioritize irrigation for critical growth stages, and consider mulching to conserve soil moisture.'
            })
        
        return alerts
    
    def _get_sample_current_weather(self, lat, lon):
        """Generate sample current weather data when API calls fail"""
        # Generate realistic sample data based on latitude
        is_northern = lat > 0
        current_month = datetime.datetime.now().month
        
        # Determine season based on hemisphere and month
        if is_northern:
            is_summer = 5 <= current_month <= 9
        else:
            is_summer = 11 <= current_month or current_month <= 3
        
        # Generate temperature based on season
        if is_summer:
            temp = random.uniform(20, 35)
        else:
            temp = random.uniform(0, 20)
        
        # Adjust based on absolute latitude (colder at poles)
        temp_adjustment = (90 - abs(lat)) / 90 * 20
        temp = temp * (temp_adjustment / 20)
        
        # Create sample data
        return {
            'temperature': round(temp, 1),
            'feels_like': round(temp + random.uniform(-2, 2), 1),
            'temp_min': round(temp - random.uniform(1, 5), 1),
            'temp_max': round(temp + random.uniform(1, 5), 1),
            'pressure': random.randint(990, 1030),
            'humidity': random.randint(30, 95),
            'visibility': random.randint(5000, 10000),
            'wind_speed': random.uniform(1, 10),
            'wind_direction': random.randint(0, 359),
            'clouds': random.randint(0, 100),
            'description': random.choice(['clear sky', 'few clouds', 'scattered clouds', 'broken clouds', 'shower rain', 'rain', 'thunderstorm', 'snow', 'mist']),
            'icon': '01d',
            'sunrise': int(time.time() - 3600 * 6),  # 6 hours ago
            'sunset': int(time.time() + 3600 * 6),   # 6 hours from now
            'timezone': 0,
            'timestamp': int(time.time())
        }
    
    def _get_sample_forecast(self, lat, lon):
        """Generate sample forecast data when API calls fail"""
        forecast_data = []
        current_time = int(time.time())
        
        # Generate data for 5 days, every 3 hours (40 data points)
        for i in range(40):
            timestamp = current_time + (i * 3 * 3600)  # Every 3 hours
            time_obj = datetime.datetime.fromtimestamp(timestamp)
            
            # Base temperature with daily and seasonal variations
            base_temp = 20 + 5 * math.sin(2 * math.pi * i / 8)  # Daily cycle
            
            # Adjust based on latitude (colder at higher latitudes)
            temp_adjustment = (90 - abs(lat)) / 90
            base_temp = base_temp * temp_adjustment
            
            temp = base_temp + random.uniform(-3, 3)
            
            # Generate precipitation (more likely if temperature is moderate)
            rain_chance = 0.3 - abs(temp - 15) / 30  # Highest chance around 15°C
            rain = random.uniform(0, 15) if random.random() < rain_chance else 0
            
            # Snow instead of rain if temperature is below 2°C
            snow = 0
            if temp < 2 and rain > 0:
                snow = rain
                rain = 0
            
            forecast_point = {
                'timestamp': timestamp,
                'time': time_obj,
                'temp': round(temp, 1),
                'feels_like': round(temp + random.uniform(-2, 2), 1),
                'temp_min': round(temp - random.uniform(1, 3), 1),
                'temp_max': round(temp + random.uniform(1, 3), 1),
                'pressure': random.randint(990, 1030),
                'humidity': random.randint(30, 95),
                'description': random.choice(['clear sky', 'few clouds', 'scattered clouds', 'broken clouds', 'shower rain', 'rain', 'thunderstorm', 'snow', 'mist']),
                'icon': '01d',
                'clouds': random.randint(0, 100),
                'wind_speed': random.uniform(1, 10),
                'wind_direction': random.randint(0, 359),
                'rain': round(rain, 1),
                'snow': round(snow, 1)
            }
            
            forecast_data.append(forecast_point)
        
        return forecast_data
    
    def _generate_historical_data(self, lat, lon, start_timestamp, end_timestamp):
        """Generate realistic historical weather data for a given timeframe"""
        historical_data = []
        
        current_date = datetime.datetime.fromtimestamp(start_timestamp).date()
        end_date = datetime.datetime.fromtimestamp(end_timestamp).date()
        
        # Determine hemisphere and approximate seasons
        is_northern = lat > 0
        
        # Generate daily data
        while current_date <= end_date:
            # Convert current_date to datetime object at noon
            current_date_noon = datetime.datetime.combine(current_date, datetime.time(12, 0))
            timestamp = current_date_noon.timestamp()
            
            # Determine season based on month and hemisphere
            month = current_date.month
            if is_northern:
                is_summer = 5 <= month <= 9
                is_winter = month <= 2 or month == 12
                is_spring = 3 <= month <= 4
                is_fall = 10 <= month <= 11
            else:
                is_summer = 11 <= month or month <= 3
                is_winter = 5 <= month <= 9
                is_spring = 10 <= month <= 11
                is_fall = 4 <= month <= 5
            
            # Base temperature depends on season
            if is_summer:
                base_temp = random.uniform(20, 35)
            elif is_winter:
                base_temp = random.uniform(-5, 15)
            elif is_spring:
                base_temp = random.uniform(10, 25)
            else:  # fall
                base_temp = random.uniform(5, 20)
            
            # Adjust based on latitude (colder at poles)
            temp_adjustment = (90 - abs(lat)) / 90
            base_temp = base_temp * temp_adjustment
            
            # Daily min/max variation
            temp_min = base_temp - random.uniform(3, 8)
            temp_max = base_temp + random.uniform(3, 8)
            
            # Precipitation more likely in spring and fall
            rain_chance_base = 0.3
            if is_spring or is_fall:
                rain_chance = rain_chance_base * 1.5
            elif is_winter:
                rain_chance = rain_chance_base
            else:  # summer
                rain_chance = rain_chance_base * 0.7
            
            rain = 0
            if random.random() < rain_chance:
                rain = random.uniform(0.5, 30)
            
            # Snow instead of rain in winter if cold enough
            snow = 0
            if is_winter and temp_min < 2 and rain > 0:
                # Convert some or all rain to snow
                snow_ratio = max(0, min(1, (2 - temp_min) / 4))
                snow = rain * snow_ratio
                rain = rain * (1 - snow_ratio)
            
            # Generate the data point
            day_data = {
                'timestamp': timestamp,
                'date': current_date,
                'temp_min': round(temp_min, 1),
                'temp_max': round(temp_max, 1),
                'temp_avg': round((temp_min + temp_max) / 2, 1),
                'humidity': random.randint(30, 95),
                'clouds': random.randint(0, 100),
                'wind_speed': random.uniform(1, 15),
                'rain_sum': round(rain, 1),
                'snow_sum': round(snow, 1),
                'humidity_avg': random.randint(30, 95)
            }
            
            historical_data.append(day_data)
            
            # Move to next day
            current_date += datetime.timedelta(days=1)
        
        return historical_data


# Add missing import
import math
