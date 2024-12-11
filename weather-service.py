"""
Weather Service Module
-------------------
Handles fetching weather data from Weatherbit.io and NREL APIs.
"""

import requests
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self, weather_api_key: str, solar_api_key: str):
        self.weather_api_key = weather_api_key
        self.solar_api_key = solar_api_key
        self.weather_base_url = "https://api.weatherbit.io/v2.0"
        self.solar_base_url = "https://developer.nrel.gov/api/solar"

    def fetch_weather_data(self, location: str, coordinates: Tuple[float, float]) -> Dict:
        """Fetch current weather data and solar radiation."""
        try:
            # Fetch current weather from Weatherbit
            weather = self._fetch_weatherbit_data(location)
            
            # Fetch solar radiation from NREL
            solar = self._fetch_nrel_data(*coordinates)
            
            return {
                'timestamp': weather['timestamp'],
                'temp_max': weather['temp_max'],
                'temp_min': weather['temp_min'],
                'humidity': weather['humidity'],
                'wind_speed': weather['wind_speed'],
                'rainfall': weather['rainfall'],
                'solar_radiation': solar['radiation']
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch weather data: {str(e)}")
            raise

    def _fetch_weatherbit_data(self, location: str) -> Dict:
        """Fetch data from Weatherbit API."""
        url = f"{self.weather_base_url}/current"
        params = {
            'city': location,
            'key': self.weather_api_key
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Weatherbit API error: {response.text}")
            
        data = response.json()['data'][0]
        return {
            'timestamp': data['ts'],
            'temp_max': data['max_temp'],
            'temp_min': data['min_temp'],
            'humidity': data['rh'],
            'wind_speed': data['wind_spd'],
            'rainfall': data['precip']
        }

    def _fetch_nrel_data(self, latitude: float, longitude: float) -> Dict:
        """Fetch solar radiation data from NREL API."""
        url = f"{self.solar_base_url}/solar_resource/v1.json"
        params = {
            'api_key': self.solar_api_key,
            'lat': latitude,
            'lon': longitude
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"NREL API error: {response.text}")
            
        data = response.json()
        return {
            'radiation': data['outputs']['avg_dni']['annual']
        }