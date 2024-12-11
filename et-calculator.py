"""
ET Calculator Module
------------------
Implements the FAO-56 Penman-Monteith equation for calculating
reference evapotranspiration (ET0) and irrigation needs.
"""

import math
from typing import Dict, Tuple

class ETCalculator:
    def __init__(self):
        """Initialize ET calculator with constants."""
        # Soil characteristics for Schriever clay
        self.soil_params = {
            'clay': {
                'field_capacity': 0.36,  # m³/m³
                'wilting_point': 0.21,   # m³/m³
                'total_available_water': 150,  # mm per meter of soil
                'readily_available_water': 0.5  # fraction of TAW
            }
        }

    def calculate_et0(self, temp_max: float, temp_min: float, 
                     humidity: float, wind_speed: float, 
                     solar_radiation: float) -> float:
        """
        Calculate reference evapotranspiration using FAO-56 Penman-Monteith.
        
        Parameters:
        - temp_max: Maximum daily temperature (°C)
        - temp_min: Minimum daily temperature (°C)
        - humidity: Mean relative humidity (%)
        - wind_speed: Wind speed at 2m height (m/s)
        - solar_radiation: Solar radiation (MJ/m²/day)
        
        Returns:
        - ET0 in mm/day
        """
        # Mean daily temperature
        temp_mean = (temp_max + temp_min) / 2
        
        # Atmospheric pressure (kPa) at sea level
        P = 101.3
        
        # Psychrometric constant (kPa/°C)
        gamma = 0.665 * 10**-3 * P
        
        # Saturation vapour pressure (kPa)
        es_max = 0.6108 * math.exp(17.27 * temp_max / (temp_max + 237.3))
        es_min = 0.6108 * math.exp(17.27 * temp_min / (temp_min + 237.3))
        es = (es_max + es_min) / 2
        
        # Actual vapour pressure (kPa)
        ea = es * humidity / 100
        
        # Slope of saturation vapour pressure curve (kPa/°C)
        delta = 4098 * es / (temp_mean + 237.3)**2
        
        # Net radiation (MJ/m²/day)
        Rn = solar_radiation * (1 - 0.23)  # assuming albedo = 0.23
        
        # Soil heat flux (assumed negligible for daily calculations)
        G = 0
        
        # FAO-56 Penman-Monteith equation
        numerator = (0.408 * delta * (Rn - G) + 
                    gamma * 900 / (temp_mean + 273) * 
                    wind_speed * (es - ea))
        denominator = delta + gamma * (1 + 0.34 * wind_speed)
        
        et0 = numerator / denominator
        
        return max(0, et0)  # Ensure non-negative value

    def calculate_irrigation_needs(self, et0: float, rainfall: float, 
                                 soil_type: str) -> float:
        """
        Calculate irrigation depth needed based on ET0, rainfall, and soil type.
        
        Parameters:
        - et0: Reference evapotranspiration (mm/day)
        - rainfall: Daily rainfall (mm)
        - soil_type: Soil type ('clay' for Schriever clay)
        
        Returns:
        - Required irrigation depth (mm)
        """
        soil = self.soil_params[soil_type]
        
        # Effective rainfall (assuming 80% efficiency)
        effective_rain = min(rainfall * 0.8, et0)
        
        # Calculate net irrigation requirement
        irrigation_depth = max(0, et0 - effective_rain)
        
        # Adjust for soil moisture holding capacity
        max_application = soil['readily_available_water'] * soil['total_available_water']
        irrigation_depth = min(irrigation_depth, max_application)
        
        return irrigation_depth