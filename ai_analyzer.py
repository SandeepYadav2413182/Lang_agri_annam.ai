import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import datetime

class WeatherPatternAnalyzer:
    """
    Uses machine learning to analyze weather patterns and identify trends,
    anomalies, and make agricultural predictions based on historical and forecast data.
    """
    
    def __init__(self):
        """Initialize the analyzer with default parameters"""
        self.anomaly_detection_model = None
        self.pattern_clustering_model = None
        self.scaler = StandardScaler()
    
    def analyze_patterns(self, historical_df, forecast_df):
        """
        Analyze weather patterns using historical and forecast data
        
        Args:
            historical_df (pd.DataFrame): Processed historical weather data
            forecast_df (pd.DataFrame): Processed forecast weather data
            
        Returns:
            dict: Dictionary containing weather insights, anomalies, and trends
        """
        results = {
            'summary': '',
            'anomalies': [],
            'trends': [],
            'patterns': {}
        }
        
        if historical_df.empty:
            results['summary'] = "Insufficient historical data for analysis."
            return results
        
        try:
            # Prepare data
            analysis_df = self._prepare_data_for_analysis(historical_df)
            
            # Detect anomalies in historical data
            anomalies = self._detect_anomalies(analysis_df)
            
            # Identify weather patterns and clusters
            patterns = self._identify_patterns(analysis_df)
            
            # Analyze trends
            trends = self._analyze_trends(historical_df)
            
            # Predict upcoming weather based on patterns and forecast
            predictions = self._predict_upcoming_conditions(historical_df, forecast_df)
            
            # Generate natural language summary and insights
            summary = self._generate_summary(historical_df, forecast_df, anomalies, trends, patterns, predictions)
            
            # Compile results
            results['summary'] = summary
            results['anomalies'] = anomalies['descriptions']
            results['trends'] = trends['descriptions']
            results['patterns'] = patterns
            
            return results
        
        except Exception as e:
            print(f"Error in analyze_patterns: {str(e)}")
            results['summary'] = "An error occurred during weather pattern analysis."
            return results
    
    def _prepare_data_for_analysis(self, historical_df):
        """
        Prepare historical data for analysis by selecting relevant features
        and handling missing values
        
        Args:
            historical_df (pd.DataFrame): Historical weather data
            
        Returns:
            pd.DataFrame: Prepared DataFrame for analysis
        """
        # Make a copy to avoid modifying the original
        df = historical_df.copy()
        
        # Reset index if date is index
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
        
        # Select relevant columns for analysis
        analysis_columns = [
            'temp_avg', 'temp_min', 'temp_max', 
            'humidity_avg', 'rain_sum', 'wind_speed'
        ]
        
        # Ensure all required columns exist
        for col in analysis_columns:
            if col not in df.columns:
                df[col] = 0
        
        # Select only analysis columns
        analysis_df = df[analysis_columns].copy()
        
        # Handle missing values
        analysis_df = analysis_df.fillna(method='bfill').fillna(method='ffill').fillna(0)
        
        return analysis_df
    
    def _detect_anomalies(self, analysis_df):
        """
        Detect anomalies in the weather data using Isolation Forest
        
        Args:
            analysis_df (pd.DataFrame): Prepared DataFrame for analysis
            
        Returns:
            dict: Dictionary containing anomaly information
        """
        result = {
            'indices': [],
            'descriptions': []
        }
        
        try:
            # Scale the data
            scaled_data = self.scaler.fit_transform(analysis_df)
            
            # Initialize and fit the anomaly detection model
            self.anomaly_detection_model = IsolationForest(
                n_estimators=100, 
                contamination=0.05,  # Expect about 5% anomalies
                random_state=42
            )
            
            # Fit and predict
            predictions = self.anomaly_detection_model.fit_predict(scaled_data)
            
            # Find anomalies (indicated by -1)
            anomaly_indices = np.where(predictions == -1)[0]
            
            if len(anomaly_indices) > 0:
                result['indices'] = anomaly_indices.tolist()
                
                # Generate descriptions for each anomaly
                for idx in anomaly_indices:
                    anomaly_point = analysis_df.iloc[idx]
                    
                    # Determine what's unusual about this data point
                    unusual_features = []
                    
                    if anomaly_point['temp_max'] > analysis_df['temp_max'].quantile(0.95):
                        unusual_features.append(f"unusually high maximum temperature ({anomaly_point['temp_max']:.1f}°C)")
                    
                    if anomaly_point['temp_min'] < analysis_df['temp_min'].quantile(0.05):
                        unusual_features.append(f"unusually low minimum temperature ({anomaly_point['temp_min']:.1f}°C)")
                    
                    if anomaly_point['rain_sum'] > analysis_df['rain_sum'].quantile(0.95):
                        unusual_features.append(f"unusually high rainfall ({anomaly_point['rain_sum']:.1f}mm)")
                    
                    if anomaly_point['wind_speed'] > analysis_df['wind_speed'].quantile(0.95):
                        unusual_features.append(f"unusually high wind speed ({anomaly_point['wind_speed']:.1f}m/s)")
                    
                    if anomaly_point['humidity_avg'] > analysis_df['humidity_avg'].quantile(0.95):
                        unusual_features.append(f"unusually high humidity ({anomaly_point['humidity_avg']:.1f}%)")
                    
                    if anomaly_point['humidity_avg'] < analysis_df['humidity_avg'].quantile(0.05):
                        unusual_features.append(f"unusually low humidity ({anomaly_point['humidity_avg']:.1f}%)")
                    
                    # If we couldn't determine why it's unusual, use a generic description
                    if not unusual_features:
                        unusual_features.append("unusual combination of weather conditions")
                    
                    # Create description
                    description = f"Weather anomaly detected with {', '.join(unusual_features)}"
                    
                    # Only add if we don't have a very similar description already
                    if description not in result['descriptions']:
                        result['descriptions'].append(description)
                
                # Limit to top 5 most significant anomalies
                result['descriptions'] = result['descriptions'][:5]
            
            return result
        
        except Exception as e:
            print(f"Error in anomaly detection: {str(e)}")
            result['descriptions'].append("Unable to detect weather anomalies due to insufficient data.")
            return result
    
    def _identify_patterns(self, analysis_df):
        """
        Identify weather patterns using clustering methods
        
        Args:
            analysis_df (pd.DataFrame): Prepared DataFrame for analysis
            
        Returns:
            dict: Dictionary containing identified patterns
        """
        patterns = {
            'clusters': [],
            'seasonal_patterns': {}
        }
        
        try:
            # Scale the data
            scaled_data = self.scaler.fit_transform(analysis_df)
            
            # Determine optimal number of clusters (simplified method)
            n_clusters = min(5, len(analysis_df) // 10) if len(analysis_df) > 10 else 2
            
            # Initialize and fit the clustering model
            self.pattern_clustering_model = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = self.pattern_clustering_model.fit_predict(scaled_data)
            
            # Analyze each cluster
            for i in range(n_clusters):
                cluster_df = analysis_df[cluster_labels == i]
                
                # Skip if cluster is empty
                if len(cluster_df) == 0:
                    continue
                
                # Calculate cluster characteristics
                cluster_info = {
                    'id': i,
                    'size': len(cluster_df),
                    'percentage': len(cluster_df) / len(analysis_df) * 100,
                    'avg_temp': cluster_df['temp_avg'].mean(),
                    'avg_rain': cluster_df['rain_sum'].mean(),
                    'avg_humidity': cluster_df['humidity_avg'].mean(),
                    'description': self._generate_cluster_description(cluster_df)
                }
                
                patterns['clusters'].append(cluster_info)
            
            # Look for seasonal patterns if we have enough data
            # This would require having the date column, which isn't in analysis_df
            # In a real implementation, we would link back to the original data
            
            return patterns
            
        except Exception as e:
            print(f"Error in pattern identification: {str(e)}")
            return patterns
    
    def _generate_cluster_description(self, cluster_df):
        """
        Generate a natural language description of a weather cluster
        
        Args:
            cluster_df (pd.DataFrame): DataFrame containing data for a single cluster
            
        Returns:
            str: Natural language description of the cluster
        """
        # Determine temperature category
        avg_temp = cluster_df['temp_avg'].mean()
        if avg_temp < 5:
            temp_desc = "cold"
        elif avg_temp < 15:
            temp_desc = "cool"
        elif avg_temp < 25:
            temp_desc = "mild"
        else:
            temp_desc = "hot"
        
        # Determine rainfall category
        avg_rain = cluster_df['rain_sum'].mean()
        if avg_rain < 0.1:
            rain_desc = "dry"
        elif avg_rain < 2:
            rain_desc = "light precipitation"
        elif avg_rain < 10:
            rain_desc = "moderate precipitation"
        else:
            rain_desc = "heavy precipitation"
        
        # Determine humidity category
        avg_humidity = cluster_df['humidity_avg'].mean()
        if avg_humidity < 40:
            humidity_desc = "low humidity"
        elif avg_humidity < 70:
            humidity_desc = "moderate humidity"
        else:
            humidity_desc = "high humidity"
        
        # Determine wind category
        avg_wind = cluster_df['wind_speed'].mean()
        if avg_wind < 3:
            wind_desc = "light winds"
        elif avg_wind < 7:
            wind_desc = "moderate winds"
        else:
            wind_desc = "strong winds"
        
        # Create description
        description = f"{temp_desc} days with {rain_desc}, {humidity_desc}, and {wind_desc}"
        
        return description
    
    def _analyze_trends(self, historical_df):
        """
        Analyze trends in the historical weather data
        
        Args:
            historical_df (pd.DataFrame): Historical weather data
            
        Returns:
            dict: Dictionary containing trend information
        """
        result = {
            'trends': {},
            'descriptions': []
        }
        
        try:
            # Create a copy with date as index if it's not already
            df = historical_df.copy()
            if 'date' not in df.columns and not isinstance(df.index, pd.DatetimeIndex):
                # Can't analyze trends without dates
                result['descriptions'].append("Unable to analyze trends due to missing date information.")
                return result
            
            if 'date' in df.columns and not isinstance(df.index, pd.DatetimeIndex):
                df = df.set_index('date')
            
            # Ensure the index is sorted
            df = df.sort_index()
            
            # Check if we have enough data for trend analysis
            if len(df) < 30:
                result['descriptions'].append("Insufficient historical data for detailed trend analysis.")
                return result
            
            # Analyze temperature trends
            temp_trend = self._calculate_trend(df, 'temp_avg')
            
            if abs(temp_trend) > 0.01:
                direction = "increasing" if temp_trend > 0 else "decreasing"
                result['trends']['temperature'] = temp_trend
                result['descriptions'].append(f"Temperature has been {direction} by approximately {abs(temp_trend):.2f}°C per month.")
            
            # Analyze precipitation trends
            if 'rain_sum' in df.columns:
                rain_trend = self._calculate_trend(df, 'rain_sum')
                
                if abs(rain_trend) > 0.5:
                    direction = "increasing" if rain_trend > 0 else "decreasing"
                    result['trends']['precipitation'] = rain_trend
                    result['descriptions'].append(f"Precipitation has been {direction} by approximately {abs(rain_trend):.1f}mm per month.")
            
            # Analyze humidity trends
            if 'humidity_avg' in df.columns:
                humidity_trend = self._calculate_trend(df, 'humidity_avg')
                
                if abs(humidity_trend) > 0.5:
                    direction = "increasing" if humidity_trend > 0 else "decreasing"
                    result['trends']['humidity'] = humidity_trend
                    result['descriptions'].append(f"Humidity has been {direction} by approximately {abs(humidity_trend):.1f}% per month.")
            
            # Add general observations
            # Calculate rolling averages to smooth the data
            if len(df) >= 30:
                rolling_temp = df['temp_avg'].rolling(window=30).mean()
                last_month = rolling_temp.iloc[-30:].mean() if len(rolling_temp) >= 30 else None
                first_month = rolling_temp.iloc[:30].mean() if len(rolling_temp) >= 30 else None
                
                if last_month is not None and first_month is not None:
                    temp_change = last_month - first_month
                    if abs(temp_change) > 1:
                        direction = "warmer" if temp_change > 0 else "cooler"
                        result['descriptions'].append(f"The recent period has been {direction} than earlier periods by {abs(temp_change):.1f}°C on average.")
            
            # If no trends were detected
            if not result['descriptions']:
                result['descriptions'].append("No significant weather trends detected in the available data.")
            
            return result
        
        except Exception as e:
            print(f"Error in trend analysis: {str(e)}")
            result['descriptions'].append("Unable to analyze weather trends due to data issues.")
            return result
    
    def get_seasonal_recommendations(self, current_season, trends, historical_df):
        """
        Generate seasonal agricultural recommendations based on weather data
        
        Args:
            current_season (str): Current season ('Winter', 'Spring', 'Summer', 'Fall')
            trends (list): List of weather trend descriptions
            historical_df (pd.DataFrame): Historical weather data
            
        Returns:
            dict: Dictionary containing seasonal recommendations
        """
        recommendations = {
            'general': [],
            'crops': {}
        }
        
        try:
            # Extract some basic climate indicators
            avg_temp = historical_df['temp_avg'].mean() if 'temp_avg' in historical_df.columns else None
            rainfall = historical_df['rain_sum'].sum() if 'rain_sum' in historical_df.columns else None
            
            # Check for trends that might impact recommendations
            drought_risk = any('drought' in trend.lower() or 'dry' in trend.lower() for trend in trends)
            flood_risk = any('flood' in trend.lower() or 'heavy rain' in trend.lower() for trend in trends)
            temp_increasing = any('temperature' in trend.lower() and 'increasing' in trend.lower() for trend in trends)
            temp_decreasing = any('temperature' in trend.lower() and 'decreasing' in trend.lower() for trend in trends)
            
            # General recommendations based on season
            if current_season == 'Spring':
                recommendations['general'].extend([
                    "Prepare soil with proper amendments and nutrients",
                    "Start sowing cold-resistant varieties as soil warms up",
                    "Monitor soil moisture as temperatures begin to rise",
                    "Check for winter damage and repair irrigation systems"
                ])
                
                if drought_risk:
                    recommendations['general'].append("Consider installing moisture-preserving mulches")
                    
                if flood_risk:
                    recommendations['general'].append("Ensure proper drainage systems are operational")
                    
                recommendations['crops']['Leafy Greens'] = [
                    "Plant lettuces, spinach, and other greens early in the season",
                    "Use row covers to protect from late frosts"
                ]
                
                recommendations['crops']['Root Vegetables'] = [
                    "Prepare for planting carrots, radishes and beets",
                    "Ensure soil is loose and free of stones for good root development"
                ]
                
            elif current_season == 'Summer':
                recommendations['general'].extend([
                    "Monitor irrigation needs closely during hot periods",
                    "Apply mulch to reduce water evaporation from soil",
                    "Watch for heat stress in sensitive crops",
                    "Regular pest monitoring is crucial in warm weather"
                ])
                
                if drought_risk:
                    recommendations['general'].extend([
                        "Implement water conservation practices",
                        "Consider drip irrigation to minimize water loss"
                    ])
                    
                if flood_risk:
                    recommendations['general'].append("Ensure raised beds have adequate drainage")
                
                recommendations['crops']['Tomatoes'] = [
                    "Support plants with stakes or cages",
                    "Monitor for leaf diseases during humid periods"
                ]
                
                recommendations['crops']['Corn'] = [
                    "Ensure adequate water during tasseling stage",
                    "Consider side-dressing with nitrogen fertilizer"
                ]
                
            elif current_season == 'Fall':
                recommendations['general'].extend([
                    "Harvest summer crops and prepare for cold-season planting",
                    "Consider cover crops for fields that will remain fallow",
                    "Begin soil testing for next season planning",
                    "Clean and store tools and equipment properly"
                ])
                
                recommendations['crops']['Winter Greens'] = [
                    "Plant cold-hardy varieties like kale and collards",
                    "Consider row covers or cold frames for extending the season"
                ]
                
                recommendations['crops']['Root Vegetables'] = [
                    "Plant storage crops like carrots and beets for winter harvesting",
                    "Ensure proper storage conditions after harvest"
                ]
                
            else:  # Winter
                recommendations['general'].extend([
                    "Plan next season's crop rotation and purchases",
                    "Repair equipment and infrastructure during downtime",
                    "Review last season's notes and adjust planning accordingly",
                    "Monitor stored produce for any signs of spoilage"
                ])
                
                if temp_increasing:
                    recommendations['general'].append("Be prepared for early pest emergence if temperatures rise unusually")
                
                recommendations['crops']['Cold-Season Crops'] = [
                    "In warmer areas, consider planting frost-resistant varieties",
                    "Protect overwintering crops with appropriate covers"
                ]
            
            # Add recommendations about climate trends regardless of season
            if rainfall is not None and rainfall < 500:
                recommendations['general'].append("Annual rainfall is below average; consider drought-resistant crop varieties")
            elif rainfall is not None and rainfall > 1200:
                recommendations['general'].append("Annual rainfall is high; ensure good drainage and consider raised beds")
            
            if avg_temp is not None and temp_increasing:
                recommendations['general'].append("Temperatures are trending warmer; plan for earlier planting dates but watch for early season frost events")
            elif avg_temp is not None and temp_decreasing:
                recommendations['general'].append("Temperatures are trending cooler; consider cold-hardy varieties and season extension techniques")
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating seasonal recommendations: {str(e)}")
            # Provide fallback recommendations
            recommendations['general'].append("Plan your agricultural activities according to local seasonal patterns")
            return recommendations
    
    def _calculate_trend(self, df, column):
        """
        Calculate the trend (slopee) for a specific column in the dataframe
        
        Args:
            df (pd.DataFrame): DataFrame with datetime index
            column (str): Column name to analyze
            
        Returns:
            float: Trend value (change per month)
        """
        # Ensure we have the column
        if column not in df.columns:
            return 0
        
        # Drop NaN values
        data = df[column].dropna()
        
        # Check if we have enough data
        if len(data) < 10:
            return 0
        
        # Convert index to numeric (days since start)
        if isinstance(data.index, pd.DatetimeIndex):
            x = (data.index - data.index.min()).days.values
        else:
            # If not datetime index, use array indices
            x = np.arange(len(data))
        
        # Use linear regression to find the slope
        y = data.values
        
        # Add small epsilon to avoid division by zero
        if np.all(x == 0):
            x = x + np.linspace(0, 1, len(x))
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        
        # Convert to change per month (assuming x is in days)
        trend_per_month = slope * 30
        
        return trend_per_month
    
    def _predict_upcoming_conditions(self, historical_df, forecast_df):
        """
        Predict upcoming weather conditions based on historical patterns and forecast
        
        Args:
            historical_df (pd.DataFrame): Historical weather data
            forecast_df (pd.DataFrame): Forecast weather data
            
        Returns:
            dict: Dictionary containing predictions
        """
        predictions = {
            'forecast_analysis': '',
            'upcoming_patterns': [],
        }
        
        try:
            # Check if we have forecast data
            if forecast_df.empty:
                predictions['forecast_analysis'] = "No forecast data available for prediction."
                return predictions
            
            # Analyze the forecast data
            avg_forecast_temp = forecast_df['temp'].mean()
            max_forecast_temp = forecast_df['temp'].max()
            min_forecast_temp = forecast_df['temp'].min()
            
            total_forecast_rain = forecast_df['rain'].sum()
            avg_forecast_humidity = forecast_df['humidity'].mean()
            
            # Compare with historical averages
            if not historical_df.empty:
                avg_historical_temp = historical_df['temp_avg'].mean()
                temp_diff = avg_forecast_temp - avg_historical_temp
                
                temp_comparison = "similar to"
                if temp_diff > 3:
                    temp_comparison = "significantly warmer than"
                elif temp_diff > 1:
                    temp_comparison = "warmer than"
                elif temp_diff < -3:
                    temp_comparison = "significantly cooler than"
                elif temp_diff < -1:
                    temp_comparison = "cooler than"
                
                predictions['forecast_analysis'] = f"The upcoming period is forecasted to be {temp_comparison} historical averages."
                
                # Detect significant patterns in the forecast
                if max_forecast_temp > historical_df['temp_max'].quantile(0.9):
                    predictions['upcoming_patterns'].append(f"Unusually warm temperatures expected with highs reaching {max_forecast_temp:.1f}°C.")
                
                if min_forecast_temp < historical_df['temp_min'].quantile(0.1):
                    predictions['upcoming_patterns'].append(f"Unusually cool temperatures expected with lows reaching {min_forecast_temp:.1f}°C.")
                
                if 'rain_sum' in historical_df.columns:
                    avg_daily_rain = historical_df['rain_sum'].mean()
                    forecast_days = forecast_df['time'].nunique()
                    avg_forecast_daily_rain = total_forecast_rain / forecast_days if forecast_days > 0 else 0
                    
                    if avg_forecast_daily_rain > avg_daily_rain * 2:
                        predictions['upcoming_patterns'].append(f"Higher than average rainfall expected in the upcoming period.")
                    elif avg_forecast_daily_rain < avg_daily_rain * 0.5:
                        predictions['upcoming_patterns'].append(f"Drier than average conditions expected in the upcoming period.")
            else:
                predictions['forecast_analysis'] = "Unable to compare forecast with historical averages due to insufficient historical data."
            
            # Add general forecast summary
            predictions['upcoming_patterns'].append(
                f"Forecast shows average temperatures of {avg_forecast_temp:.1f}°C, with a total expected rainfall of {total_forecast_rain:.1f}mm."
            )
            
            # Look for significant changes within the forecast period
            if len(forecast_df) > 5:
                first_days = forecast_df.iloc[:3]
                last_days = forecast_df.iloc[-3:]
                
                temp_change = last_days['temp'].mean() - first_days['temp'].mean()
                
                if abs(temp_change) > 5:
                    direction = "increasing" if temp_change > 0 else "decreasing"
                    predictions['upcoming_patterns'].append(f"Temperatures are expected to be {direction} significantly during the forecast period.")
            
            return predictions
            
        except Exception as e:
            print(f"Error in predicting upcoming conditions: {str(e)}")
            predictions['forecast_analysis'] = "Unable to analyze forecast data due to an error."
            return predictions
    
    def _generate_summary(self, historical_df, forecast_df, anomalies, trends, patterns, predictions):
        """
        Generate a comprehensive natural language summary of the weather analysis
        
        Args:
            historical_df (pd.DataFrame): Historical weather data
            forecast_df (pd.DataFrame): Forecast weather data
            anomalies (dict): Anomaly detection results
            trends (dict): Trend analysis results
            patterns (dict): Pattern identification results
            predictions (dict): Weather predictions
            
        Returns:
            str: Natural language summary
        """
        summary_parts = []
        
        # Start with general historical data summary
        if not historical_df.empty:
            avg_temp = historical_df['temp_avg'].mean()
            summary_parts.append(f"Based on historical weather data, this region has an average temperature of {avg_temp:.1f}°C.")
            
            if 'rain_sum' in historical_df.columns:
                total_rain = historical_df['rain_sum'].sum()
                summary_parts.append(f"The area has received approximately {total_rain:.0f}mm of rainfall over the analyzed period.")
        
        # Add trend information
        if trends['descriptions']:
            summary_parts.append("Weather trends analysis reveals that " + trends['descriptions'][0].lower())
            
            if len(trends['descriptions']) > 1:
                summary_parts[-1] += " and " + trends['descriptions'][1].lower()
        
        # Add forecast analysis
        if predictions['forecast_analysis']:
            summary_parts.append(predictions['forecast_analysis'])
            
            if predictions['upcoming_patterns']:
                summary_parts.append(predictions['upcoming_patterns'][0])
        
        # Add anomaly information if relevant
        if anomalies['descriptions']:
            summary_parts.append("Weather anomalies have been detected, including " + anomalies['descriptions'][0].lower() + ".")
        
        # Add agricultural implications
        summary_parts.append(
            "These weather patterns suggest farmers should monitor soil moisture levels closely and adjust irrigation schedules accordingly."
        )
        
        # Connect all parts into a coherent summary
        summary = " ".join(summary_parts)
        
        return summary
    
    def get_seasonal_recommendations(self, current_season, trends, historical_df):
        """
        Generate seasonal agricultural recommendations based on weather data
        
        Args:
            current_season (str): Current season ('Winter', 'Spring', 'Summer', 'Fall')
            trends (list): List of weather trend descriptions
            historical_df (pd.DataFrame): Historical weather data
            
        Returns:
            dict: Dictionary containing seasonal recommendations
        """
        result = {
            'summary': '',
            'monthly_tasks': {}
        }
        
        # Season-specific recommendations
        if current_season == "Winter":
            result['summary'] = (
                "Winter planning focuses on soil preparation, equipment maintenance, and planning for spring planting. "
                "Review your crop rotation plans and order seeds well in advance. Consider conducting soil tests to "
                "determine nutrient needs for spring."
            )
            
            result['monthly_tasks'] = {
                'December': [
                    "Maintain drainage systems to prevent waterlogging",
                    "Service farm equipment while activity is low",
                    "Analyze previous season's data and plan crop rotations",
                    "Check stored crops for signs of spoilage or pests"
                ],
                'January': [
                    "Order seeds and supplies for spring planting",
                    "Conduct soil tests to determine spring fertilizer needs",
                    "Repair fences, buildings, and other infrastructure",
                    "Monitor overwintering crops for frost damage"
                ],
                'February': [
                    "Start seedlings indoors for early spring crops",
                    "Begin pruning fruit trees before bud break",
                    "Apply winter fertilizers if ground is not frozen",
                    "Plan irrigation system maintenance before spring"
                ]
            }
        
        elif current_season == "Spring":
            result['summary'] = (
                "Spring is the critical planting season. Prepare your fields once soil temperatures reach appropriate levels, "
                "being careful not to work wet soil. Monitor for early season pests as temperatures warm and implement "
                "your integrated pest management strategies."
            )
            
            result['monthly_tasks'] = {
                'March': [
                    "Prepare seedbeds once soil has dried sufficiently",
                    "Apply pre-planting fertilizers based on soil tests",
                    "Set up weather monitoring stations for the growing season",
                    "Begin early season weed control measures"
                ],
                'April': [
                    "Plant main season crops when soil temperature is optimal",
                    "Implement irrigation system as needed for germination",
                    "Monitor for early season pests and diseases",
                    "Apply post-emergence herbicides as needed"
                ],
                'May': [
                    "Complete planting of all warm-season crops",
                    "Thin seedlings to appropriate spacing",
                    "Begin regular scouting for pests and diseases",
                    "Apply side-dress fertilizers for early planted crops"
                ]
            }
        
        elif current_season == "Summer":
            result['summary'] = (
                "Summer is focused on crop management, irrigation, and pest control. Monitor soil moisture regularly "
                "and adjust irrigation schedules based on weather conditions and crop needs. Stay vigilant for "
                "pest and disease pressures which increase in warm weather."
            )
            
            result['monthly_tasks'] = {
                'June': [
                    "Implement efficient irrigation scheduling based on crop needs",
                    "Monitor for insect pests with increased activity in warm weather",
                    "Apply foliar fertilizers if tissue tests indicate deficiencies",
                    "Prepare for harvest of early season crops"
                ],
                'July': [
                    "Maintain consistent irrigation during peak water demand",
                    "Continue regular pest and disease monitoring",
                    "Apply fungicides preventatively during periods of high humidity",
                    "Plan for cover crop seeding after early harvests"
                ],
                'August': [
                    "Monitor crops for signs of heat stress",
                    "Adjust irrigation to account for any rainfall",
                    "Prepare harvesting equipment for upcoming harvest season",
                    "Begin soil preparation for fall planted crops"
                ]
            }
        
        else:  # Fall
            result['summary'] = (
                "Fall is harvest season and preparation for the following year. Focus on timely harvesting, proper crop storage, "
                "and establishment of winter cover crops. Perform post-harvest soil management practices and evaluate the "
                "season's performance for future planning."
            )
            
            result['monthly_tasks'] = {
                'September': [
                    "Harvest crops at optimal maturity to maximize quality",
                    "Plant cover crops in harvested fields to prevent erosion",
                    "Conduct soil testing after harvest to plan winter amendments",
                    "Clean and prepare storage facilities"
                ],
                'October': [
                    "Complete main crop harvest before frost damage",
                    "Apply fall fertilizers and soil amendments",
                    "Plant winter grains if part of rotation",
                    "Winterize irrigation systems to prevent freeze damage"
                ],
                'November': [
                    "Finish any remaining harvest activities",
                    "Complete fall tillage operations where appropriate",
                    "Apply winter weed control measures",
                    "Analyze yield data and begin planning for next season"
                ]
            }
        
        # Adjust recommendations based on detected weather trends
        if trends:
            for trend in trends:
                if "temperature has been increasing" in trend.lower():
                    result['summary'] += " Due to the warming trend, consider selecting heat-tolerant crop varieties and adjusting planting dates accordingly."
                
                elif "temperature has been decreasing" in trend.lower():
                    result['summary'] += " With the cooling trend observed, be prepared for potential early frosts and consider cold-hardy varieties."
                
                elif "precipitation has been increasing" in trend.lower():
                    result['summary'] += " The increasing precipitation trend suggests investing in improved drainage systems and raising beds for crops sensitive to waterlogging."
                
                elif "precipitation has been decreasing" in trend.lower():
                    result['summary'] += " With decreasing precipitation levels, prioritize drought-resistant crop varieties and efficient irrigation methods."
        
        # Add specific recommendations based on historical data if available
        if not historical_df.empty:
            # Check for frost risk
            if 'temp_min' in historical_df.columns:
                frost_days = (historical_df['temp_min'] < 0).sum()
                if current_season == "Spring" and frost_days > 0:
                    # Add frost warning to April tasks
                    result['monthly_tasks']['April'].append("Be prepared for potential late frosts based on historical patterns")
            
            # Check for heat stress risk
            if 'temp_max' in historical_df.columns:
                heat_days = (historical_df['temp_max'] > 32).sum()
                if current_season == "Summer" and heat_days > 10:
                    # Add heat stress management to July tasks
                    result['monthly_tasks']['July'].append("Implement heat stress management strategies during historically high-temperature periods")
        
        return result
