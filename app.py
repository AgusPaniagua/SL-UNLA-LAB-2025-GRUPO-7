from fastapi import FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session
from database import SessionLocal, Turnos, Persona
import models  # models.models_Turnos = modelo Pydantic

#Creacion de la instancia de FastApi
app = FastAPI()
#Creacion de la session de base de datos
db: Session = SessionLocal()

@app.get("/")
def doc():
    return "Hola,presentamos la Api en python del Grupo 7"
#Endpoints para turnos
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
        turno.estado = turno_actualizado.estado
        hubo_Cambios = True
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