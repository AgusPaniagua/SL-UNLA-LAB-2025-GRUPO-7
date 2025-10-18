from fastapi import FastAPI, HTTPException, Response, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract
from database import SessionLocal, Turnos, Persona
import models  # models.models_Turnos = modelo Pydantic
from models import TurnoCreate, PersonaCreate
from datetime import date
from typing import Optional
import re, calendar
from pydantic import BaseModel
from datetime import date, datetime 
from dateutil.relativedelta import relativedelta
from turnosdisponibles import calcular_turnos_disponibles
from config import HORARIOS_DISPONIBLES, ESTADOS_DISPONIBLES
ESTADOS_VALIDOS = ESTADOS_DISPONIBLES
print("Verificamos desde var_entornos Horarios disponibles:", HORARIOS_DISPONIBLES)
print("Verificamos desde var_entornos Estados disponibles:", ESTADOS_DISPONIBLES)

# Creacion de la instancia de FastApi
app = FastAPI()
# Creacion de la session de base de datos
db: Session = SessionLocal()


@app.get("/")
def doc():
    return "Hola,presentamos la Api en python del Grupo 7"

# Endpoints para turnos


@app.get("/turnos/", response_model=list[models.models_Turnos])
def leer_turnos():
    turnos = db.query(Turnos).all()
    return turnos


@app.get("/turno/{turno_id}", response_model=models.models_Turnos)
def leer_turno(turno_id: int):
    turno = db.query(Turnos).filter(Turnos.id == turno_id).first()
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
    return turno

@app.get("/reportes/turnos-por-fecha", response_model=list[models.TurnoConPersonaPorFecha])
def obtener_turnos_por_fecha(fecha: date = Query(..., description="YYYY-MM-DD")):
    turnos = (
        db.query(Turnos)
        .filter(Turnos.fecha == fecha)
        .options(joinedload(Turnos.persona))  
        .all()
    )
    #if not turnos:
    #    raise HTTPException(status_code=404, detail="No hay turnos para la fecha especificada")
    return turnos

@app.get("/reportes/turnos-cancelados-por-mes", response_model=models.TurnosCanceladosPorMes)
def turnos_cancelados_ultimo_mes():
    hoy = datetime.today()
    ultimo_mes = hoy - relativedelta(months=1)
    mes = ultimo_mes.month
    anio = ultimo_mes.year

    turnos_cancelados = (
        db.query(Turnos)
        .filter(Turnos.estado == "cancelado")
        .filter(extract('month', Turnos.fecha) == mes)
        .filter(extract('year', Turnos.fecha) == anio)
        .all()
    )

    lista_turnos = [
        models.TurnoCanceladoInfo(
            id=t.id,
            persona_id=t.persona_id,
            fecha=t.fecha,
            hora=t.hora,
            estado=t.estado
        )
        for t in turnos_cancelados
    ]

    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]

    return models.TurnosCanceladosPorMes(
        anio=anio,
        mes=meses[mes - 1],
        cantidad=len(lista_turnos),
        turnos=lista_turnos
    )

@app.patch("/turnos/{turno_id}", response_model=models.models_Turnos)
def actualizar_turno(turno_id: int, turno_actualizado: models.TurnoUpdate):
    turno = db.query(Turnos).filter(Turnos.id == turno_id).first()
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
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
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail= f"Estado inválido. Debe ser: {', '.join(ESTADOS_VALIDOS)}.")
    if turno_actualizado.persona_id is not None:
        turno.persona_id = turno_actualizado.persona_id
        hubo_Cambios = True

    if hubo_Cambios == False:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    db.commit()
    db.refresh(turno)
    return turno

@app.put("/turnos/{turno_id}", response_model=models.models_Turnos)
def actualizar_turno_put(turno_id: int, turno_actualizado: models.models_Turnos):
    turno = db.query(Turnos).filter(Turnos.id == turno_id).first()
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado"
        )
    if turno_actualizado.estado not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= f"Estado inválido. Debe ser: {', '.join(ESTADOS_VALIDOS)}.")
    
    turno.fecha = turno_actualizado.fecha
    turno.hora = turno_actualizado.hora
    turno.estado = turno_actualizado.estado
    turno.persona_id = turno_actualizado.persona_id

    db.commit()
    db.refresh(turno)
    return turno

@app.put("/turnos/{turno_id}/cancelar", response_model=models.TurnoSalida)
def cancelar_turno(turno_id: int):
    turno = (
        db.query(Turnos)
        .options(joinedload(Turnos.persona))  
        .filter(Turnos.id == turno_id)
        .first()
    )
    if turno is None:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    #Regla de negocio: No se puede cancelar un turno asistido 
    if turno.estado == "asistido":
        raise HTTPException(status_code=409, detail="No se puede cancelar un turno asistido.")
    if turno.estado == "cancelado":
        raise HTTPException(status_code=409, detail="El turno ya está cancelado.")

    turno.estado = "cancelado"
    db.add(turno)
    db.commit()
    db.refresh(turno)
    return turno

@app.post("/turnos/", response_model=models.models_Turnos, status_code=status.HTTP_201_CREATED)
def crear_turno(turno: TurnoCreate):
    # Validar que la persona exista en la base de datos
    persona = db.query(Persona).filter(Persona.id == turno.persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="La persona no existe")

    hora_str = turno.hora.strftime("%H:%M")

    # Evitar que otro turno esté en la misma fecha y hora y que si existe, tire la Exception correcta
    turno_existente = db.query(Turnos).filter(
        Turnos.fecha == turno.fecha,
        Turnos.hora == turno.hora,
        Turnos.estado != "cancelado"
    ).first()
    if turno_existente:
        raise HTTPException(
            status_code=400,
            detail=f"El horario {hora_str} ya está ocupado por otro turno"
        )

    # Verificar que la hora esté dentro de los slots disponibles, y si no lo está, tire la Exception
    turnos_disponibles = calcular_turnos_disponibles(db, turno.fecha)
    if hora_str not in turnos_disponibles:
        raise HTTPException(
            status_code=400,
            detail=f"La hora {hora_str} no está disponible para la fecha {turno.fecha}",
        )

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
        raise HTTPException(
            status_code=400, detail="La persona tiene demasiados turnos cancelados")

    # Crear nuevo turno con estado inicial "pendiente"
    nuevo_turno = Turnos(
        fecha=turno.fecha,
        hora=turno.hora,
        estado="pendiente",
        persona_id=turno.persona_id
    )

    # Guardar el turno en la base de datos
    db.add(nuevo_turno)
    db.commit()
    db.refresh(nuevo_turno)
    return nuevo_turno


@app.delete("/turno/{turno_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_turno(turno_id: int):
    turno = db.query(Turnos).filter(Turnos.id == turno_id).first()
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
    # Regla de negocio: No se pueden eliminar turnos asistidos
    if turno.estado == "asistido":
        raise HTTPException(status_code=409, detail="No se puede eliminar un turno asistido.")
    db.delete(turno)
    db.commit()
    return


@app.get("/turnos-disponibles")
def turnos_disponibles(fecha: date = Query(..., description="YYYY-MM-DD")):
    horarios = calcular_turnos_disponibles(db, fecha)
    return {
        "fecha": fecha.isoformat(),
        "horarios_disponibles": horarios,
    }

# Funcion para validar email


def validar_email(email: str):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(patron, email):
        raise ValueError("Email inválido")
    return True

# Funcion para validar fecha de nacimiento


def validar_fecha_nacimiento(año, mes, dia):
    año_actual = date.today().year
    if año > año_actual:
        raise ValueError("El año no puede ser mayor al actual")
    try:
        fecha = date(año, mes, dia)
    except ValueError:
        raise ValueError("Fecha inválida")
    return fecha


# Endpoints para personas

# Endpoin para traer a todas las personas
@app.get("/personas/", response_model=list[models.DatosPersona])
def traer_personas():
    personas = db.query(Persona).all()
    return personas

# Endpoin para traer a una persona por su id

@app.get("/personas/{persona_id}", response_model=models.DatosPersona)
def traer_personas(persona_id: int):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona no encontrada")
    return persona
    

# Endpoin para modificar una persona


@app.put("/personas/{persona_id}", response_model=models.DatosPersona)
def modificar_persona(persona_id: int, persona_modificada: models.PersonaBase):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if (persona is None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona no encontrada")
    if not (persona_modificada.nombre.strip()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="El nombre no puede estar vacío")
    persona.nombre = persona_modificada.nombre
    if not (persona_modificada.email.strip()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="El email no puede estar vacío")
    try:
        validar_email(persona_modificada.email)
        persona.email = persona_modificada.email
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not (persona_modificada.telefono.strip()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="El telefono no puede estar vacío")
    persona.telefono = persona_modificada.telefono
    if (persona_modificada.dni <= 0):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="El dni no puede ser 0 o negativo")
    try:
        fecha = persona_modificada.fecha_de_nacimiento
        validar_fecha_nacimiento(fecha.year, fecha.month, fecha.day)
        persona.fecha_de_nacimiento = fecha
    except ValueError as e:
        raise HTTPException(
            status_code=422, detail=f"Fecha de nacimiento inválida: {str(e)}")
    persona.habilitado_para_turno = persona_modificada.habilitado_para_turno
    db.commit()
    db.refresh(persona)
    return persona

# Endpoin para crear una persona


@app.post("/personas/", response_model=models.PersonaBase, status_code=status.HTTP_201_CREATED)
def crear_persona(persona: models.PersonaCreate):
    try:
        # Validaciones básicas
        if not persona.nombre.strip():
            raise HTTPException(status_code=422, detail="El nombre no puede estar vacío")
        if not persona.email.strip():
            raise HTTPException(status_code=422, detail="El email no puede estar vacío")
        if persona.dni <= 0:
            raise HTTPException(status_code=422, detail="El DNI no puede ser 0 o negativo")
        if not persona.telefono.strip():
            raise HTTPException(status_code=422, detail="El teléfono no puede estar vacío")
        if persona.fecha_de_nacimiento > date.today():
            raise HTTPException(status_code=422, detail="La fecha de nacimiento no puede ser futura")
        
        # Validar formato de email
        try:
            validar_email(persona.email)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        
        # Verificar si ya existe persona con mismo DNI o email
        existe = db.query(Persona).filter(
            (Persona.dni == persona.dni) | (Persona.email == persona.email)
        ).first()
        if existe:
            raise HTTPException(status_code=400, detail="Ya existe una persona con ese DNI o email")
        
        # Calcular edad (opcional, si lo necesitas en la respuesta)
        hoy = date.today()
        edad = hoy.year - persona.fecha_de_nacimiento.year - (
            (hoy.month, hoy.day) < (persona.fecha_de_nacimiento.month, persona.fecha_de_nacimiento.day)
        )
        
        # Crear la persona
        nueva_persona = Persona(
            nombre=persona.nombre,
            email=persona.email,
            dni=persona.dni,
            telefono=persona.telefono,
            fecha_de_nacimiento=persona.fecha_de_nacimiento,
            edad=edad,
            habilitado_para_turno=True  # siempre habilitado al crear
        )
        
        db.add(nueva_persona)
        db.commit()
        db.refresh(nueva_persona)
        
        return nueva_persona

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear persona: {str(e)}")

# Endpoint para eliminar un persona
@app.delete("/personas/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_persona(persona_id: int):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if (persona is None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona no encontrada")
    db.delete(persona)
    db.commit()
    return

#Endopoint para traer todos los turnos de una persona mediante el dni 
@app.get("/reportes/turnos-por-personas/{dni}",response_model=list[models.models_Turnos])
def traer_turnos_por_dni_de_persona(dni: int):
    try:
        persona=db.query(Persona).filter(Persona.dni==dni).first()
        if (persona is None):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Persona no encontrada")
        turnos=db.query(Turnos).join(Persona, Turnos.persona_id==Persona.id).filter(Persona.dni==dni).all()
        return turnos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar persona: {str(e)}")


#Endpoint para traer todas las personas mediante el parametro habilitado_para_turno
@app.get("/reportes/estado-personas/",response_model=list[models.DatosPersona])
def traer_personas_por_estado_de_turno(habilitado_para_turno: bool):
    try:
        personas=db.query(Persona).filter(Persona.habilitado_para_turno==habilitado_para_turno).all()
        return personas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")