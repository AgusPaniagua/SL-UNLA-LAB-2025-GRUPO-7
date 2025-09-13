from pydantic import BaseModel
from typing import Optional
from datetime import date, time

#Modelo para turnos
class models_Turnos(BaseModel):
    id: Optional[int] = None
    fecha: date
    hora: time
    estado: str
    persona_id: int

    model_config = {
        "from_attributes": True  # Así le decís a Pydantic v2 que use atributos del ORM
    }
    
#Modelo para actualizar turnos
class TurnoUpdate(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[time] = None
    estado: Optional[str] = None
    persona_id: Optional[int] = None


#Modelo para personas
class DatosPersona(BaseModel):
    id: int  # Incluimos el ID para que Pydantic lo reconozca   
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


