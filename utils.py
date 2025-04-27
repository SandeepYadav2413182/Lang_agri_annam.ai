import os
import json
import requests
import datetime
import pickle
import time

def get_state_coordinates(state, county=None):
    """
    Get the latitude and longitude for a U.S. state and optional county
    
    Args:
        state (str): The state name
        county (str, optional): The county name
    
    Returns:
        tuple: (latitude, longitude) coordinates
    """
    try:
        # Build the search query
        if county:
            query = f"{county}, {state}, USA"
        else:
            query = f"{state}, USA"
        
        # Use Nominatim API for geocoding (OpenStreetMap data)
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1
        }
        
        # Add a user agent as required by Nominatim usage policy
        headers = {
            "User-Agent": "FarmWeatherAIAdvisor/1.0"
        }
        
        # Make the request
        response = requests.get(base_url, params=params, headers=headers)
        
        if response.status_code == 200:
            results = response.json()
            if results:
                # Return latitude and longitude as floats
                return float(results[0]["lat"]), float(results[0]["lon"])
        
        # If we get here, something went wrong with the API request
        print(f"Could not find coordinates for {query}")
        return None, None
    
    except Exception as e:
        print(f"Error in get_state_coordinates: {str(e)}")
        return None, None

def cache_data(cache_id, data, expiry_hours=24):
    """
    Cache data to a local file to avoid excessive API calls
    
    Args:
        cache_id (str): Unique identifier for the cached data
        data: The data to cache
        expiry_hours (int): Number of hours the cache is valid
    """
    try:
        # Create cache directory if it doesn't exist
        os.makedirs("cache", exist_ok=True)
        
        # Sanitize the cache_id to create a valid filename
        sanitized_id = "".join(c if c.isalnum() or c in "_-." else "_" for c in cache_id)
        cache_file = os.path.join("cache", f"{sanitized_id}.pickle")
        
        # Create a cache object with the data and expiry time
        cache_obj = {
            "data": data,
            "expiry": datetime.datetime.now() + datetime.timedelta(hours=expiry_hours)
        }
        
        # Write to file
        with open(cache_file, "wb") as f:
            pickle.dump(cache_obj, f)
            
    except Exception as e:
        print(f"Error caching data: {str(e)}")

def load_cached_data(cache_id):
    """
    Load data from cache if it exists and is not expired
    
    Args:
        cache_id (str): Unique identifier for the cached data
    
    Returns:
        The cached data if valid, None otherwise
    """
    try:
        # Sanitize the cache_id to create a valid filename
        sanitized_id = "".join(c if c.isalnum() or c in "_-." else "_" for c in cache_id)
        cache_file = os.path.join("cache", f"{sanitized_id}.pickle")
        
        # Check if cache file exists
        if not os.path.exists(cache_file):
            return None
        
        # Load cache object
        with open(cache_file, "rb") as f:
            cache_obj = pickle.load(f)
        
        # Check if cache is expired
        if datetime.datetime.now() > cache_obj["expiry"]:
            # Cache expired, delete the file
            os.remove(cache_file)
            return None
        
        # Return the cached data
        return cache_obj["data"]
    
    except Exception as e:
        print(f"Error loading cached data: {str(e)}")
        # If there's any error loading the cache, return None
        return None

def fahrenheit_to_celsius(fahrenheit):
    """
    Convert temperature from Fahrenheit to Celsius
    
    Args:
        fahrenheit (float): Temperature in Fahrenheit
    
    Returns:
        float: Temperature in Celsius
    """
    return (fahrenheit - 32) * 5 / 9

def celsius_to_fahrenheit(celsius):
    """
    Convert temperature from Celsius to Fahrenheit
    
    Args:
        celsius (float): Temperature in Celsius
    
    Returns:
        float: Temperature in Fahrenheit
    """
    return (celsius * 9 / 5) + 32

def inches_to_mm(inches):
    """
    Convert precipitation from inches to millimeters
    
    Args:
        inches (float): Precipitation in inches
    
    Returns:
        float: Precipitation in millimeters
    """
    return inches * 25.4

def mm_to_inches(mm):
    """
    Convert precipitation from millimeters to inches
    
    Args:
        mm (float): Precipitation in millimeters
    
    Returns:
        float: Precipitation in inches
    """
    return mm / 25.4

def format_datetime(dt, format_str="%Y-%m-%d %H:%M"):
    """
    Format a datetime object or timestamp to a string
    
    Args:
        dt: Datetime object or unix timestamp
        format_str (str): Format string for output
    
    Returns:
        str: Formatted datetime string
    """
    if isinstance(dt, (int, float)):
        dt = datetime.datetime.fromtimestamp(dt)
    
    return dt.strftime(format_str)

def get_growing_season(lat):
    """
    Determine the typical growing season based on latitude
    
    Args:
        lat (float): Latitude of the location
    
    Returns:
        tuple: (start_month, end_month) representing the growing season
    """
    is_northern = lat > 0
    
    if is_northern:
        # Northern hemisphere
        if abs(lat) < 23.5:  # Tropical
            return (1, 12)  # Year-round growing
        elif abs(lat) < 35:  # Subtropical
            return (3, 11)  # March to November
        elif abs(lat) < 45:  # Temperate
            return (4, 10)  # April to October
        elif abs(lat) < 55:  # Cold temperate
            return (5, 9)  # May to September
        else:  # Subarctic/Arctic
            return (6, 8)  # June to August
    else:
        # Southern hemisphere (reversed seasons)
        if abs(lat) < 23.5:  # Tropical
            return (1, 12)  # Year-round growing
        elif abs(lat) < 35:  # Subtropical
            return (9, 5)  # September to May
        elif abs(lat) < 45:  # Temperate
            return (10, 4)  # October to April
        elif abs(lat) < 55:  # Cold temperate
            return (11, 3)  # November to March
        else:  # Subarctic/Antarctic
            return (12, 2)  # December to February
