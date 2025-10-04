from datetime import date, time, datetime   
from sqlalchemy.orm import Session
from database import Turnos
from config import HORARIOS_DISPONIBLES, ESTADOS_DISPONIBLES


def calcular_turnos_disponibles(db: Session, fecha: date) -> list[str]:
    #Devuelve los horarios disponibles  para la fecha dada.
    ocupados = (
        db.query(Turnos)
          #.filter(Turnos.fecha == fecha, Turnos.estado.in_(["cancelado", "pendiente"]))
          .filter(Turnos.fecha == fecha, Turnos.estado != "cancelado")
          .all()
    )
    ocupados_set = {(t.hora.hour, t.hora.minute) for t in ocupados}

    #slots = _generar_slots()
    slots = [datetime.strptime(h, "%H:%M").time() for h in HORARIOS_DISPONIBLES]
    libres = [s for s in slots if (s.hour, s.minute) not in ocupados_set]
    return [s.strftime("%H:%M") for s in libres]