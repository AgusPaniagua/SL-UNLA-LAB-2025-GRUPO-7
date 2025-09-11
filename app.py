from fastapi import FastAPI
from sqlalchemy.orm import Session
from database import SessionLocal, Turnos 
import models  # models.models_Turnos = modelo Pydantic

app = FastAPI()

db: Session = SessionLocal()

@app.get("/")
def doc():
    return "Hola prueba Api python Grupo 7"

@app.get("/turnos/", response_model=list[models.models_Turnos])
def leer_turnos():
    turnos = db.query(Turnos).all()
    return turnos