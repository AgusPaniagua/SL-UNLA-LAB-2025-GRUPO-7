from datetime import date, time
from sqlalchemy.orm import Session
from database import Turnos

def _generar_slots() -> list[time]:
    # Genera slots de 09:00 a 16:30 cada 30 minutos
    slots = []
    h, m = 9, 0
    while True:
        slots.append(time(hour=h, minute=m))
        if h == 16 and m == 30:
            break
        m = 30 if m == 0 else 0
        if m == 0:
            h += 1
    return slots

def calcular_turnos_disponibles(db: Session, fecha: date) -> list[str]:
    #Devuelve los horarios disponibles  para la fecha dada.
    ocupados = (
        db.query(Turnos)
          .filter(Turnos.fecha == fecha, Turnos.estado.in_(["cancelado", "confirmado", "asistido"]))
          .all()
    )
    ocupados_set = {(t.hora.hour, t.hora.minute) for t in ocupados}

    slots = _generar_slots()
    libres = [s for s in slots if (s.hour, s.minute) not in ocupados_set]
    return [s.strftime("%H:%M") for s in libres]