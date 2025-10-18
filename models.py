from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time
    
class DatosPersona(BaseModel):
    id: int
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

# Modelo de datos para crear un nuevo turno
class TurnoCreate(BaseModel):
    fecha: date
    hora: time
    persona_id: int

#Modelo para turnos
class models_Turnos(BaseModel):
    id: Optional[int] = None
    fecha: date
    hora: time
    estado: str
    persona_id: int
    persona: Optional[DatosPersona] = None

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
class PersonaBase(BaseModel):
    nombre: str
    email: str
    dni: int
    telefono: str
    fecha_de_nacimiento: date
    habilitado_para_turno:Optional[bool] =bool

    model_config={
        "from_attributes": True
    }

class PersonaCreate(BaseModel):
    nombre: str
    email: str
    dni: int
    telefono: Optional[str] = None
    fecha_de_nacimiento: date

#Persona para la respuesta del Get(/turnos/fecha/) de los turnos por fecha
class PersonaInfo(BaseModel):
    nombre: str
    dni: int
#Turno para la respuesta del Get(/turnos/fecha/) de los turnos por fecha
class TurnoConPersonaPorFecha(BaseModel):
    id: int
    fecha: date
    hora: time
    estado: str
    persona_id: int
    persona: PersonaInfo

class TurnoCanceladoInfo(BaseModel):
    id: int
    persona_id: int
    fecha: date
    hora: time
    estado: str

class TurnosCanceladosPorMes(BaseModel):
    anio: int
    mes: str
    cantidad: int
    turnos: List[TurnoCanceladoInfo]

class TurnoCanceladoDetalle(BaseModel):
    """Detalle de cada turno cancelado"""
    id: int
    fecha: date
    hora: time
    estado: str

class PersonaConTurnosCancelados(BaseModel):
    """Información de la persona con turnos cancelados"""
    id: int
    nombre: str
    email: str
    dni: int
    telefono: str

class ReportePersonasConTurnosCancelados(BaseModel):
    """Modelo principal del reporte /reportes/turnos-cancelados"""
    persona: PersonaConTurnosCancelados
    cantidad_cancelados: int
    turnos: List[TurnoCanceladoDetalle]    
