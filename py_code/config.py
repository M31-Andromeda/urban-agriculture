
from pathlib import Path

###-----------------------CONFIG PARAMS-----------------------###


MOIST_SENSORS_CONFIG = [
    (0, 275, 682), # Sensor 1
    (1, 290, 685), # Sensor 2
    (2, 287, 683)  # Sensor 3
]
WATER_PUMP_PIN = 6
FANS_PIN = 5

#To conect with the script to update the google sheet
URL_APPSCRIPT = "https://script.google.com/macros/s/AKfycbyFNCn9OWuZSEPUOSEIZhJtWSEGQWEd3B1YFfZUxOJlJJaprr39rMuThdxxp7qogdQUbQ/exec" 


parent = Path(__file__).resolve().parent.parent
data_directory = parent / "data" 

BEAT = 30*60         
WINDOW_DAYS = 3       
rows_logged = int(WINDOW_DAYS * 24 * 60 * 60 / BEAT)


THRESHOLDS = {
    "soil_moisture_low_pct": 10,
    "soil_moisture_high_pct": 90,
    "env_temp_high": 33.0,
    "env_temp_low": 10.0,
    "plants_temp_high": 30.0,
    "light_low_lux": 200.0,
}
