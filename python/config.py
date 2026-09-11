
import os
from pathlib import Path

MOIST_SENSORS_CONFIG = [
    (0, 275, 682), # Sensor 1
    (1, 290, 685), # Sensor 2
    (2, 287, 683)  # Sensor 3
]
WATER_PUMP_PIN = 6
FANS_PIN = 5

URL_APPSCRIPT = os.environ.get("URL_APPSCRIPT")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


parent = Path(__file__).resolve().parent.parent
data_directory = parent / "data"
decision_model_training_directory = parent / "decision_model_training"

sensors_csv_path = data_directory / "sensors_data.csv"
telegram_subscribers_path = data_directory / "telegram_subscribers.json"

decision_model_name = "decision_model.joblib"

BEAT = 20*60
DAYS_LOGGED = 2
rows_logged = int(DAYS_LOGGED * 24 * 60 * 60 / BEAT)

WATERING_DURATION = 30
VENTILATION_DURATION = 60

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
    "light_night_lux": 5.0,
    "moist_baseline_window": 24*60*60/BEAT,
    "moist_baseline_margin_pct": 10.0,
    "moist_absolute_floor_pct": 40.0,
}

FEATURES = [
    "soil_moisture_(%)", "soil_moisture_baseline", "moisture_vs_baseline",
    "env_temperature_(°C)", "env_humidity_(%)",
    "plants_temp_(°C)", "plants_hum_(%)",
    "light_intensity_(lux)", "power_(W)",
]

CAMERA_SETTINGS = {
    "camera_index" : 0,
    "resolution" : (1920, 1080),
    "jpeg_quality" : 95
}

IMAGE_MODEL_PATH = "  "