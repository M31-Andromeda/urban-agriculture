from arduino.app_utils import *
import numpy as np

import config as c


logger = Logger("DecisionSystem")


class DecisionOrquestra:
    def __init__(self, garden, data_orchestra):
        self.garden = garden
        self.data_orchestra = data_orchestra
        
        


def decide(reading: dict, moisture_history: list) -> str:
    """Función pura: misma entrada -> misma salida, siempre.

    reading: diccionario con la lectura actual (garden.sensors_readings)
    moisture_history: lista de floats, histórico reciente de soil_moisture_(%)
                       (viene de data_orchestra.read_column_history(...))
    """
    # TODO 1: calcula moist_low y moist_high con np.percentile() sobre
    #         moisture_history — recuerda el caso de "aún no hay suficiente
    #         histórico" (¿cuántas lecturas mínimo te fiarías?) y un
    #         fallback razonable si no llega a ese mínimo.

    # TODO 2: aplica las reglas en cascada, en este orden:
    #         humedad -> temperatura (ventilar/alerta) -> luz -> si nada
    #         de lo anterior salta, "OK"
    pass