#!/usr/bin/env python3
"""
Irrigation Control Application
----------------------------
Main application entry point that coordinates weather data collection, 
ET calculations, and irrigation scheduling based on FAO-56 methodology.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple

from db_handler import Database
from weather_service import WeatherService
from et_calculator import ETCalculator
from irrigation_scheduler import IrrigationScheduler
from config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('irrigation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class IrrigationApp:
    def __init__(self):
        """Initialize the irrigation application components."""
        self.config = ConfigManager()
        self.db = Database(self.config.get_db_config())
        self.weather_service = WeatherService(
            self.config.get_weather_api_key(),
            self.config.get_solar_api_key()
        )
        self.et_calculator = ETCalculator()
        self.scheduler = IrrigationScheduler(
            rotator_count=9,
            flow_rate=0.11  # MP Rotator flow rate in m³/hour at 2.8 bar
        )

    def setup(self):
        """Perform initial setup and database creation."""
        logger.info("Setting up irrigation application...")
        self.db.setup_database()
        
    def run_daily_cycle(self):
        """Execute daily irrigation cycle calculations and scheduling."""
        try:
            # Fetch weather data
            weather_data = self.weather_service.fetch_weather_data(
                self.config.get_location(),
                self.config.get_coordinates()
            )
            
            # Store weather data
            self.db.store_weather_data(weather_data)
            
            # Calculate ET0 using FAO-56 Penman-Monteith equation
            et0 = self.et_calculator.calculate_et0(
                temp_max=weather_data['temp_max'],
                temp_min=weather_data['temp_min'],
                humidity=weather_data['humidity'],
                wind_speed=weather_data['wind_speed'],
                solar_radiation=weather_data['solar_radiation']
            )
            
            # Calculate irrigation needs based on ET0 and rainfall
            irrigation_depth = self.et_calculator.calculate_irrigation_needs(
                et0=et0,
                rainfall=weather_data['rainfall'],
                soil_type='clay'  # Schriever clay
            )
            
            # Generate irrigation schedule
            schedule = self.scheduler.generate_schedule(
                irrigation_depth=irrigation_depth,
                start_time=datetime.now().replace(hour=5, minute=0)  # Start at 5 AM
            )
            
            # Store irrigation schedule
            self.db.store_irrigation_schedule(schedule)
            
            logger.info(f"Daily cycle completed - ET0: {et0:.2f} mm, "
                       f"Irrigation depth: {irrigation_depth:.2f} mm")
            
        except Exception as e:
            logger.error(f"Error in daily cycle: {str(e)}")
            raise

def main():
    """Main application entry point."""
    try:
        app = IrrigationApp()
        app.setup()
        
        while True:
            current_time = datetime.now()
            
            # Run daily at 4 AM
            if current_time.hour == 4 and current_time.minute == 0:
                app.run_daily_cycle()
                
            # Wait for 1 minute before next check
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Application shutdown requested")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    main()