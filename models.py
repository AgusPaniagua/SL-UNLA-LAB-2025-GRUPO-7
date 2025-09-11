from pydantic import BaseModel
from datetime import date, time

class models_Turnos(BaseModel):
    fecha: date
    hora: time
    estado: str
    persona_id: int

    model_config = {
        "from_attributes": True  # Así le decís a Pydantic v2 que use atributos del ORM
    }


