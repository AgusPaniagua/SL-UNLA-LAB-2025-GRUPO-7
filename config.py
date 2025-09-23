import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="var_entorno.env")  

HORARIOS_DISPONIBLES = os.getenv("HORARIOS_DISPONIBLES", "")
if HORARIOS_DISPONIBLES:
    HORARIOS_DISPONIBLES = HORARIOS_DISPONIBLES.split(",")
else:
    HORARIOS_DISPONIBLES = []

ESTADOS_DISPONIBLES = os.getenv("ESTADOS_DISPONIBLES", "")
if ESTADOS_DISPONIBLES:
    ESTADOS_DISPONIBLES = ESTADOS_DISPONIBLES.split(",")
else:
    ESTADOS_DISPONIBLES = []
