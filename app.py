from fastapi import FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session
from database import SessionLocal, Turnos, Persona
import models  # models.models_Turnos = modelo Pydantic
from datetime import date
from typing import Optional

from pydantic import BaseModel
from datetime import date, time

# Modelo de datos para crear una nueva persona
class PersonaCreate(BaseModel):
    nombre: str
    email: str
    dni: int
    telefono: Optional[str] = None
    fecha_de_nacimiento: date

# Modelo de datos para crear un nuevo turno
class TurnoCreate(BaseModel):
    fecha: date
    hora: time
    persona_id: int

#Creacion de la instancia de FastApi
app = FastAPI()
#Creacion de la session de base de datos
db: Session = SessionLocal()

@app.get("/")
def doc():
    return "Hola,presentamos la Api en python del Grupo 7"

#Endpoints para turnos
# Tener en cuenta al crear POST las siguientes validaciones:
# Los estados posibles de un turno son pendiente, cancelado, confirmado y asistido. 
# Los turnos deberán ser creados con estado "pendiente". 
ESTADOS_VALIDOS = {"pendiente", "cancelado", "confirmado", "asistido"}
@app.get("/turnos/", response_model=list[models.models_Turnos])
def leer_turnos():
    turnos = db.query(Turnos).all()
    return turnos

@app.get("/turnos/{turno_id}", response_model=models.models_Turnos)
def leer_turno(turno_id: int):
    turno = db.query(Turnos).filter(Turnos.id == turno_id).first()
    if turno is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
    return turno

@app.put("/turnos/{turno_id}", response_model=models.models_Turnos)
def actualizar_turno(turno_id: int, turno_actualizado: models.TurnoUpdate):
    turno = db.query(Turnos).filter(Turnos.id == turno_id).first()
    if turno is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
    
    hubo_Cambios = False
    if turno_actualizado.fecha is not None: 
        turno.fecha = turno_actualizado.fecha
        hubo_Cambios = True
    if turno_actualizado.hora is not None:     
        turno.hora = turno_actualizado.hora
        hubo_Cambios = True
    if turno_actualizado.estado is not None:
        if turno_actualizado.estado in ESTADOS_VALIDOS:
            turno.estado = turno_actualizado.estado
            hubo_Cambios = True
        else:
            if turno_actualizado.estado is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estado inválido. Debe ser: pendiente, cancelado, confirmado o asistido.") 
    if turno_actualizado.persona_id is not None:
        turno.persona_id = turno_actualizado.persona_id
        hubo_Cambios = True

    if hubo_Cambios == False:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
         
    db.commit()
    db.refresh(turno)
    return turno

@app.delete("/turnos/{turno_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_turno(turno_id: int):
    turno = db.query(Turnos).filter(Turnos.id == turno_id).first()
    if turno is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
    db.delete(turno)
    db.commit()
    return

#Endpoints para personas

@app.get("/personas/", response_model=list[models.DatosPersona])
def traer_personas():
    personas = db.query(Persona).all()
    return personas

# POST /personas
# Endpoint para crear una nueva persona en la base de datos
# Recibe los datos necesarios mediante el modelo PersonaCreate
# Calcula automáticamente la edad y establece habilitado_para_turno en True

@app.post("/personas/", response_model=models.DatosPersona, status_code=status.HTTP_201_CREATED)
def crear_persona(persona: PersonaCreate):
    # Calcular edad a partir de la fecha de nacimiento
    hoy = date.today()
    edad = hoy.year - persona.fecha_de_nacimiento.year - (
        (hoy.month, hoy.day) < (persona.fecha_de_nacimiento.month, persona.fecha_de_nacimiento.day)
    )

# Crear instancia de Persona para guardar en la base de datos
    nueva_persona = Persona(
        nombre=persona.nombre,
        email=persona.email,
        dni=persona.dni,
        telefono=persona.telefono,
        fecha_de_nacimiento=persona.fecha_de_nacimiento,
        edad=edad,
        habilitado_para_turno=True  # Por defecto habilitado para solicitar el turno
    )

# Guardar en la base de datos
    db.add(nueva_persona)
    db.commit()
    db.refresh(nueva_persona)
    return nueva_persona


# POST /turnos
# Endpoint para crear un nuevo turno para una persona existente
# Valida que la persona exista y cumple reglas de negocio

@app.post("/turnos/", response_model=models.models_Turnos, status_code=status.HTTP_201_CREATED)
def crear_turno(turno: TurnoCreate):
    # Validar que la persona exista en la base de datos
    persona = db.query(Persona).filter(Persona.id == turno.persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="La persona no existe")

    # Regla de negocio: no permitir si tiene 5 o más turnos cancelados en los últimos 6 meses
    seis_meses_atras = date.today().replace(month=max(1, date.today().month - 6))
    cancelados = (
        db.query(Turnos)
        .filter(Turnos.persona_id == turno.persona_id)
        .filter(Turnos.estado == "cancelado")
        .filter(Turnos.fecha >= seis_meses_atras)
        .count()
    )

    if cancelados >= 5:
        raise HTTPException(status_code=400, detail="La persona tiene demasiados turnos cancelados")

 # Crear nuevo turno con estado inicial "pendiente"
    nuevo_turno = Turnos(
        fecha=turno.fecha,
        hora=turno.hora,
        estado="pendiente",  # Siempre arranca en pendiente
        persona_id=turno.persona_id
    )

# Guardar el turno en la base de datos
    db.add(nuevo_turno)
    db.commit()
    db.refresh(nuevo_turno)
    return nuevo_turno