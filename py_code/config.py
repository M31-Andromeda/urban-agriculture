
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
    "low_pct": 10,
    "high_pct": 90,
    "env_temp_high": 40.0,
    "env_temp_low": 10.0,
    "plants_temp_high": 36.0,
    "plants_temp_low": 15.0,
    "light_low_lux": 10000.0,
    "light_intense_lux": 50000.0,
    "env_humidity_stress_low": 30.0,
    "env_humidity_fungal_high": 70.0,
    "plants_humidity_fungal_high": 80.0,
    "pumps_max_consum":1.0, 
    "fans_max_consum": 1.5,
    "uno_q_consum":1
}