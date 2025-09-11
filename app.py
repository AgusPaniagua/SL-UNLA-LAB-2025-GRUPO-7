from fastapi import FastAPI
from sqlalchemy.orm import Session
from database import SessionLocal, Turnos, Persona
import models  # models.models_Turnos = modelo Pydantic

#Creacion de la instancia de FastApi
app = FastAPI()

#Creacion de la session de base de datos
db: Session = SessionLocal()

#Endpoints para turnos
@app.get("/")
def doc():
    return "Hola prueba Api python Grupo 7"

@app.get("/turnos/", response_model=list[models.models_Turnos])
def leer_turnos():
    turnos = db.query(Turnos).all()
    return turnos

#Endpoints para personas

@app.get("/personas/", response_model=list[models.DatosPersona])
def traer_personas():
    personas = db.query(Persona).all()
    return personas