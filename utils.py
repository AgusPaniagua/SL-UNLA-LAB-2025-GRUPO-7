
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from dateutil.relativedelta import relativedelta
import models
from database import Persona  # <- esto reemplaza models.Persona

def obtener_turnos_cancelados_por_mes_por_persona(db: Session):
    """
    Devuelve un diccionario con:
        - anio: año del último mes
        - mes: nombre del último mes
        - cantidad: total de turnos cancelados
        - turnos: lista de PersonaConTurnos, cada persona con sus turnos cancelados del último mes
    """
    hoy = datetime.today()
    ultimo_mes = hoy - relativedelta(months=1)
    mes_num = ultimo_mes.month
    anio = ultimo_mes.year

    # Traemos todas las personas con sus turnos
    personas_db = (
        db.query(Persona)
        .options(joinedload(Persona.turnos))
        .all()
    )

    resultado = []

    for persona in personas_db:
        # Filtramos solo los turnos cancelados del último mes
        turnos_cancelados = [
            models.TurnoInfoDni(
                id=t.id,
                fecha=t.fecha,
                hora=t.hora,
                estado=t.estado
            )
            for t in persona.turnos
            if t.estado == "cancelado" and t.fecha.month == mes_num and t.fecha.year == anio
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

    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]

    return {
        "anio": anio,
        "mes": meses[mes_num - 1],
        "cantidad": sum(len(p.turnos) for p in resultado),
        "turnos": resultado
    }