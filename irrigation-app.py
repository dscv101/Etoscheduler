#!/usr/bin/env python3
"""
Irrigation Control Application
----------------------------
Main application entry point that coordinates weather data collection, 
ET calculations, and irrigation scheduling based on FAO-56 methodology.
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, List

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
        
        # List of plants to manage
        self.plants = [
            'Warm Season Turf',
            'Azalea',
            'Dianella',
            'Wax Leaf Privet',
            'Begonia'
        ]

    def setup(self):
        """Perform initial setup and database creation."""
        try:
            logger.info("Setting up irrigation application...")
            self.db.setup_database()
            
            # Verify all plants exist in database
            for plant in self.plants:
                try:
                    self.db.get_plant_parameters(plant)
                except Exception as e:
                    logger.error(f"Plant '{plant}' not found in database: {str(e)}")
                    raise
                    
            logger.info("Application setup completed successfully")
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            raise
        
    def _calculate_irrigation_needs(self, weather_data: Dict, 
                                  plant_params: Dict) -> float:
        """Calculate irrigation needs for a specific plant type."""
        try:
            # Calculate ET0 using FAO-56 Penman-Monteith equation
            et0 = self.et_calculator.calculate_et0(
                temp_max=weather_data['temp_max'],
                temp_min=weather_data['temp_min'],
                humidity=weather_data['humidity'],
                wind_speed=weather_data['wind_speed'],
                solar_radiation=weather_data['solar_radiation']
            )
            
            # Apply crop coefficients and calculate irrigation depth
            kc = plant_params['kc_mid']  # Use mid-season Kc for now
            etc = et0 * kc
            
            # Calculate irrigation needs considering rainfall
            irrigation_depth = self.et_calculator.calculate_irrigation_needs(
                et0=etc,
                rainfall=weather_data['rainfall'],
                soil_type='clay',  # Schriever clay
                root_depth=plant_params['root_depth_max'],
                depletion_factor=plant_params['water_depletion']
            )
            
            return irrigation_depth
            
        except Exception as e:
            logger.error(f"Failed to calculate irrigation needs: {str(e)}")
            raise
            
    def run_daily_cycle(self):
        """Execute daily irrigation cycle calculations and scheduling."""
        try:
            logger.info("Starting daily irrigation cycle")
            
            # Fetch weather data
            weather_data = self.weather_service.fetch_weather_data(
                self.config.get_location(),
                self.config.get_coordinates()
            )
            
            # Store weather data
            self.db.store_weather_data(weather_data)
            
            # Process each plant type
            for plant_name in self.plants:
                try:
                    # Get plant parameters
                    plant_params = self.db.get_plant_parameters(plant_name)
                    
                    # Calculate irrigation needs
                    irrigation_depth = self._calculate_irrigation_needs(
                        weather_data,
                        plant_params
                    )
                    
                    # Skip irrigation if depth is negligible
                    if irrigation_depth < 0.5:  # Less than 0.5mm
                        logger.info(f"Skipping irrigation for {plant_name}: "
                                  f"depth {irrigation_depth:.2f}mm too small")
                        continue
                    
                    # Generate irrigation schedule for the plant
                    start_time = datetime.now().replace(
                        hour=5, minute=0, second=0, microsecond=0
                    )
                    
                    schedule = self.scheduler.generate_schedule(
                        irrigation_depth=irrigation_depth,
                        start_time=start_time,
                        plant_name=plant_name
                    )
                    
                    # Store irrigation schedule
                    self.db.store_irrigation_schedule(schedule)
                    
                    logger.info(f"Scheduled irrigation for {plant_name}: "
                              f"{irrigation_depth:.2f}mm")
                    
                except Exception as e:
                    logger.error(f"Failed to process {plant_name}: {str(e)}")
                    continue
            
            logger.info("Daily cycle completed successfully")
            
        except Exception as e:
            logger.error(f"Error in daily cycle: {str(e)}")
            raise

def main():
    """Main application entry point."""
    try:
        app = IrrigationApp()
        app.setup()
        
        logger.info("Application started, entering main loop")
        
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