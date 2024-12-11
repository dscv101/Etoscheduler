# Automated Irrigation Control System

A Python-based irrigation control system that uses weather data and the FAO-56 Penman-Monteith methodology to calculate evapotranspiration and automate irrigation scheduling for Hunter MP Rotators.

## Features

- Real-time weather data collection from Weatherbit.io
- Solar radiation data from NREL API 
- Evapotranspiration calculation using FAO-56 Penman-Monteith equation
- Plant-specific irrigation scheduling for:
  - Warm season turf grass
  - Azaleas
  - Dianella
  - Wax leaf privets
  - Begonia
- Automated irrigation scheduling for 9 Hunter MP Rotators
- PostgreSQL database storage for weather and irrigation data
- Dynamic adjustment based on rainfall
- Detailed logging system

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- API keys for:
  - Weatherbit.io (https://www.weatherbit.io/api)
  - NREL (https://developer.nrel.gov/signup/)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/irrigation-control.git
cd irrigation-control
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up the PostgreSQL database:
```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE irrigation;

# Connect to the new database
\c irrigation

# Import database schema (including plant data)
\i plant_schema.sql
```

## Configuration

1. Create a `config.json` file in the project root:
```json
{
    "weather_api_key": "your_weatherbit_api_key",
    "solar_api_key": "your_nrel_api_key",
    "location": "New Orleans",
    "coordinates": {
        "lat": 29.951065,
        "lon": -90.071533
    },
    "database": {
        "host": "localhost",
        "port": 5432,
        "dbname": "irrigation",
        "user": "postgres",
        "password": "your_password"
    }
}
```

Alternatively, you can set environment variables:
```bash
export WEATHER_API_KEY=your_weatherbit_api_key
export SOLAR_API_KEY=your_nrel_api_key
export LOCATION="New Orleans"
export LATITUDE=29.951065
export LONGITUDE=-90.071533
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=irrigation
export DB_USER=postgres
export DB_PASSWORD=your_password
```

## Project Structure

```
irrigation-control/
├── main.py                 # Main application entry point
├── config_manager.py       # Configuration handling
├── db_handler.py           # Database operations
├── et_calculator.py        # ET0 calculations
├── irrigation_scheduler.py # Irrigation scheduling
├── weather_service.py      # Weather data fetching
├── plant_schema.sql       # Plant database schema and data
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Running the Application

1. Verify database setup:
```bash
psql -U postgres -d irrigation
\dt  # Should show all tables including plant_types
```

2. Start the application:
```bash
python main.py
```

The application will:
- Run automatically at 4 AM daily
- Calculate irrigation needs based on weather conditions and plant types
- Generate and store irrigation schedules
- Log all activities to 'irrigation.log'

3. Monitor the application:
```bash
tail -f irrigation.log
```

## Database Schema

The application uses four main tables:

1. plant_types
   - Stores plant-specific parameters
   - Crop coefficients and growth characteristics
   - Allowable water depletion values

2. weather_data
   - Stores weather and solar radiation data
   - Daily measurements and calculations

3. irrigation_calcs
   - Stores ET0 calculations
   - Irrigation depth requirements

4. irrigation_schedule
   - Stores zone-specific irrigation schedules
   - Water volumes and durations

## Plant Management

To add or modify plant data:

1. Connect to the database:
```bash
psql -U postgres -d irrigation
```

2. Insert new plant data:
```sql
INSERT INTO plant_types 
(name, category, kc_ini, kc_mid, kc_end, root_depth_min, root_depth_max, 
height_max, water_depletion, growing_season_start, growing_season_end)
VALUES
('Plant Name', 'Category', 0.4, 0.6, 0.4, 0.3, 0.6, 1.2, 0.4, 3, 11);
```

## Troubleshooting

1. Database Connection Issues:
   - Verify PostgreSQL is running
   - Check database credentials
   - Ensure database exists and plant_types table is populated
   ```bash
   psql -U postgres -d irrigation -c "SELECT * FROM plant_types;"
   ```

2. API Issues:
   - Verify API keys are valid
   - Check internet connection
   - Confirm API rate limits

3. Irrigation Scheduling Issues:
   - Check log file for errors
   - Verify zone configuration
   - Confirm flow rate settings
   - Validate plant parameters in database

## Additional Resources

- FAO-56 Paper on Crop Evapotranspiration
- Hunter MP Rotator Technical Specifications
- Local Extension Office Guidelines for Plant Water Requirements

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.