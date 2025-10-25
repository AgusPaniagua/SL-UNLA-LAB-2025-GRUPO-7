from fastapi import FastAPI, HTTPException, Response, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, func
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
import utils
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

@app.get("/reportes/turnos-por-fecha", response_model=list[models.PersonaConTurnos])
def obtener_turnos_por_fecha(fecha: date = Query(..., description="YYYY-MM-DD")):
    try:
        resultado = utils.obtener_turnos_por_fecha_service(db, fecha)

        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron turnos para la fecha {fecha}"
            )

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener turnos por fecha: {str(e)}"
        )


@app.get("/reportes/turnos-cancelados-por-mes", response_model=models.TurnosCanceladosPorMes)
def turnos_cancelados_ultimo_mes(mes: int = Query(None, ge=1, le=12, description="Número de mes (1-12)"),
    anio: int = Query(None, description="Año, por ejemplo 2025")):
    try: 
        if not mes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El parámetro 'mes' es obligatorio. Debe indicar un número de 1 a 12."
            )
        resultado = utils.obtener_turnos_cancelados_por_mes_por_persona(db, mesQ=mes, anioQ=anio)
        
        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener turnos cancelados por persona: {str(e)}"
        )
    
@app.patch("/turnos/{turno_id}", response_model=models.models_Turnos)
def actualizar_turno(turno_id: int, turno_actualizado: models.TurnoUpdate):
    turno = db.query(Turnos).filter(Turnos.id == turno_id).first()
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
    hubo_Cambios = False
    #Regla de negocio la cual indica que no se puede modificar un turno asistido o cancelado
    if turno.estado in ["asistido", "cancelado"]:
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"No se puede modificar un turno con estado '{turno.estado}'."
    )
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
    if turno.estado in ["asistido", "cancelado"]:
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"No se puede modificar un turno con estado '{turno.estado}'."
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

@app.put("/turnos/{turno_id}/confirmar", response_model=models.TurnoSalida)
def confirmar_turno(turno_id: int):
    turno = db.query(Turnos).filter(Turnos.id == turno_id).first()
    
    #Si el turno no se encuentra, da esta excepcion
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno no encontrado"
        )
    
    #Si el estado del turno está cancelado, no te deja confirmar el mismo
    if turno.estado == "cancelado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede confirmar un turno cancelado"
        )
    
    #Si el turno ya se encuentra confirmado, no se puede volver a confirmar
    if turno.estado == "confirmado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El turno ya está confirmado"
        )
    
    #Cambia el estado del turno y por ultimo te retorna el detalle del turno
    turno.estado = "confirmado"
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

def validar_email(email: str):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(patron, email):
        raise ValueError("Email inválido")
    return True

def validar_fecha_nacimiento(año, mes, dia):
    año_actual = date.today().year
    if año > año_actual:
        raise ValueError("El año no puede ser mayor al actual")
    try:
        fecha = date(año, mes, dia)
    except ValueError:
        raise ValueError("Fecha inválida")
    return fecha

# Endpoin para traer a todas las personas
@app.get("/personas/", response_model=list[models.DatosPersona])
def traer_personas():
    personas = db.query(Persona).all()
    return personas

@app.get("/personas/{persona_id}", response_model=models.DatosPersona)
def traer_personas(persona_id: int):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona no encontrada")
    return persona
    
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
@app.get("/reportes/turnos-por-personas/{dni}",response_model=list[models.PersonaConTurnos])
def traer_turnos_por_dni_de_persona(dni: int):
    try:
        persona_db = (
            db.query(Persona)
            .filter(Persona.dni == dni)
            .options(joinedload(Persona.turnos))
            .first()
        )

        if persona_db is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Persona no encontrada"
            )  

        turno_info = []
        
        for turno_db in persona_db.turnos:
            turno=models.TurnoInfoDni(
                id=turno_db.id,
                fecha=turno_db.fecha,
                hora=turno_db.hora,
                estado=turno_db.estado,
            )
            turno_info.append(turno)

        datos_persona=models.DatosPersona.model_validate(persona_db)

        lista_turnos=models.PersonaConTurnos(
            persona=datos_persona,
            turnos=turno_info
        )

        return [lista_turnos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar persona: {str(e)}")
    
#Endopoint para traer a las personas que tienen minimo 5 turnos cancelados, y el detalle de cada turno
@app.get(
    "/reportes/turnos-cancelados",
    response_model=list[models.ReportePersonasConTurnosCancelados]
)
def obtener_personas_con_turnos_cancelados(
    min: int = Query(5, ge=1, description="Cantidad mínima de turnos cancelados")
):
    # Buscar personas con al menos 'min' turnos cancelados
    resultados = (
        db.query(Persona, func.count(Turnos.id).label("cantidad_cancelados"))
        .join(Turnos, Persona.id == Turnos.persona_id)
        .filter(Turnos.estado == "cancelado")
        .group_by(Persona.id)
        .having(func.count(Turnos.id) >= min)
        .all()
    )

    if not resultados:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay personas con {min} o más turnos cancelados"
        )

    respuesta = []
    for persona, cantidad in resultados:
        # Obtener los turnos cancelados de esta persona
        turnos_detalle = (
            db.query(Turnos)
            .filter(Turnos.persona_id == persona.id, Turnos.estado == "cancelado")
            .all()
        )

        # Construir la estructura del reporte según el modelo
        respuesta.append(models.ReportePersonasConTurnosCancelados(
            persona=models.PersonaConTurnosCancelados(
                id=persona.id,
                nombre=persona.nombre,
                email=persona.email,
                dni=persona.dni,
                telefono=persona.telefono
            ),
            cantidad_cancelados=cantidad,
            turnos=[
                models.TurnoCanceladoDetalle(
                    id=t.id,
                    fecha=t.fecha,
                    hora=t.hora,
                    estado=t.estado
                ) for t in turnos_detalle
            ]
        ))

    return respuesta


#Endpoint para traer todas las personas mediante el parametro habilitado_para_turno
@app.get("/reportes/estado-personas/",response_model=list[models.DatosPersona])
def traer_personas_por_estado_de_turno(habilitado_para_turno: bool):
    try:
        personas=db.query(Persona).filter(Persona.habilitado_para_turno==habilitado_para_turno).all()
        return personas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

#Endpoint para traer los turnos confirmados en un período de tiempo
@app.get("/reportes/turnos-confirmados", response_model=models.ReporteTurnosConfirmados)
def turnos_confirmados(
    desde: date = Query(..., description="AAAA-MM-DD"),
    hasta: date = Query(..., description="AAAA-MM-DD"),
    pagina: int = Query(1, ge=1, description="Número de página (>=1)")
):
    if desde > hasta:
        raise HTTPException(status_code=400, detail="El parámetro 'desde' no puede ser mayor que 'hasta'.")

    POR_PAGINA = 5

    consulta_turnos_confirmados = (
        db.query(Turnos)
        .options(joinedload(Turnos.persona))
        .filter(Turnos.estado == "confirmado")
        .filter(Turnos.fecha >= desde)
        .filter(Turnos.fecha <= hasta)   
        .order_by(Turnos.fecha.asc(), Turnos.hora.asc(), Turnos.id.asc())
    )

    total = consulta_turnos_confirmados.count()
    total_paginas = (total + POR_PAGINA - 1) // POR_PAGINA if total > 0 else 0
    desplazamiento = (pagina - 1) * POR_PAGINA

    if total > 0 and pagina > total_paginas:
        elementos_pagina = []
    else:
        elementos_pagina = (
            consulta_turnos_confirmados
                .offset(desplazamiento)
                .limit(POR_PAGINA)
                .all()
        )


    return models.ReporteTurnosConfirmados(
        desde=desde,
        hasta=hasta,
        pagina=pagina,
        por_pagina=POR_PAGINA,
        total=total,
        total_paginas=total_paginas,
        resultados=elementos_pagina,  
    )