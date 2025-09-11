from pydantic import BaseModel
from datetime import date, time

#Modelo para turnos
class models_Turnos(BaseModel):
    fecha: date
    hora: time
    estado: str
    persona_id: int

    model_config = {
        "from_attributes": True  # Así le decís a Pydantic v2 que use atributos del ORM
    }

#Modelo para personas
class DatosPersona(BaseModel):
    nombre: str
    email: str
    dni: int
    telefono: str
    fecha_de_nacimiento: date
    edad: int
    habilitado_para_turno: bool

    model_config={
        "from_attributes": True
    }


