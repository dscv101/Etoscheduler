"""
Irrigation Scheduler Module
------------------------
Handles scheduling of irrigation zones based on calculated water requirements.
"""

from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class IrrigationScheduler:
    def __init__(self, rotator_count: int, flow_rate: float):
        """
        Initialize scheduler with system parameters.
        
        Args:
            rotator_count: Number of MP Rotator zones
            flow_rate: Flow rate per rotator in m³/hour
        """
        self.rotator_count = rotator_count
        self.flow_rate = flow_rate
        self.zone_area = 100  # m² per zone (approximate)
        
    def generate_schedule(self, irrigation_depth: float, 
                         start_time: datetime) -> List[Dict]:
        """
        Generate irrigation schedule for all zones.
        
        Args:
            irrigation_depth: Required irrigation depth in mm
            start_time: Schedule start time
            
        Returns:
            List of schedule entries per zone
        """
        try:
            # Convert irrigation depth to volume
            volume_per_zone = (irrigation_depth * self.zone_area) / 1000  # m³
            
            # Calculate runtime in minutes
            runtime = int((volume_per_zone / self.flow_rate) * 60)
            
            # Generate schedule
            schedule = []
            current_time = start_time
            
            for zone in range(1, self.rotator_count + 1):
                schedule.append({
                    'zone_id': zone,
                    'start_time': current_time,
                    'duration_minutes': runtime,
                    'water_volume': volume_per_zone
                })
                
                current_time += timedelta(minutes=runtime)
            
            logger.info(f"Generated schedule for {self.rotator_count} zones, "
                       f"{runtime} minutes per zone")
            return schedule
            
        except Exception as e:
            logger.error(f"Failed to generate schedule: {str(e)}")
            raise