import pandas as pd
import numpy as np
import random
import datetime

class CropRecommender:
    """
    Recommends suitable crops based on weather data and location.
    Uses climate data to suggest optimal crops and provide insights.
    """
    
    def __init__(self):
        """Initialize with crop data and recommendations"""
        # Define a list of common crops with their climate requirements
        # This would ideally come from a database in a real application
        self.crop_data = {
            'Corn': {
                'min_temp': 10,
                'max_temp': 35,
                'optimal_temp': 25,
                'min_rainfall': 500,  # mm per growing season
                'max_rainfall': 1200,
                'drought_tolerant': False,
                'frost_tolerant': False,
                'growing_season': 'Summer',
                'soil_pH': (5.5, 7.5)
            },
            'Wheat': {
                'min_temp': 3,
                'max_temp': 30,
                'optimal_temp': 20,
                'min_rainfall': 350,
                'max_rainfall': 1000,
                'drought_tolerant': True,
                'frost_tolerant': True,
                'growing_season': 'Winter/Spring',
                'soil_pH': (6.0, 7.5)
            },
            'Soybeans': {
                'min_temp': 10,
                'max_temp': 38,
                'optimal_temp': 27,
                'min_rainfall': 450,
                'max_rainfall': 1200,
                'drought_tolerant': False,
                'frost_tolerant': False,
                'growing_season': 'Summer',
                'soil_pH': (6.0, 7.0)
            },
            'Rice': {
                'min_temp': 16,
                'max_temp': 40,
                'optimal_temp': 30,
                'min_rainfall': 900,
                'max_rainfall': 2500,
                'drought_tolerant': False,
                'frost_tolerant': False,
                'growing_season': 'Summer',
                'soil_pH': (5.0, 6.5)
            },
            'Cotton': {
                'min_temp': 15,
                'max_temp': 40,
                'optimal_temp': 30,
                'min_rainfall': 500,
                'max_rainfall': 1500,
                'drought_tolerant': True,
                'frost_tolerant': False,
                'growing_season': 'Summer',
                'soil_pH': (5.5, 8.0)
            },
            'Potatoes': {
                'min_temp': 7,
                'max_temp': 30,
                'optimal_temp': 20,
                'min_rainfall': 500,
                'max_rainfall': 1000,
                'drought_tolerant': False,
                'frost_tolerant': False,
                'growing_season': 'Spring/Summer',
                'soil_pH': (5.0, 6.5)
            },
            'Tomatoes': {
                'min_temp': 10,
                'max_temp': 35,
                'optimal_temp': 25,
                'min_rainfall': 400,
                'max_rainfall': 1000,
                'drought_tolerant': False,
                'frost_tolerant': False,
                'growing_season': 'Summer',
                'soil_pH': (5.5, 7.5)
            },
            'Lettuce': {
                'min_temp': 5,
                'max_temp': 25,
                'optimal_temp': 18,
                'min_rainfall': 300,
                'max_rainfall': 800,
                'drought_tolerant': False,
                'frost_tolerant': True,
                'growing_season': 'Spring/Fall',
                'soil_pH': (6.0, 7.0)
            },
            'Carrots': {
                'min_temp': 7,
                'max_temp': 30,
                'optimal_temp': 18,
                'min_rainfall': 300,
                'max_rainfall': 900,
                'drought_tolerant': False,
                'frost_tolerant': True,
                'growing_season': 'Spring/Fall',
                'soil_pH': (5.5, 7.0)
            },
            'Barley': {
                'min_temp': 4,
                'max_temp': 30,
                'optimal_temp': 18,
                'min_rainfall': 300,
                'max_rainfall': 1000,
                'drought_tolerant': True,
                'frost_tolerant': True,
                'growing_season': 'Spring/Winter',
                'soil_pH': (6.0, 8.0)
            },
            'Oats': {
                'min_temp': 4,
                'max_temp': 32,
                'optimal_temp': 20,
                'min_rainfall': 350,
                'max_rainfall': 1000,
                'drought_tolerant': True,
                'frost_tolerant': True,
                'growing_season': 'Spring',
                'soil_pH': (5.0, 7.5)
            },
            'Sunflower': {
                'min_temp': 8,
                'max_temp': 35,
                'optimal_temp': 25,
                'min_rainfall': 300,
                'max_rainfall': 1000,
                'drought_tolerant': True,
                'frost_tolerant': False,
                'growing_season': 'Summer',
                'soil_pH': (6.0, 7.5)
            },
            'Alfalfa': {
                'min_temp': 5,
                'max_temp': 35,
                'optimal_temp': 25,
                'min_rainfall': 400,
                'max_rainfall': 1200,
                'drought_tolerant': True,
                'frost_tolerant': True,
                'growing_season': 'Perennial',
                'soil_pH': (6.5, 7.5)
            },
            'Sweet Corn': {
                'min_temp': 10,
                'max_temp': 35,
                'optimal_temp': 25,
                'min_rainfall': 500,
                'max_rainfall': 1200,
                'drought_tolerant': False,
                'frost_tolerant': False,
                'growing_season': 'Summer',
                'soil_pH': (5.5, 7.0)
            },
            'Peas': {
                'min_temp': 5,
                'max_temp': 24,
                'optimal_temp': 18,
                'min_rainfall': 350,
                'max_rainfall': 800,
                'drought_tolerant': False,
                'frost_tolerant': True,
                'growing_season': 'Spring/Fall',
                'soil_pH': (6.0, 7.0)
            }
        }
        
        self.available_crops = list(self.crop_data.keys())
    
    def recommend_crops(self, historical_df, forecast_df, lat, lon):
        """
        Recommend suitable crops based on weather data and location
        
        Args:
            historical_df (pd.DataFrame): Historical weather data
            forecast_df (pd.DataFrame): Forecast weather data
            lat (float): Latitude of the location
            lon (float): Longitude of the location
            
        Returns:
            list: List of recommended crops with confidence scores and reasons
        """
        recommendations = []
        
        try:
            # Extract key climate indicators from historical data
            climate_data = self._extract_climate_data(historical_df)
            
            # Add recent forecast data for near-term planning
            forecast_climate = self._extract_forecast_climate(forecast_df)
            
            # Determine current season
            current_month = datetime.datetime.now().month
            is_northern = lat > 0
            
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
            
            # Evaluate each crop's suitability based on climate data
            crop_scores = {}
            crop_reasons = {}
            
            for crop_name, crop_info in self.crop_data.items():
                # Skip crops that are out of season
                if current_season not in crop_info['growing_season'] and crop_info['growing_season'] != 'Perennial':
                    continue
                
                # Calculate match score based on temperature
                temp_score = self._calculate_temperature_score(
                    climate_data['avg_temp'], 
                    climate_data['min_temp'], 
                    climate_data['max_temp'],
                    crop_info['min_temp'],
                    crop_info['optimal_temp'],
                    crop_info['max_temp']
                )
                
                # Calculate match score based on rainfall
                rainfall_score = self._calculate_rainfall_score(
                    climate_data['annual_rainfall'],
                    crop_info['min_rainfall'],
                    crop_info['max_rainfall']
                )
                
                # Adjust for drought tolerance if needed
                if climate_data['drought_risk'] and not crop_info['drought_tolerant']:
                    rainfall_score *= 0.7
                
                # Adjust for frost risk
                if climate_data['frost_risk'] and not crop_info['frost_tolerant']:
                    temp_score *= 0.8
                
                # Combine scores (weight temperature higher than rainfall)
                overall_score = temp_score * 0.6 + rainfall_score * 0.4
                crop_scores[crop_name] = overall_score * 100  # Convert to percentage
                
                # Generate reasons for the recommendation
                reasons = []
                
                if temp_score > 0.8:
                    reasons.append(f"Temperature range ({climate_data['min_temp']:.1f}°C to {climate_data['max_temp']:.1f}°C) is ideal")
                elif temp_score > 0.6:
                    reasons.append(f"Temperature range is suitable")
                elif temp_score > 0.4:
                    reasons.append(f"Temperature range is acceptable but not optimal")
                else:
                    reasons.append(f"Temperature range may be challenging")
                
                if rainfall_score > 0.8:
                    reasons.append(f"Precipitation levels are ideal")
                elif rainfall_score > 0.6:
                    reasons.append(f"Precipitation levels are suitable")
                elif rainfall_score > 0.4:
                    reasons.append(f"Precipitation levels are acceptable with proper irrigation")
                else:
                    reasons.append(f"Irrigation will be necessary")
                
                if climate_data['drought_risk']:
                    if crop_info['drought_tolerant']:
                        reasons.append(f"Drought tolerance is advantageous in this climate")
                    else:
                        reasons.append(f"Drought risk requires careful water management")
                
                if climate_data['frost_risk']:
                    if crop_info['frost_tolerant']:
                        reasons.append(f"Frost tolerance is beneficial in this climate")
                    else:
                        reasons.append(f"Frost protection measures may be needed")
                
                crop_reasons[crop_name] = reasons
            
            # Sort crops by score and create recommendations
            sorted_crops = sorted(crop_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Return top crops (up to 5)
            for crop_name, score in sorted_crops[:5]:
                if score >= 40:  # Only recommend if score is at least 40%
                    recommendations.append({
                        'crop': crop_name,
                        'confidence': score,
                        'reasons': ". ".join(crop_reasons[crop_name])
                    })
            
            # If no crops meet the threshold, provide at least one option
            if not recommendations and sorted_crops:
                top_crop, score = sorted_crops[0]
                recommendations.append({
                    'crop': top_crop,
                    'confidence': score,
                    'reasons': ". ".join(crop_reasons[top_crop]) + ". Consider as experimental with proper adaptations."
                })
            
            return recommendations
            
        except Exception as e:
            print(f"Error in recommend_crops: {str(e)}")
            # Provide a fallback recommendation
            return [{
                'crop': 'General crops',
                'confidence': 50,
                'reasons': "Based on limited data analysis. Consider local successful crops as a guide."
            }]
    
    def get_crop_insights(self, crop_list, historical_df, forecast_df):
        """
        Get insights for specific crops selected by the user
        
        Args:
            crop_list (list): List of crop names to analyze
            historical_df (pd.DataFrame): Historical weather data
            forecast_df (pd.DataFrame): Forecast weather data
            
        Returns:
            dict: Dictionary with insights for each crop
        """
        insights = {}
        
        try:
            # Extract climate data
            climate_data = self._extract_climate_data(historical_df)
            forecast_climate = self._extract_forecast_climate(forecast_df)
            
            for crop_name in crop_list:
                if crop_name in self.crop_data:
                    crop_info = self.crop_data[crop_name]
                    
                    # Calculate match scores
                    temp_score = self._calculate_temperature_score(
                        climate_data['avg_temp'], 
                        climate_data['min_temp'], 
                        climate_data['max_temp'],
                        crop_info['min_temp'],
                        crop_info['optimal_temp'],
                        crop_info['max_temp']
                    )
                    
                    rainfall_score = self._calculate_rainfall_score(
                        climate_data['annual_rainfall'],
                        crop_info['min_rainfall'],
                        crop_info['max_rainfall']
                    )
                    
                    overall_score = temp_score * 0.6 + rainfall_score * 0.4
                    
                    # Determine suitability text
                    if overall_score > 0.8:
                        suitability = "Excellent match for this climate"
                    elif overall_score > 0.6:
                        suitability = "Good match with proper management"
                    elif overall_score > 0.4:
                        suitability = "Fair match with adaptations required"
                    else:
                        suitability = "Challenging match, consider alternatives"
                    
                    # Generate insights
                    summary = f"Overall climate suitability for {crop_name} is {overall_score*100:.0f}%."
                    
                    if temp_score < 0.6:
                        if climate_data['avg_temp'] < crop_info['optimal_temp']:
                            summary += f" The average temperature of {climate_data['avg_temp']:.1f}°C is below the optimal {crop_info['optimal_temp']}°C for this crop."
                        else:
                            summary += f" The average temperature of {climate_data['avg_temp']:.1f}°C is above the optimal {crop_info['optimal_temp']}°C for this crop."
                    
                    if rainfall_score < 0.6:
                        if climate_data['annual_rainfall'] < crop_info['min_rainfall']:
                            summary += f" Annual rainfall of {climate_data['annual_rainfall']:.0f}mm is below the minimum {crop_info['min_rainfall']}mm needed."
                        elif climate_data['annual_rainfall'] > crop_info['max_rainfall']:
                            summary += f" Annual rainfall of {climate_data['annual_rainfall']:.0f}mm exceeds the maximum {crop_info['max_rainfall']}mm recommended."
                    
                    # Generate challenges
                    challenges = []
                    
                    if climate_data['min_temp'] < crop_info['min_temp']:
                        challenges.append(f"Minimum temperatures of {climate_data['min_temp']:.1f}°C may be too cold (crop minimum: {crop_info['min_temp']}°C)")
                    
                    if climate_data['max_temp'] > crop_info['max_temp']:
                        challenges.append(f"Maximum temperatures of {climate_data['max_temp']:.1f}°C may cause heat stress (crop maximum: {crop_info['max_temp']}°C)")
                    
                    if climate_data['annual_rainfall'] < crop_info['min_rainfall']:
                        challenges.append(f"Insufficient natural rainfall ({climate_data['annual_rainfall']:.0f}mm vs. needed {crop_info['min_rainfall']}mm)")
                    
                    if climate_data['annual_rainfall'] > crop_info['max_rainfall']:
                        challenges.append(f"Excessive rainfall may increase disease pressure ({climate_data['annual_rainfall']:.0f}mm vs. optimal maximum {crop_info['max_rainfall']}mm)")
                    
                    if climate_data['drought_risk'] and not crop_info['drought_tolerant']:
                        challenges.append("Drought periods may affect crop development as this variety has low drought tolerance")
                    
                    if climate_data['frost_risk'] and not crop_info['frost_tolerant']:
                        challenges.append("Frost risk may damage crops as this variety has low frost tolerance")
                    
                    # Generate recommendations
                    recommendations = []
                    
                    if climate_data['min_temp'] < crop_info['min_temp']:
                        recommendations.append("Consider using row covers or high tunnels for cold protection")
                        recommendations.append("Plant after risk of frost has passed")
                    
                    if climate_data['max_temp'] > crop_info['max_temp']:
                        recommendations.append("Use shade cloth during peak heat periods")
                        recommendations.append("Plant early to avoid peak summer heat for maturation")
                    
                    if climate_data['annual_rainfall'] < crop_info['min_rainfall']:
                        recommendations.append("Implement efficient irrigation systems")
                        recommendations.append("Use mulch to conserve soil moisture")
                    
                    if climate_data['annual_rainfall'] > crop_info['max_rainfall']:
                        recommendations.append("Ensure good drainage to prevent waterlogging")
                        recommendations.append("Consider raised beds to improve drainage")
                        recommendations.append("Implement disease monitoring and prevention strategies")
                    
                    if climate_data['drought_risk'] and not crop_info['drought_tolerant']:
                        recommendations.append("Develop a drought contingency irrigation plan")
                        recommendations.append("Consider drought-resistant varieties or alternative crops")
                    
                    if climate_data['frost_risk'] and not crop_info['frost_tolerant']:
                        recommendations.append("Have frost protection measures ready (covers, sprinklers)")
                        recommendations.append("Monitor weather forecasts closely during frost-risk periods")
                    
                    # If no specific challenges, add general recommendations
                    if not challenges:
                        challenges.append("No major climate challenges identified for this crop")
                    
                    if not recommendations:
                        recommendations.append("Follow standard agricultural practices for this crop")
                        recommendations.append("Monitor for pests and diseases common to this crop")
                    
                    # Store insights
                    insights[crop_name] = {
                        'suitability': suitability,
                        'summary': summary,
                        'challenges': challenges,
                        'recommendations': recommendations
                    }
                
            return insights
            
        except Exception as e:
            print(f"Error in get_crop_insights: {str(e)}")
            # Return basic insights if there's an error
            default_insight = {
                'suitability': "Unable to determine accurately",
                'summary': "Analysis could not be completed with the available data.",
                'challenges': ["Insufficient climate data for detailed analysis"],
                'recommendations': ["Consult local agricultural extension services for specific advice"]
            }
            
            return {crop: default_insight for crop in crop_list}
    
    def _extract_climate_data(self, historical_df):
        """
        Extract key climate indicators from historical data
        
        Args:
            historical_df (pd.DataFrame): Historical weather data
            
        Returns:
            dict: Dictionary of climate indicators
        """
        climate_data = {
            'avg_temp': 20,  # Default values in case of missing data
            'min_temp': 5,
            'max_temp': 35,
            'annual_rainfall': 800,
            'drought_risk': False,
            'frost_risk': False
        }
        
        # If we have valid historical data, calculate actual values
        if not historical_df.empty:
            if 'temp_avg' in historical_df.columns:
                climate_data['avg_temp'] = historical_df['temp_avg'].mean()
            
            if 'temp_min' in historical_df.columns:
                climate_data['min_temp'] = historical_df['temp_min'].min()
                # Check frost risk
                climate_data['frost_risk'] = (historical_df['temp_min'] < 0).sum() > 5
            
            if 'temp_max' in historical_df.columns:
                climate_data['max_temp'] = historical_df['temp_max'].max()
            
            # Calculate annual rainfall
            if 'rain_sum' in historical_df.columns:
                climate_data['annual_rainfall'] = historical_df['rain_sum'].sum()
                
                # Check for drought risk - look for extended periods without rain
                if len(historical_df) > 30:  # Only if we have enough data
                    historical_df['dry_day'] = historical_df['rain_sum'] < 1
                    historical_df['dry_spell'] = (historical_df['dry_day'].rolling(window=15, min_periods=15).sum() >= 13)
                    climate_data['drought_risk'] = historical_df['dry_spell'].any()
        
        return climate_data
    
    def _extract_forecast_climate(self, forecast_df):
        """
        Extract climate indicators from forecast data
        
        Args:
            forecast_df (pd.DataFrame): Forecast weather data
            
        Returns:
            dict: Dictionary of forecast climate indicators
        """
        forecast_climate = {
            'avg_temp': 20,
            'min_temp': 10,
            'max_temp': 30,
            'total_rainfall': 0,
            'forecast_days': 0,
            'high_temp_days': 0,
            'low_temp_days': 0,
            'rainy_days': 0
        }
        
        if not forecast_df.empty:
            forecast_climate['avg_temp'] = forecast_df['temp'].mean()
            forecast_climate['min_temp'] = forecast_df['temp'].min()
            forecast_climate['max_temp'] = forecast_df['temp'].max()
            
            # Get unique days in forecast
            if 'time' in forecast_df.columns:
                unique_days = forecast_df['time'].dt.date.nunique()
                forecast_climate['forecast_days'] = unique_days
            
            # Calculate total rainfall
            if 'rain' in forecast_df.columns:
                forecast_climate['total_rainfall'] = forecast_df['rain'].sum()
                forecast_climate['rainy_days'] = (forecast_df['rain'] > 0).sum()
            
            # Count high temp days
            forecast_climate['high_temp_days'] = (forecast_df['temp'] > 30).sum()
            
            # Count low temp days
            forecast_climate['low_temp_days'] = (forecast_df['temp'] < 5).sum()
        
        return forecast_climate
    
    def _calculate_temperature_score(self, avg_temp, min_temp, max_temp, crop_min, crop_optimal, crop_max):
        """
        Calculate how well temperatures match crop requirements
        
        Args:
            avg_temp (float): Average temperature
            min_temp (float): Minimum temperature
            max_temp (float): Maximum temperature
            crop_min (float): Crop minimum temperature tolerance
            crop_optimal (float): Crop optimal temperature
            crop_max (float): Crop maximum temperature tolerance
            
        Returns:
            float: Score between 0 and 1 representing match quality
        """
        # Check if temperature range is completely outside crop tolerance
        if max_temp < crop_min or min_temp > crop_max:
            return 0.1  # Very poor match, but not impossible
        
        # Calculate how close average temp is to optimal
        optimal_score = 1.0 - min(abs(avg_temp - crop_optimal) / 15.0, 1.0)
        
        # Check if extremes are within tolerance but close to limits
        range_penalty = 0
        
        if min_temp < crop_min:
            range_penalty += 0.3 * (crop_min - min_temp) / crop_min
        
        if max_temp > crop_max:
            range_penalty += 0.3 * (max_temp - crop_max) / crop_max
        
        # Combine scores
        score = optimal_score * (1.0 - range_penalty)
        
        # Ensure score is between 0 and 1
        return max(0.1, min(score, 1.0))
    
    def _calculate_rainfall_score(self, annual_rainfall, crop_min_rain, crop_max_rain):
        """
        Calculate how well rainfall matches crop requirements
        
        Args:
            annual_rainfall (float): Annual rainfall in mm
            crop_min_rain (float): Minimum rainfall needed by crop
            crop_max_rain (float): Maximum rainfall tolerated by crop
            
        Returns:
            float: Score between 0 and 1 representing match quality
        """
        # If rainfall is seriously insufficient, allow for irrigation
        if annual_rainfall < crop_min_rain * 0.5:
            return 0.3  # Assuming irrigation is available but costly
        
        # If rainfall exceeds maximum by a lot, poor drainage may be an issue
        if annual_rainfall > crop_max_rain * 1.5:
            return 0.4  # Assuming some drainage solutions can be implemented
        
        # If within optimal range
        if crop_min_rain <= annual_rainfall <= crop_max_rain:
            # Calculate position within optimal range (higher score in middle)
            range_size = crop_max_rain - crop_min_rain
            position = (annual_rainfall - crop_min_rain) / range_size if range_size > 0 else 0.5
            
            # Highest score when in middle of optimal range
            position_score = 1.0 - abs(0.5 - position)
            
            return 0.8 + (position_score * 0.2)  # Score between 0.8 and 1.0
        
        # If outside optimal range but within tolerance
        if annual_rainfall < crop_min_rain:
            # Score decreases as rainfall decreases below minimum
            shortfall_ratio = annual_rainfall / crop_min_rain
            return 0.4 + (shortfall_ratio * 0.4)
        else:  # annual_rainfall > crop_max_rain
            # Score decreases as rainfall increases above maximum
            excess_ratio = min(crop_max_rain / annual_rainfall, 1.0)
            return 0.4 + (excess_ratio * 0.4)
