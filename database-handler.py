"""
Database Handler Module
---------------------
Handles all database operations for the irrigation application including
plant parameters, weather data, and irrigation scheduling.
"""

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, config: Dict):
        """Initialize database connection with configuration."""
        self.config = config
        self.conn = None

    def connect(self):
        """Establish database connection."""
        if not self.conn or self.conn.closed:
            try:
                self.conn = psycopg2.connect(
                    dbname=self.config['dbname'],
                    user=self.config['user'],
                    password=self.config['password'],
                    host=self.config['host'],
                    port=self.config['port']
                )
            except Exception as e:
                logger.error(f"Failed to connect to database: {str(e)}")
                raise
        return self.conn

    def setup_database(self):
        """Create necessary database tables if they don't exist."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Create weather data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weather_data (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    temp_max FLOAT NOT NULL,
                    temp_min FLOAT NOT NULL,
                    humidity FLOAT NOT NULL,
                    wind_speed FLOAT NOT NULL,
                    solar_radiation FLOAT NOT NULL,
                    rainfall FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create irrigation calculations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS irrigation_calcs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    plant_id INTEGER NOT NULL,
                    et0 FLOAT NOT NULL,
                    etc FLOAT NOT NULL,
                    irrigation_depth FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plant_id) REFERENCES plant_types(id)
                )
            ''')
            
            # Create irrigation schedule table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS irrigation_schedule (
                    id SERIAL PRIMARY KEY,
                    plant_id INTEGER NOT NULL,
                    zone_id INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    water_volume FLOAT NOT NULL,
                    status VARCHAR(20) DEFAULT 'scheduled',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plant_id) REFERENCES plant_types(id)
                )
            ''')
            
            # Create index on timestamp fields for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_weather_timestamp 
                ON weather_data(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_irrigation_timestamp 
                ON irrigation_calcs(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_schedule_start_time 
                ON irrigation_schedule(start_time);
            ''')
            
            conn.commit()
            logger.info("Database setup completed successfully")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database setup failed: {str(e)}")
            raise
        finally:
            cursor.close()

    def get_plant_parameters(self, plant_name: str) -> Dict:
        """
        Retrieve plant-specific parameters from database.
        
        Args:
            plant_name: Name of the plant
            
        Returns:
            Dictionary containing plant parameters
            
        Raises:
            Exception if plant not found
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id, kc_ini, kc_mid, kc_end, root_depth_min, root_depth_max,
                       height_max, water_depletion, growing_season_start, 
                       growing_season_end
                FROM plant_types
                WHERE name = %s
            """
            cursor.execute(query, (plant_name,))
            result = cursor.fetchone()
            
            if not result:
                raise Exception(f"Plant type '{plant_name}' not found")
                
            return {
                'id': result[0],
                'kc_ini': result[1],
                'kc_mid': result[2],
                'kc_end': result[3],
                'root_depth_min': result[4],
                'root_depth_max': result[5],
                'height_max': result[6],
                'water_depletion': result[7],
                'growing_season_start': result[8],
                'growing_season_end': result[9]
            }
            
        finally:
            cursor.close()

    def store_weather_data(self, weather_data: Dict) -> int:
        """
        Store weather data in the database.
        
        Args:
            weather_data: Dictionary containing weather measurements
            
        Returns:
            ID of the inserted record
            
        Raises:
            Exception on database error
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = """
                INSERT INTO weather_data 
                (timestamp, temp_max, temp_min, humidity, wind_speed, 
                solar_radiation, rainfall)
                VALUES (%(timestamp)s, %(temp_max)s, %(temp_min)s, 
                %(humidity)s, %(wind_speed)s, %(solar_radiation)s, %(rainfall)s)
                RETURNING id
            """
            cursor.execute(query, weather_data)
            record_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"Stored weather data with ID: {record_id}")
            return record_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store weather data: {str(e)}")
            raise
        finally:
            cursor.close()

    def store_irrigation_calcs(self, calc_data: Dict) -> int:
        """
        Store irrigation calculations in the database.
        
        Args:
            calc_data: Dictionary containing ET and irrigation calculations
            
        Returns:
            ID of the inserted record
            
        Raises:
            Exception on database error
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = """
                INSERT INTO irrigation_calcs 
                (timestamp, plant_id, et0, etc, irrigation_depth)
                VALUES (%(timestamp)s, %(plant_id)s, %(et0)s, %(etc)s, 
                %(irrigation_depth)s)
                RETURNING id
            """
            cursor.execute(query, calc_data)
            record_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"Stored irrigation calculations with ID: {record_id}")
            return record_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store irrigation calculations: {str(e)}")
            raise
        finally:
            cursor.close()

    def store_irrigation_schedule(self, schedule: List[Dict]) -> List[int]:
        """
        Store irrigation schedule in the database.
        
        Args:
            schedule: List of schedule entries for each zone
            
        Returns:
            List of inserted record IDs
            
        Raises:
            Exception on database error
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = """
                INSERT INTO irrigation_schedule 
                (plant_id, zone_id, start_time, duration_minutes, water_volume)
                VALUES (%(plant_id)s, %(zone_id)s, %(start_time)s, 
                %(duration_minutes)s, %(water_volume)s)
                RETURNING id
            """
            record_ids = []
            for entry in schedule:
                cursor.execute(query, entry)
                record_ids.append(cursor.fetchone()[0])
                
            conn.commit()
            
            logger.info(f"Stored {len(record_ids)} schedule entries")
            return record_ids
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store irrigation schedule: {str(e)}")
            raise
        finally:
            cursor.close()

    def get_active_schedule(self, start_time: datetime) -> List[Dict]:
        """
        Retrieve active irrigation schedule for a given time.
        
        Args:
            start_time: Time to check for scheduled irrigation
            
        Returns:
            List of active schedule entries
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT is.id, pt.name as plant_name, is.zone_id, 
                       is.start_time, is.duration_minutes, is.water_volume,
                       is.status
                FROM irrigation_schedule is
                JOIN plant_types pt ON is.plant_id = pt.id
                WHERE is.start_time <= %s 
                AND is.start_time + INTERVAL '1 minute' * is.duration_minutes > %s
                AND is.status = 'scheduled'
                ORDER BY is.start_time
            """
            cursor.execute(query, (start_time, start_time))
            
            schedule = []
            for row in cursor.fetchall():
                schedule.append({
                    'id': row[0],
                    'plant_name': row[1],
                    'zone_id': row[2],
                    'start_time': row[3],
                    'duration_minutes': row[4],
                    'water_volume': row[5],
                    'status': row[6]
                })
                
            return schedule
            
        finally:
            cursor.close()

    def update_schedule_status(self, schedule_id: int, status: str):
        """
        Update the status of a schedule entry.
        
        Args:
            schedule_id: ID of the schedule entry
            status: New status ('completed', 'cancelled', etc.)
            
        Raises:
            Exception on database error
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = """
                UPDATE irrigation_schedule 
                SET status = %s 
                WHERE id = %s
            """
            cursor.execute(query, (status, schedule_id))
            conn.commit()
            
            logger.info(f"Updated schedule {schedule_id} status to {status}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update schedule status: {str(e)}")
            raise
        finally:
            cursor.close()