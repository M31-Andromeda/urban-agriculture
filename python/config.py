
import os
from pathlib import Path

###-----------------------CONFIG PARAMS-----------------------###


MOIST_SENSORS_CONFIG = [
    (0, 275, 682), # Sensor 1
    (1, 290, 685), # Sensor 2
    (2, 287, 683)  # Sensor 3
]
WATER_PUMP_PIN = 6
FANS_PIN = 5

# Apps Script endpoint that syncs sensor data to the Google Sheet. Treated as a secret
# (it grants write access to the sheet), so it is read from an environment variable
# instead of being hardcoded:
#   - Manual workflow: export URL_APPSCRIPT before running `python3 main.py`
#     (e.g. add `export URL_APPSCRIPT="..."` to your venv activation script).
#   - App Lab: set it as an environment variable in the App's Brick Configuration.
URL_APPSCRIPT = os.environ.get("URL_APPSCRIPT")


parent = Path(__file__).resolve().parent.parent
data_directory = parent / "data" 

decision_model_name = "decision_model.joblib"

BEAT = 20*60  # seconds between sensor readings (20 min)         
DAYS_LOGGED = 2       
rows_logged = int(DAYS_LOGGED * 24 * 60 * 60 / BEAT)

THRESHOLDS = {
    "env_temp_high": 37.5,
    "env_temp_low": 10.0,
    "plants_temp_high": 36.0,
    "plants_temp_low": 15.0,
    "light_low_lux": 10000.0,
    "env_humidity_stress_low": 30.0,
    "env_humidity_fungal_high": 70.0,
    "plants_humidity_fungal_high": 80.0,
    "pumps_max_consum":1.0,
    "fans_max_consum": 1.5,
    "uno_q_consum":1,
    "light_night_lux": 5.0,                 # below this, treat as night (real 0 isn't always bit-exact)
    "moist_baseline_window": 24*60*60/BEAT, # 1 days @ 30 min beat
    "moist_baseline_margin_pct": 10.0,      # points above/below baseline = high/low
    "moist_absolute_floor_pct": 40.0,       # backstop: always water below this, regardless of baseline
}

#model features used for training and prediction
FEATURES = [
    "soil_moisture_(%)", "soil_moisture_baseline", "moisture_vs_baseline",
    "env_temperature_(°C)", "env_humidity_(%)",
    "plants_temp_(°C)", "plants_hum_(%)",
    "light_intensity_(lux)", "power_(W)",
]