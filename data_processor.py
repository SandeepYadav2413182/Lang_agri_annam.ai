import pandas as pd
import numpy as np
import datetime

class DataProcessor:
    """
    Process weather data for analysis and visualization.
    Converts raw API data into useful formats for analysis.
    """
    
    def process_forecast_data(self, forecast_data):
        """
        Process forecast data into a Pandas DataFrame for analysis
        
        Args:
            forecast_data (list): List of forecast data points from WeatherService
            
        Returns:
            pd.DataFrame: Processed forecast data
        """
        if not forecast_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(forecast_data)
        
        # Ensure all expected columns exist
        if 'rain' not in df.columns:
            df['rain'] = 0
        if 'snow' not in df.columns:
            df['snow'] = 0
        
        # Fill missing values
        df = df.fillna(0)
        
        # Format date columns
        if 'timestamp' in df.columns and 'time' not in df.columns:
            df['time'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Ensure numeric types
        numeric_columns = ['temp', 'feels_like', 'humidity', 'pressure', 
                          'wind_speed', 'clouds', 'rain', 'snow']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    
    def process_historical_data(self, historical_data):
        """
        Process historical weather data into a Pandas DataFrame
        
        Args:
            historical_data (list): List of historical data points from WeatherService
            
        Returns:
            pd.DataFrame: Processed historical data
        """
        if not historical_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        
        # Ensure all expected columns exist
        expected_columns = [
            'temp_min', 'temp_max', 'temp_avg', 
            'humidity', 'clouds', 'wind_speed',
            'rain_sum', 'snow_sum', 'humidity_avg'
        ]
        
        for col in expected_columns:
            if col not in df.columns:
                df[col] = 0
        
        # Fill missing values
        df = df.fillna(0)
        
        # Format date columns
        if 'timestamp' in df.columns and 'date' not in df.columns:
            df['date'] = pd.to_datetime(df['timestamp'], unit='s').dt.date
        
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        # Ensure numeric types
        numeric_columns = ['temp_min', 'temp_max', 'temp_avg', 
                          'humidity', 'clouds', 'wind_speed',
                          'rain_sum', 'snow_sum', 'humidity_avg']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Handle duplicate dates before setting as index
        # If there are duplicate dates, keep the first occurrence
        if df['date'].duplicated().any():
            print("Found duplicate dates in historical data, keeping the first occurrence of each date")
            df = df.drop_duplicates(subset=['date'], keep='first')
            
        # Set date as index for time series analysis
        df = df.set_index('date', drop=False)
        
        return df
    
    def calculate_climate_indicators(self, historical_df):
        """
        Calculate climate indicators for agricultural analysis
        
        Args:
            historical_df (pd.DataFrame): Historical weather data
            
        Returns:
            dict: Dictionary of climate indicators
        """
        if historical_df.empty:
            return {}
        
        # Reset index if date is the index
        if isinstance(historical_df.index, pd.DatetimeIndex):
            df = historical_df.reset_index()
        else:
            df = historical_df.copy()
        
        # Ensure date column is datetime
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        # Extract month and season
        df['month'] = df['date'].dt.month
        
        # Define seasons based on meteorological definition (Northern Hemisphere)
        # Adjust for Southern Hemisphere if needed
        df['season'] = 'Unknown'
        df.loc[df['month'].isin([12, 1, 2]), 'season'] = 'Winter'
        df.loc[df['month'].isin([3, 4, 5]), 'season'] = 'Spring'
        df.loc[df['month'].isin([6, 7, 8]), 'season'] = 'Summer'
        df.loc[df['month'].isin([9, 10, 11]), 'season'] = 'Fall'
        
        # Calculate indicators
        indicators = {}
        
        # Temperature indicators
        indicators['avg_annual_temp'] = df['temp_avg'].mean()
        indicators['temp_range'] = df['temp_max'].max() - df['temp_min'].min()
        
        # Calculate growing degree days (base 10°C)
        df['gdd'] = df.apply(lambda x: max(0, x['temp_avg'] - 10), axis=1)
        indicators['growing_degree_days'] = df['gdd'].sum()
        
        # Precipitation indicators
        indicators['total_annual_rainfall'] = df['rain_sum'].sum()
        indicators['rainy_days'] = (df['rain_sum'] > 0).sum()
        indicators['heavy_rain_days'] = (df['rain_sum'] > 20).sum()
        
        # Frost indicators
        indicators['frost_days'] = (df['temp_min'] < 0).sum()
        
        # Heat stress indicators
        indicators['heat_stress_days'] = (df['temp_max'] > 30).sum()
        
        # Seasonal aggregations
        season_agg = df.groupby('season').agg({
            'temp_avg': 'mean',
            'rain_sum': 'sum',
            'humidity_avg': 'mean',
            'wind_speed': 'mean'
        })
        
        for season in season_agg.index:
            indicators[f'{season.lower()}_avg_temp'] = season_agg.loc[season, 'temp_avg']
            indicators[f'{season.lower()}_total_rain'] = season_agg.loc[season, 'rain_sum']
        
        # Drought indicators
        df['dry_spell'] = (df['rain_sum'] < 1).astype(int)
        df['dry_spell_group'] = (df['dry_spell'].diff() != 0).cumsum()
        dry_spells = df[df['dry_spell'] == 1].groupby('dry_spell_group').size()
        
        indicators['max_dry_spell'] = dry_spells.max() if not dry_spells.empty else 0
        indicators['dry_spells_5d_plus'] = (dry_spells >= 5).sum() if not dry_spells.empty else 0
        
        return indicators
    
    def identify_extreme_events(self, historical_df):
        """
        Identify extreme weather events in historical data
        
        Args:
            historical_df (pd.DataFrame): Historical weather data
            
        Returns:
            list: List of extreme weather events
        """
        if historical_df.empty:
            return []
        
        events = []
        
        # Define thresholds for extreme events
        extreme_rain_threshold = 30  # mm per day
        extreme_heat_threshold = 35  # °C
        extreme_cold_threshold = -5  # °C
        drought_threshold = 15  # days without significant rain
        
        # Heat waves (3+ consecutive days with temp > threshold)
        heat_days = historical_df[historical_df['temp_max'] > extreme_heat_threshold]
        if not heat_days.empty:
            # Group consecutive days
            heat_days['date_diff'] = heat_days['date'].diff().dt.days
            heat_days['group'] = (heat_days['date_diff'] > 1).cumsum()
            heat_waves = heat_days.groupby('group').filter(lambda x: len(x) >= 3)
            
            if not heat_waves.empty:
                for group, wave in heat_waves.groupby('group'):
                    start_date = wave['date'].min()
                    end_date = wave['date'].max()
                    max_temp = wave['temp_max'].max()
                    days = len(wave)
                    
                    events.append({
                        'type': 'Heat Wave',
                        'start_date': start_date,
                        'end_date': end_date,
                        'duration': days,
                        'max_value': max_temp,
                        'description': f"Heat wave with temperatures up to {max_temp:.1f}°C for {days} days"
                    })
        
        # Extreme rainfall events
        extreme_rain = historical_df[historical_df['rain_sum'] > extreme_rain_threshold]
        for _, row in extreme_rain.iterrows():
            events.append({
                'type': 'Heavy Rainfall',
                'start_date': row['date'],
                'end_date': row['date'],
                'duration': 1,
                'max_value': row['rain_sum'],
                'description': f"Heavy rainfall of {row['rain_sum']:.1f}mm"
            })
        
        # Cold snaps
        cold_days = historical_df[historical_df['temp_min'] < extreme_cold_threshold]
        if not cold_days.empty:
            # Group consecutive days
            cold_days['date_diff'] = cold_days['date'].diff().dt.days
            cold_days['group'] = (cold_days['date_diff'] > 1).cumsum()
            cold_snaps = cold_days.groupby('group').filter(lambda x: len(x) >= 2)
            
            if not cold_snaps.empty:
                for group, snap in cold_snaps.groupby('group'):
                    start_date = snap['date'].min()
                    end_date = snap['date'].max()
                    min_temp = snap['temp_min'].min()
                    days = len(snap)
                    
                    events.append({
                        'type': 'Cold Snap',
                        'start_date': start_date,
                        'end_date': end_date,
                        'duration': days,
                        'max_value': min_temp,
                        'description': f"Cold snap with temperatures down to {min_temp:.1f}°C for {days} days"
                    })
        
        # Drought periods
        # Create a rolling window to find periods without significant rain
        historical_df['significant_rain'] = historical_df['rain_sum'] >= 1
        historical_df['days_without_rain'] = (~historical_df['significant_rain']).rolling(window=drought_threshold, min_periods=1).sum()
        
        drought_periods = historical_df[historical_df['days_without_rain'] >= drought_threshold]
        if not drought_periods.empty:
            # Group by month to avoid multiple drought events in the same period
            drought_periods['month_year'] = drought_periods['date'].dt.to_period('M')
            unique_droughts = drought_periods.groupby('month_year').first().reset_index()
            
            for _, row in unique_droughts.iterrows():
                events.append({
                    'type': 'Drought',
                    'start_date': row['date'] - pd.Timedelta(days=drought_threshold),
                    'end_date': row['date'],
                    'duration': drought_threshold,
                    'max_value': drought_threshold,
                    'description': f"Drought period of {drought_threshold}+ days without significant rainfall"
                })
        
        return events
