"""
Database Handler Module
---------------------
Handles all database operations for the irrigation application.
"""

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from typing import Dict, List

class Database:
    def __init__(self, config: Dict):
        """Initialize database connection with configuration."""
        self.config = config
        self.conn = None

    def connect(self):
        """Establish database connection."""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(
                dbname=self.config['dbname'],
                user=self.config['user'],
                password=self.config['password'],
                host=self.config['host'],
                port=self.config['port']
            )
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
                    temp_max FLOAT,
                    temp_min FLOAT,
                    humidity FLOAT,
                    wind_speed FLOAT,
                    solar_radiation FLOAT,
                    rainfall FLOAT
                )
            ''')
            
            # Create ET and irrigation calculations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS irrigation_calcs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    et0 FLOAT,
                    irrigation_depth FLOAT
                )
            ''')
            
            # Create irrigation schedule table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS irrigation_schedule (
                    id SERIAL PRIMARY KEY,
                    zone_id INTEGER,
                    start_time TIMESTAMP,
                    duration_minutes INTEGER,
                    water_volume FLOAT
                )
            ''')
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Database setup failed: {str(e)}")
        finally:
            cursor.close()

    def store_weather_data(self, weather_data: Dict):
        """Store weather data in the database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = """
                INSERT INTO weather_data 
                (timestamp, temp_max, temp_min, humidity, wind_speed, 
                solar_radiation, rainfall)
                VALUES (%(timestamp)s, %(temp_max)s, %(temp_min)s, 
                %(humidity)s, %(wind_speed)s, %(solar_radiation)s, %(rainfall)s)
            """
            cursor.execute(query, weather_data)
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to store weather data: {str(e)}")
        finally:
            cursor.close()

    def store_irrigation_schedule(self, schedule: List[Dict]):
        """Store irrigation schedule in the database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = """
                INSERT INTO irrigation_schedule 
                (zone_id, start_time, duration_minutes, water_volume)
                VALUES (%(zone_id)s, %(start_time)s, %(duration_minutes)s, 
                %(water_volume)s)
            """
            execute_values(cursor, query, schedule)
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to store irrigation schedule: {str(e)}")
        finally:
            cursor.close()