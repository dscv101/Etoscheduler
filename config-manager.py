"""
Configuration Manager Module
-------------------------
Handles application configuration and settings.
"""

import os
import json
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        """Initialize configuration manager."""
        self.config_file = 'config.json'
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from file or environment variables."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Fall back to environment variables
        return {
            'weather_api_key': os.getenv('WEATHER_API_KEY'),
            'solar_api_key': os.getenv('SOLAR_API_KEY'),
            'location': os.getenv('LOCATION', 'New Orleans'),
            'coordinates': {
                'lat': float(os.getenv('LATITUDE', '29.951065')),
                'lon': float(os.getenv('LONGITUDE', '-90.071533'))
            },
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'dbname': os.getenv('DB_NAME', 'irrigation'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', '')
            }
        }

    def get_weather_api_key(self) -> str:
        """Get Weatherbit API key."""
        return self.config['weather_api_key']

    def get_solar_api_key(self) -> str:
        """Get NREL API key."""
        return self.config['solar_api_key']

    def get_location(self) -> str:
        """Get location name."""
        return self.config['location']

    def get_coordinates(self) -> Tuple[float, float]:
        """Get latitude and longitude."""
        return (
            self.config['coordinates']['lat'],
            self.config['coordinates']['lon']
        )

    def get_db_config(self) -> Dict:
        """Get database configuration."""
        return self.config['database']

    def save_config(self, config: Dict):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.config = config
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            raise