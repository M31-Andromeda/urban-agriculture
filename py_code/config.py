
from pathlib import Path

###-----------------------CONFIG PARAMS-----------------------###

BEAT = 10 # 30 minuts (pendiente de cambiar a 30 minutos para la versión definitiva)

MOIST_SENSORS_CONFIG = [
    (0, 275, 682), # Sensor 1
    (1, 290, 685), # Sensor 2
    (2, 287, 683)  # Sensor 3
]

#To conect with the script to update the google sheet
URL_APPSCRIPT = "https://script.google.com/macros/s/AKfycbyFNCn9OWuZSEPUOSEIZhJtWSEGQWEd3B1YFfZUxOJlJJaprr39rMuThdxxp7qogdQUbQ/exec" 


parent = Path(__file__).resolve().parent.parent
data_directory = parent / "data" 

rows_logged = 5
