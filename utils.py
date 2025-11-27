import re
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import models
from typing import List
from collections import defaultdict
from database import Persona, Turnos  
from config import MESES_DISPONIBLES, ESTADOS_DISPONIBLES 
from fastapi import HTTPException, status
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.horizontal_rule import HorizontalRule
from borb.pdf.canvas.color.color import HexColor
from borb.pdf.canvas.layout.table.table import Table, TableCell
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable


def obtener_turnos_cancelados_por_mes_por_persona(db: Session, mesQ: int = None, anioQ: int = None):
    hoy = datetime.today()
    if mesQ is None and anioQ is None:
        ultimo_mes = hoy - relativedelta(months=1)
        mes_num = ultimo_mes.month
        anio = ultimo_mes.year
    elif mesQ is not None and anioQ is None:
        mes_num = mesQ
        anio = hoy.year
    elif mesQ is None and anioQ is not None:
        mes_num = 12
        anio = anioQ
    else:
        mes_num = mesQ
        anio = anioQ

    personas_db = db.query(Persona).options(joinedload(Persona.turnos)).all()
    resultado = []

    for persona in personas_db:
        estado_cancelado = ESTADOS_DISPONIBLES[1] if len(ESTADOS_DISPONIBLES) > 2 else "cancelado"
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
            continue

        datos_persona = models.DatosPersona.model_validate(persona)
        resultado.append(
            models.PersonaConTurnos(
                persona=datos_persona,
                turnos=turnos_cancelados
            )
        )

    meses = MESES_DISPONIBLES 

    return {
        "anio": anio,
        "mes": meses[mes_num - 1],
        "cantidad": sum(len(p.turnos) for p in resultado),
        "turnos": resultado
    }


def obtener_turnos_por_fecha_service(db: Session, fecha: date) -> List[models.PersonaConTurnos]:
    turnos_db = db.query(Turnos).options(joinedload(Turnos.persona)).filter(Turnos.fecha == fecha).all()
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

    resultado = [models.PersonaConTurnos(**datos) for datos in personas_dict.values()]
    return resultado


def actualizar_campos_dinamicos(obj_db, obj_update, estados_validos=None):
    hubo_cambios = False
    for campo, valor in obj_update.dict(exclude_unset=True).items():
        if campo == "estado" and estados_validos is not None:
            if valor not in estados_validos:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Estado inválido. Debe ser: {', '.join(estados_validos)}."
                )
        setattr(obj_db, campo, valor)
        hubo_cambios = True
    return hubo_cambios


def traer_personas_por_estado_de_turno(db: Session, habilitado_para_turno: bool):
    try:
        personas = db.query(Persona).filter(Persona.habilitado_para_turno == habilitado_para_turno).all()
        return personas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    

def traer_turnos_por_dni_de_persona(db: Session, dni: int):
    try:
        persona_db = (
            db.query(Persona)
            .filter(Persona.dni == dni)
            .options(joinedload(Persona.turnos))
            .first()
        )
        if persona_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona no encontrada")  

        turno_info = []
        for turno_db in persona_db.turnos:
            turno = models.TurnoInfoDni(
                id=turno_db.id,
                fecha=turno_db.fecha,
                hora=turno_db.hora,
                estado=turno_db.estado,
            )
            turno_info.append(turno)

        datos_persona = models.DatosPersona.model_validate(persona_db)
        lista_turnos = models.PersonaConTurnos(persona=datos_persona, turnos=turno_info)
        return [lista_turnos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar persona: {str(e)}")


def agregar_titulo(layout, texto):
    layout.add(
        Paragraph(
            texto,
            font_size=20,
            font_color=HexColor("#000000"),
            font="Helvetica-Bold",
            margin_bottom=2,
        )
    )
    layout.add(
        HorizontalRule(
            line_color=HexColor("#000000"),
            margin_top=5,
            margin_bottom=10,
        )
    )


def agregar_tabla(numero_filas: int, numero_columnas: int, tamaño_columnas: list):
    tabla = FixedColumnWidthTable(
        number_of_rows=numero_filas + 1,
        number_of_columns=numero_columnas,
        column_widths=tamaño_columnas
    )
    tabla.set_padding_on_all_cells(5, 5, 5, 5)
    tabla.set_border_color_on_all_cells(HexColor("#CCCCCC"))
    return tabla


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
