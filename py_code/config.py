
from pathlib import Path

###-----------------------CONFIG PARAMS-----------------------###

BEAT = 5 # 30 minuts (pendiente de cambiar a 30 minutos para la versión definitiva)

MOIST_SENSORS_CONFIG = [
    (0, 275, 682), # Sensor 1
    (1, 290, 685), # Sensor 2
    (2, 287, 683)  # Sensor 3
]


parent = Path(__file__).resolve().parent.parent
data_directory = parent / "data" 

rows_logged = 10
