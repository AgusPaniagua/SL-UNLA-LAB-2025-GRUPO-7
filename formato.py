from datetime import time, datetime


def formatear_hora(h):
    ##Devuelve la hora en formato HH:MM
    if isinstance(h, (time, datetime)):
        return h.strftime("%H:%M")
    return str(h)[:5]


def clave_orden_turno_por_persona(turno):
    
    #Orden para un turno: persona_id, hora, id del turno.
    
    persona_id = getattr(turno, "persona_id", None)

    if persona_id is None:
        # Si el turno no tiene persona asociada, lo mando al final
        return (float("inf"), turno.hora, turno.id)

    return (persona_id, turno.hora, turno.id)
