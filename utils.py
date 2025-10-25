
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from dateutil.relativedelta import relativedelta
import models
from datetime import date
from typing import List
from collections import defaultdict
from database import Persona,Turnos  
from config import MESES_DISPONIBLES, ESTADOS_DISPONIBLES   

def obtener_turnos_cancelados_por_mes_por_persona(db: Session, mesQ: int = None, anioQ: int = None):
    """
    Devuelve un diccionario con:
        - anio: año del último mes
        - mes: nombre del último mes
        - cantidad: total de turnos cancelados
        - turnos: lista de PersonaConTurnos, cada persona con sus turnos cancelados del último mes
    """
    hoy = datetime.today()
    if mesQ is None and anioQ is None:
        # Caso 1: nada pasado → último mes completo
        ultimo_mes = hoy - relativedelta(months=1)
        mes_num = ultimo_mes.month
        anio = ultimo_mes.year
    elif mesQ is not None and anioQ is None:
        # Caso 2: solo mes → usar año actual
        mes_num = mesQ
        anio = hoy.year
    elif mesQ is None and anioQ is not None:
        # Caso 3: solo año → usar diciembre del año pasado por parámetro
        mes_num = 12
        anio = anioQ
    else:
        # Caso 4: mes y año → usar exactamente los valores pasados
        mes_num = mesQ
        anio = anioQ

    # Traemos todas las personas con sus turnos
    personas_db = (
        db.query(Persona)
        .options(joinedload(Persona.turnos))
        .all()
    )

    resultado = []

    for persona in personas_db:
        # Filtramos solo los turnos cancelados del último mes "cancelado"
        estado_cancelado = ESTADOS_DISPONIBLES[1] if len(ESTADOS_DISPONIBLES) > 2 else "cancelado"
        print(estado_cancelado)
        turnos_cancelados = [
            models.TurnoInfoDni(
                id=t.id,
                fecha=t.fecha,
                hora=t.hora,
                estado=t.estado
            )
            for t in persona.turnos
            if t.estado == estado_cancelado and t.fecha.month == mes_num and t.fecha.year == anio
        ]

        if not turnos_cancelados:
            continue  # ignoramos personas sin turnos cancelados

        datos_persona = models.DatosPersona.model_validate(persona)

        resultado.append(
            models.PersonaConTurnos(
                persona=datos_persona,
                turnos=turnos_cancelados
            )
        )

    meses = MESES_DISPONIBLES 
    # [
    #     "enero", "febrero", "marzo", "abril", "mayo", "junio",
    #     "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    # ]

    return {
        "anio": anio,
        "mes": meses[mes_num - 1],
        "cantidad": sum(len(p.turnos) for p in resultado),
        "turnos": resultado
    }


def obtener_turnos_por_fecha_service(db: Session, fecha: date) -> List[models.PersonaConTurnos]:
    # Traemos todos los turnos con la persona relacionada para la fecha dada
    turnos_db = (
        db.query(Turnos)
        .options(joinedload(Turnos.persona))
        .filter(Turnos.fecha == fecha)
        .all()
    )

    # Agrupamos los turnos por persona
    personas_dict = {}

    for turno_db in turnos_db:
        persona_id = turno_db.persona.id

        if persona_id not in personas_dict:
            personas_dict[persona_id] = {
                "persona": models.DatosPersona.model_validate(turno_db.persona),
                "turnos": []
            }

        turno_info = models.TurnoInfoDni(
            id=turno_db.id,
            fecha=turno_db.fecha,
            hora=turno_db.hora,
            estado=turno_db.estado
        )

        personas_dict[persona_id]["turnos"].append(turno_info)

    # Convertimos el diccionario en lista para devolverlo
    resultado = [models.PersonaConTurnos(**datos) for datos in personas_dict.values()]

    return resultado