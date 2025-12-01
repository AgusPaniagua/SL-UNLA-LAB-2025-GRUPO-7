import io
import pandas as pd
import csv
from decimal import Decimal
from pathlib import Path
from fastapi import HTTPException, status
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, time
from sqlalchemy.orm import Session

import utils
import database

from borb.pdf import Document, Page, PDF, Image, Alignment
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.layout.table.table import TableCell
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.color.color import HexColor
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable


def generar_pdf_turnos_cancelados(db: Session, data: dict = None):
    """
    Genera un PDF con los turnos cancelados según la estructura JSON que pasaste.
    Devuelve un BytesIO listo para enviar como StreamingResponse en FastAPI.
    """
    try:
        if data is None:
            hoy = datetime.now()
            mes = hoy.month
            anio = hoy.year
            data = utils.obtener_turnos_cancelados_por_mes_por_persona(db, mesQ=mes, anioQ=anio)
        
        if not data["turnos"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron turnos cancelados para el período solicitado."
            )
        
        doc = Document()
        page = Page()
        doc.add_page(page)
        layout = SingleColumnLayout(page)

        # Títulos existentes    
        layout.add(Paragraph(f"Materia: Seminario Python", font_size=26, font_color=HexColor("003366"), font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(f"Alumno: Maximiliano F. Anabalon", font_size=20, font_color=HexColor("003366"), font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(" "))
        layout.add(Paragraph(f"Reporte de Turnos Cancelados - {data['mes'].capitalize()} {data['anio']}", font_size=18, horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(f"Cantidad total de turnos cancelados: {data['cantidad']}", font_size=14, horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(" "))  
        layout.add(Paragraph(" "))

        ruta_actual = Path(__file__).parent
        ruta_img = ruta_actual / "img" / "img_reporte.jpg"
        layout.add(
            Image(
                ruta_img,            
                width=Decimal(400),      
                height=Decimal(300),     
                horizontal_alignment=Alignment.CENTERED
            )
        )

        page2 = Page()
        doc.add_page(page2)
        layout2 = SingleColumnLayout(page2)
        layout2.add(Paragraph(" "))

        for persona_data in data["turnos"]: 
            persona = persona_data.persona  
            layout2.add(Paragraph(f"NOMBRE: {persona.nombre}", font="Helvetica-Bold", font_size=14, font_color=HexColor("0D1366"), horizontal_alignment=Alignment.CENTERED))
            layout2.add(Paragraph(f"DNI: {persona.dni} - EMAIL {persona.email} - TELEFONO: {persona.telefono}", font="Helvetica", font_size=12, font_color=HexColor("0D1366"), horizontal_alignment=Alignment.CENTERED))

            if puede_sacar_turno(db, persona.id):
                layout2.add(Paragraph(f"Habilitado para turno: SI", font_size=12, font_color=HexColor("52D93D"), horizontal_alignment=Alignment.CENTERED))    
            else:
                layout2.add(Paragraph(f"Habilitado para turno: NO", font_size=12, font_color=HexColor("D90909"), horizontal_alignment=Alignment.CENTERED))    

            encabezados = ["Turno ID", "Fecha", "Hora", "Estado", "Persona ID"]
            tamaño_de_columnas = [
                Decimal("0.20"),
                Decimal("0.35"),
                Decimal("0.35"),
                Decimal("0.35"),
                Decimal("0.35")
            ]

            # Crear tabla con la cantidad de filas necesarias
            tabla = utils.agregar_tabla(
                len(persona_data.turnos),
                len(encabezados),
                tamaño_de_columnas
            )

            # Agregar encabezados
            for encabezado in encabezados:
                tabla.add(
                    TableCell(
                        Paragraph(encabezado, font="Helvetica-Bold", font_color=HexColor("003366"))
                    )
                )

            # Agregar los turnos de la persona
            for turno in persona_data.turnos:
                hora_formateada = (
                    turno.hora.strftime("%H:%M")
                    if hasattr(turno.hora, "strftime")
                    else str(turno.hora)[0:5]
                )
                datos_turno = [turno.id, turno.fecha, hora_formateada, turno.estado, persona.id]
                for dato in datos_turno:
                    tabla.add(TableCell(Paragraph(str(dato))))

            layout2.add(tabla)
            layout2.add(Paragraph(" "))

        pdf_bytes = io.BytesIO()
        PDF.dumps(pdf_bytes, doc)
        pdf_bytes.seek(0)
        nombre_archivo = f"turnos_cancelados_{anio}_{mes:02d}.pdf"
        return pdf_bytes, nombre_archivo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF de turnos cancelados por persona: {str(e)}")

def generar_pdf_turnos_por_fecha_agrupado(db: Session, fecha: date):
    try:
        data = utils.obtener_turnos_por_fecha_service(db, fecha)
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron turnos para la fecha {fecha}."
            )
        doc = Document()

        # ===================== PÁGINA 1 =====================
        page = Page()
        doc.add_page(page)
        layout = SingleColumnLayout(page)

        # Contar todos los turnos
        cantidad_turnos = sum(len(p.turnos) for p in data)
        # Encabezado
        layout.add(Paragraph("Materia: Seminario Python", font_size=26, font_color=HexColor("003366"),
                             font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph("Alumno: Maximiliano F. Anabalon", font_size=20, font_color=HexColor("003366"),
                             font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(" "))
        layout.add(Paragraph(f"Reporte de Turnos por Fecha - {fecha.strftime('%d/%m/%Y')}",
                             font_size=18, horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(f"Cantidad total de turnos: {cantidad_turnos}",
                     font_size=14, horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(f"Cantidad total de personas con turnos: {len(data)}",
                             font_size=14, horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(" "))
        layout.add(Paragraph(" "))

        # Imagen portada
        ruta_actual = Path(__file__).parent
        ruta_img = ruta_actual / "img" / "img_reporte.jpg"
        if ruta_img.exists():
            layout.add(Image(ruta_img, width=Decimal(400), height=Decimal(300),
                             horizontal_alignment=Alignment.CENTERED))

        # ===================== PÁGINA 2 – TABLAS AGRUPADAS =====================
        page2 = Page()
        doc.add_page(page2)
        layout2 = SingleColumnLayout(page2)
        layout2.add(Paragraph(" "))

        # ---------------------------------------------------
        # TABLA GLOBAL DE TURNOS
        # ---------------------------------------------------
        layout2.add(Paragraph("Turnos",
                              font="Helvetica-Bold", font_size=16,
                              font_color=HexColor("003366"),
                              horizontal_alignment=Alignment.CENTERED))
        layout2.add(Paragraph(" "))

        # Obtener todos los turnos
        todos_los_turnos = []
        for p in data:
            for t in p.turnos:
                hora_format = (
                    t.hora[:5] if isinstance(t.hora, str)
                    else t.hora.strftime("%H:%M")
                )
                todos_los_turnos.append({
                    "id": t.id,
                    "fecha": t.fecha,
                    "hora": hora_format,
                    "estado": t.estado,
                    "persona_id": p.persona.id
                })

        # Ordenados por ID
        todos_los_turnos.sort(key=lambda x: x["id"])

        # Encabezados tabla turnos
        encabezados_turnos = ["Turno ID", "Fecha", "Hora", "Estado", "Persona ID"]
        tabla_turnos = utils.agregar_tabla(
            len(todos_los_turnos),
            len(encabezados_turnos),
            [Decimal("0.25"), Decimal("0.35"), Decimal("0.35"), Decimal("0.35"), Decimal("0.35")]
        )

        # Encabezados
        for h in encabezados_turnos:
            tabla_turnos.add(TableCell(Paragraph(h, font="Helvetica-Bold", font_color=HexColor("003366"))))

        # Filas
        for t in todos_los_turnos:
            for campo in [t["id"], t["fecha"], t["hora"], t["estado"], t["persona_id"]]:
                tabla_turnos.add(TableCell(Paragraph(str(campo))))

        layout2.add(tabla_turnos)
        layout2.add(Paragraph(" "))

        # ---------------------------------------------------
        # TABLA GLOBAL DE PERSONAS
        # ---------------------------------------------------
        layout2.add(Paragraph("Personas",
                              font="Helvetica-Bold", font_size=16,
                              font_color=HexColor("003366"),
                              horizontal_alignment=Alignment.CENTERED))
        layout2.add(Paragraph(" "))

        lista_personas = [p.persona for p in data]
        lista_personas.sort(key=lambda x: x.id)

        encabezados_personas = ["Persona ID", "Nombre", "DNI", "Email", "Teléfono"]

        tabla_personas = utils.agregar_tabla(
            len(lista_personas),
            len(encabezados_personas),
            [Decimal("0.20"), Decimal("0.40"), Decimal("0.30"), Decimal("0.55"), Decimal("0.40")]
        )

        # Encabezados
        for h in encabezados_personas:
            tabla_personas.add(TableCell(Paragraph(h, font="Helvetica-Bold", font_color=HexColor("003366"))))

        # Filas
        for persona in lista_personas:
            fila = [
                persona.id,
                persona.nombre,
                persona.dni,
                persona.email,
                persona.telefono
            ]
            for campo in fila:
                tabla_personas.add(TableCell(Paragraph(str(campo))))

        layout2.add(tabla_personas)
        layout2.add(Paragraph(" "))

        pdf_bytes = io.BytesIO()
        PDF.dumps(pdf_bytes, doc)
        pdf_bytes.seek(0)
        return pdf_bytes

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener PDF turnos por fecha: {e}")


def generar_pdf_con_estado_de_personas(data: list):
    documento = Document()
    pagina = Page()
    documento.add_page(pagina)
    diseño = SingleColumnLayout(pagina)

    # Titulo
    utils.agregar_titulo(diseño, "Reporte de estado de personas")

    # Encabezados
    encabezados = ["ID", "Nombre", "Email", "Dni", "Telefono", "Edad", "Habilitado"]
    tamaño_de_columnas = [
        Decimal("0.08"),
        Decimal("0.20"),
        Decimal("0.45"),
        Decimal("0.25"),
        Decimal("0.25"),
        Decimal("0.15"),
        Decimal("0.25"),
    ]

    # Crear tabla
    tabla = utils.agregar_tabla(len(data), len(encabezados), tamaño_de_columnas)

    # Agregar encabezados
    for encabezado in encabezados:
        tabla.add(
            TableCell(
                Paragraph(encabezado, font="Helvetica-Bold", font_color=HexColor("003366")),
            )
        )

    # Agregar personas
    for persona in data:
        datos_persona = [
            persona.id,
            persona.nombre,
            persona.email,
            persona.dni,
            persona.telefono,
            persona.edad,
            persona.habilitado_para_turno,
        ]
        for dato in datos_persona:
            tabla.add(TableCell(Paragraph(str(dato))))

    tabla.set_padding_on_all_cells(5, 5, 5, 5)
    tabla.set_border_color_on_all_cells(HexColor("#CCCCCC"))
    diseño.add(tabla)

    buffer = io.BytesIO()
    PDF.dumps(buffer, documento)
    buffer.seek(0)
    return buffer


def generar_csv_con_estado_de_personas(data: list):
    personas = []
    for persona in data:
        datos_persona = {
            "ID": persona.id,
            "Nombre": persona.nombre,
            "Email": persona.email,
            "Dni": persona.dni,
            "Telefono": persona.telefono,
            "Edad": persona.edad,
            "Habilitado": persona.habilitado_para_turno,
        }
        personas.append(datos_persona)

    df = pd.DataFrame(personas)
    buffer_encabezado = io.StringIO()
    buffer_encabezado.write(f"Registro de estado de personas\n")
    buffer_encabezado.write(f"\n")
    df.to_csv(buffer_encabezado, index=False, encoding="utf-8")
    buffer_encabezado.seek(0)
    buffer = io.BytesIO(buffer_encabezado.getvalue().encode('utf-8'))
    buffer.seek(0)
    return buffer


def generar_pdf_con_turnos_por_dni(data: list):
    persona_con_turnos = data[0]
    persona = persona_con_turnos.persona
    lista_turnos = persona_con_turnos.turnos

    documento = Document()
    pagina = Page()
    documento.add_page(pagina)
    diseño = SingleColumnLayout(pagina)
    utils.agregar_titulo(diseño, "Reporte de turnos de una persona mediante su dni")

    encabezados_persona = ["ID", "Nombre", "Email", "Dni", "Telefono", "Edad", "Habilitado"]
    encabezados_turno = ["ID", "Fecha", "Hora", "Estado"]

    tamaño_de_columnas_persona = [
        Decimal("0.08"),
        Decimal("0.20"),
        Decimal("0.45"),
        Decimal("0.25"),
        Decimal("0.25"),
        Decimal("0.15"),
        Decimal("0.25"),
    ]
    tamaño_de_columnas_turno = [
        Decimal("0.20"),
        Decimal("0.20"),
        Decimal("0.20"),
        Decimal("0.20"),
    ]

    tabla_persona = utils.agregar_tabla(1, len(encabezados_persona), tamaño_de_columnas_persona)
    tabla_turno = utils.agregar_tabla(len(lista_turnos), len(encabezados_turno), tamaño_de_columnas_turno)

    for encabezado in encabezados_persona:
        tabla_persona.add(
            TableCell(
                Paragraph(encabezado, font="Helvetica-Bold", font_color=HexColor("003366")),
            )
        )

    datos_persona = [
        persona.id,
        persona.nombre,
        persona.email,
        persona.dni,
        persona.telefono,
        persona.edad,
        persona.habilitado_para_turno,
    ]

    for dato in datos_persona:
        tabla_persona.add(TableCell(Paragraph(str(dato))))

    utils.agregar_titulo(diseño, "Listado de Turnos")

    for encabezado in encabezados_turno:
        tabla_turno.add(
            TableCell(
                Paragraph(encabezado, font="Helvetica-Bold", font_color=HexColor("#003366"))
            )
        )

    for turno in lista_turnos:
        datos_turno = [turno.id, turno.fecha, turno.hora, turno.estado]
        for dato in datos_turno:
            tabla_turno.add(TableCell(Paragraph(str(dato))))

    tabla_persona.set_padding_on_all_cells(5, 5, 5, 5)
    tabla_persona.set_border_color_on_all_cells(HexColor("#CCCCCC"))
    diseño.add(tabla_persona)

    tabla_turno.set_padding_on_all_cells(5, 5, 5, 5)
    tabla_turno.set_border_color_on_all_cells(HexColor("#CCCCCC"))
    diseño.add(tabla_turno)

    buffer = io.BytesIO()
    PDF.dumps(buffer, documento)
    buffer.seek(0)
    return buffer


def generar_pdf_turnos_por_fecha(db: Session, fecha: date):
    try:
        data = utils.obtener_turnos_por_fecha_service(db, fecha)

        doc = Document()
        page = Page()
        doc.add_page(page)
        layout = SingleColumnLayout(page)

        # Encabezado
        layout.add(Paragraph("Materia: Seminario Python", font_size=26, font_color=HexColor("003366"),
                             font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph("Alumno: Maximiliano F. Anabalon", font_size=20, font_color=HexColor("003366"),
                             font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(" "))
        layout.add(Paragraph(f"Reporte de Turnos por Fecha - {fecha.strftime('%d/%m/%Y')}",
                             font_size=18, horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(f"Cantidad total de personas con turnos: {len(data)}",
                             font_size=14, horizontal_alignment=Alignment.CENTERED))
        layout.add(Paragraph(" "))
        layout.add(Paragraph(" "))

        # Imagen portada
        ruta_actual = Path(__file__).parent
        ruta_img = ruta_actual / "img" / "img_reporte.jpg"
        if ruta_img.exists():
            layout.add(Image(ruta_img, width=Decimal(400), height=Decimal(300),
                             horizontal_alignment=Alignment.CENTERED))

        # Página de detalle
        page2 = Page()
        doc.add_page(page2)
        layout2 = SingleColumnLayout(page2)
        layout2.add(Paragraph(" "))

        for persona_con_turnos in data:
            persona = persona_con_turnos.persona

            layout2.add(Paragraph(f"NOMBRE: {persona.nombre}",
                                  font="Helvetica-Bold", font_size=14,
                                  font_color=HexColor("0D1366"), horizontal_alignment=Alignment.CENTERED))
            layout2.add(Paragraph(
                f"DNI: {persona.dni} - EMAIL: {persona.email} - TELÉFONO: {persona.telefono}",
                font="Helvetica", font_size=12, font_color=HexColor("0D1366"),
                horizontal_alignment=Alignment.CENTERED
            ))

            if puede_sacar_turno(db, persona.id):
                layout2.add(Paragraph("Habilitado para turno: SI",
                                      font_size=12, font_color=HexColor("52D93D"),
                                      horizontal_alignment=Alignment.CENTERED))
            else:
                layout2.add(Paragraph("Habilitado para turno: NO",
                                      font_size=12, font_color=HexColor("D90909"),
                                      horizontal_alignment=Alignment.CENTERED))
            encabezados = ["Turno ID", "Fecha", "Hora", "Estado","Persona ID"]
            tamaño_de_columnas = [
                Decimal("0.20"),
                Decimal("0.35"),
                Decimal("0.35"),
                Decimal("0.35"),
                Decimal("0.35")
            ]

            # Crear tabla con la cantidad de filas necesarias
            tabla = utils.agregar_tabla(
                len(persona_con_turnos.turnos),   # filas (la función agrega +1 internamente)
                len(encabezados),           # columnas
                tamaño_de_columnas
            )

            # ------- AGREGAR ENCABEZADOS -------
            for encabezado in encabezados:
                tabla.add(
                    TableCell(
                        Paragraph(
                            encabezado,
                            font="Helvetica-Bold",
                            font_color=HexColor("003366")
                        )
                    )
                )

            # ------- AGREGAR LOS TURNOS DE LA PERSONA -------
            for turno in persona_con_turnos.turnos:
                # Formatear hora (tu formato original)
                hora_formateada = (
                    turno.hora.strftime("%H:%M")
                    if hasattr(turno.hora, "strftime")
                    else str(turno.hora)[0:5]
                )

                datos_turno = [
                    turno.id,
                    turno.fecha,
                    hora_formateada,
                    turno.estado,
                    persona.id
                ]

                for dato in datos_turno:
                    tabla.add(
                        TableCell(
                            Paragraph(str(dato))
                        )
                    )

            layout2.add(tabla)   
            layout2.add(Paragraph(" "))

            # Turnos
            # for turno in persona_con_turnos.turnos:
            #     # Manejo robusto de hora
            #     hora = turno.hora
            #     if isinstance(hora, time):
            #         hora_formateada = hora.strftime("%H:%M")
            #     else:
            #         hora_formateada = str(hora)[:5]

            #     layout2.add(Paragraph(
            #         f"ID: {turno.id}    Fecha: {turno.fecha}    Hora: {hora_formateada}    Estado: {turno.estado}",
            #         font_size=12, font="Times-Roman", font_color=HexColor("2F2CE6"),
            #         horizontal_alignment=Alignment.CENTERED
            #     ))

            # layout2.add(Paragraph("-" * 130, font_size=10, horizontal_alignment=Alignment.CENTERED))
            # layout2.add(Paragraph(" "))

        # Exportar PDF
        pdf_bytes = io.BytesIO()
        PDF.dumps(pdf_bytes, doc)
        pdf_bytes.seek(0)
        return pdf_bytes

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener PDF turnos por fecha: {e}")


def puede_sacar_turno(db: Session, persona_id: int, meses: int = 6, limite_cancelaciones: int = 5) -> bool:
    fecha_limite = datetime.combine(
        date.today() - relativedelta(months=meses),
        datetime.min.time()
    )
    cancelados = (
        db.query(database.Turnos)
        .filter(database.Turnos.persona_id == persona_id)
        .filter(database.Turnos.estado == "cancelado")
        .filter(database.Turnos.fecha >= fecha_limite)
        .count()
    )
    return cancelados < limite_cancelaciones


def generar_csv_turnos_cancelados(db):
    try:
        hoy = datetime.now()
        mes = hoy.month
        anio = hoy.year
        data = utils.obtener_turnos_cancelados_por_mes_por_persona(db, mesQ=mes, anioQ=anio)
        
        if not data["turnos"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron turnos cancelados para el período solicitado."
            )

        if not data["turnos"]:
            return None

        personas = []
        for persona_data in data["turnos"]:
            persona = persona_data.persona
            habilitado = "SI" if puede_sacar_turno(db, persona.id) else "NO"
            personas.append({
                "ID Persona": persona.id,
                "Nombre": persona.nombre,
                "DNI": persona.dni,
                "Email": persona.email,
                "Telefono": persona.telefono,
                "Habilitado": habilitado
            })
        df_personas = pd.DataFrame(personas)

        turnos = []
        for persona_data in data["turnos"]:
            for turno in persona_data.turnos:
                # hora_formateada = turno.hora.strftime("%H:%M") if isinstance(turno.hora, datetime) else turno.hora
                hora_formateada = (turno.hora.strftime("%H:%M") if isinstance(turno.hora, (datetime, time))
                                else str(turno.hora)[:5])
                turnos.append({
                    "ID Turno": turno.id,
                    "ID Persona": persona_data.persona.id,
                    "Fecha": turno.fecha,
                    "Hora": hora_formateada,
                    "Estado": turno.estado
                })
        df_turnos = pd.DataFrame(turnos)

        buffer = io.StringIO()
        df_personas.to_csv(buffer, index=False, sep=';')
        buffer.write("\n\n")
        df_turnos.to_csv(buffer, index=False, sep=';')
        buffer.seek(0)
        return io.BytesIO(buffer.getvalue().encode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener csv turnos cancelados:: {e}")


def generar_archivos_csv_turnos_cancelados(db):
    try:
        hoy = datetime.now()
        mes = hoy.month
        anio = hoy.year
        data = utils.obtener_turnos_cancelados_por_mes_por_persona(db, mesQ=mes, anioQ=anio)
        
        if not data["turnos"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron turnos cancelados para el período solicitado."
            )
        personas = []
        for persona_data in data["turnos"]:
            persona = persona_data.persona
            habilitado = "SI" if puede_sacar_turno(db, persona.id) else "NO"
            personas.append({
                "ID Persona": persona.id,
                "Nombre": persona.nombre,
                "DNI": persona.dni,
                "Email": persona.email,
                "Telefono": persona.telefono,
                "Habilitado": habilitado
            })
        df_personas = pd.DataFrame(personas)

        buffer_personas = io.BytesIO()
        df_personas.to_csv(buffer_personas, index=False, sep=';')
        buffer_personas.seek(0)

        turnos = []
        for persona_data in data["turnos"]:
            for turno in persona_data.turnos:
                # hora_formateada = (
                #     turno.hora.strftime("%H:%M")
                #     if isinstance(turno.hora, datetime)
                #     else turno.hora
                # )
                hora_formateada = (turno.hora.strftime("%H:%M") if isinstance(turno.hora, (datetime, time))
                                else str(turno.hora)[:5])
                turnos.append({
                    "ID Turno": turno.id,
                    "ID Persona": persona_data.persona.id,
                    "Fecha": turno.fecha,
                    "Hora": hora_formateada,
                    "Estado": turno.estado
                })
        df_turnos = pd.DataFrame(turnos)

        buffer_turnos = io.BytesIO()
        df_turnos.to_csv(buffer_turnos, index=False, sep=';')
        buffer_turnos.seek(0)

        return buffer_personas, buffer_turnos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener archivos csv en zip turnos cancelados:: {e}")

def generar_excel_turnos_cancelados(db):
    try:
        hoy = datetime.now()
        mes = hoy.month
        anio = hoy.year
        data = utils.obtener_turnos_cancelados_por_mes_por_persona(db, mesQ=mes, anioQ=anio)

        if not data["turnos"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron turnos cancelados para el período solicitado."
            )

        personas = []
        for persona_data in data["turnos"]:
            persona = persona_data.persona
            habilitado = "SI" if puede_sacar_turno(db, persona.id) else "NO"
            personas.append({
                "ID Persona": persona.id,
                "Nombre": persona.nombre,
                "DNI": persona.dni,
                "Email": persona.email,
                "Telefono": persona.telefono,
                "Habilitado": habilitado
            })
        df_personas = pd.DataFrame(personas)

        turnos = []
        for persona_data in data["turnos"]:
            for turno in persona_data.turnos:
                # hora_formateada = (
                #     turno.hora.strftime("%H:%M")
                #     if isinstance(turno.hora, datetime)
                #     else turno.hora
                # )
                hora_formateada = (turno.hora.strftime("%H:%M") if isinstance(turno.hora, (datetime, time))
                                else str(turno.hora)[:5])
                turnos.append({
                    "ID Turno": turno.id,
                    "ID Persona": persona_data.persona.id,
                    "Fecha": turno.fecha,
                    "Hora": hora_formateada,
                    "Estado": turno.estado
                })
        df_turnos = pd.DataFrame(turnos)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_personas.to_excel(writer, sheet_name='Personas', index=False)
            df_turnos.to_excel(writer, sheet_name='Turnos', index=False)
        buffer.seek(0)
        return buffer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener excel turnos cancelados: {e}")
    
# ----------- ULTIMOS REPORTES DE JUAN IGNACIO AMALFITANO -----------    

def generar_pdf_personas_con_5_cancelados(data: list, minimo: int):

    documento = Document()
    pagina = Page()
    documento.add_page(pagina)
    diseño = SingleColumnLayout(pagina)

    # Titulo y encabezado
    diseño.add(Paragraph("Materia: Seminario Python", font_size=22, font_color=HexColor("003366"), font="Helvetica-Bold"))
    diseño.add(Paragraph("Alumno: Amalfitano Juan Ignacio", font_size=20, font_color=HexColor("003366"), font="Helvetica-Bold"))
    diseño.add(Paragraph("DNI: 45.397.013", font_size=15, font_color=HexColor("003366"), font="Helvetica-Bold"))
    diseño.add(Paragraph(" "))
    diseño.add(Paragraph(f"Reporte: Personas con mínimo {minimo} turnos cancelados", font_size=18))
    diseño.add(Paragraph(f"Cantidad de personas encontradas: {len(data)}", font_size=12))
    diseño.add(Paragraph(" "))

    for item in data:
        p = item.persona

        # Aca se muestran los datos de la persona
        diseño.add(Paragraph(f"Persona: {p.nombre} (ID {p.id})", font="Helvetica-Bold", font_size=14, font_color=HexColor("0D1366")))
        diseño.add(Paragraph(f"DNI: {p.dni} - Email: {p.email} - Teléfono: {p.telefono}", font_size=12))
        diseño.add(Paragraph(f"Total de turnos cancelados: {item.cantidad_cancelados}", font_size=12))
        diseño.add(Paragraph(" "))

        encabezados = ["ID", "Fecha", "Hora", "Estado"]
        columnas = len(encabezados)

        tabla = FixedColumnWidthTable(
            number_of_rows=len(item.turnos) + 1,
            number_of_columns=columnas,
            column_widths=[
                Decimal("0.25"),
                Decimal("0.25"),
                Decimal("0.25"),
                Decimal("0.25"),
            ]
        )

        # Encabezados con ID - FECHA - HORA - ESTADO
        for e in encabezados:
            tabla.add(TableCell(Paragraph(e, font="Helvetica-Bold", font_color=HexColor("003366"))))

        # Aca está la tabla de los turnos cancelados
        for t in item.turnos:
            fila = [
                t.id,
                str(t.fecha),
                str(t.hora),
                t.estado
            ]
            for campo in fila:
                tabla.add(TableCell(Paragraph(str(campo))))

        # Aca estan todos los estilos
        tabla.set_padding_on_all_cells(5, 5, 5, 5)
        tabla.set_border_color_on_all_cells(HexColor("#CCCCCC"))
        diseño.add(tabla)

        diseño.add(Paragraph(" "))

    # Y por ultimo genera el archivo PDF
    buffer = io.BytesIO()
    PDF.dumps(buffer, documento)
    buffer.seek(0)
    return buffer

def generar_csv_personas_con_cancelados(data: list, minimo: int):
    try:
        # Si no hay datos, devolvemos un error de que no se encontraron personas
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron personas con al menos {minimo} turnos cancelados."
            )

        # ---- DETALLES DE LA PERSONA ----
        # Va recorriendo a cada persona
        personas = []
        for item in data:
            p = item.persona
            personas.append({
                "ID Persona": p.id,
                "Nombre": p.nombre,
                "DNI": p.dni,
                "Email": p.email,
                "Telefono": p.telefono,
                "Total Cancelados": item.cantidad_cancelados
            })

        # Convierte la lista, en una tabla con Pandas
        df_personas = pd.DataFrame(personas)

        # ---- DETALLE DE LOS TURNOS CANCELADOS ----
          # Va recorriendo cada turno de cada persona
        turnos = []
        for item in data:
            for t in item.turnos:
                hora_formateada = (
                    t.hora.strftime("%H:%M")
                    if isinstance(t.hora, (datetime, time))
                    else str(t.hora)[:5]
                )

                turnos.append({
                    "ID Turno": t.id,
                    "ID Persona": item.persona.id,
                    "Fecha": t.fecha,
                    "Hora": hora_formateada,
                    "Estado": t.estado,
                })

        # Convierte la lista, en una tabla con Pandas
        df_turnos = pd.DataFrame(turnos)

        # ---- ARMADO DEL CSV ----
        # Se crea el archivo, escribe la tabla de personas y la tabla de turnos
        buffer = io.StringIO()
        df_personas.to_csv(buffer, index=False, sep=';')
        buffer.write("\n\n")
        df_turnos.to_csv(buffer, index=False, sep=';')
        buffer.seek(0)
        # Deja el archivo CSV listo para descargarlo
        return io.BytesIO(buffer.getvalue().encode("utf-8"))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar CSV de personas con cancelados: {str(e)}"
        )

def generar_csv_turnos_por_persona(data: list):
    # Aca extrae a las personas y a los turnos
    try:
        persona_con_turnos = data[0]
        persona = persona_con_turnos.persona
        turnos = persona_con_turnos.turnos

        # ------- DATOS DE PERSONA -------
        persona_dict = [{
            "ID Persona": persona.id,
            "Nombre": persona.nombre,
            "Email": persona.email,
            "DNI": persona.dni,
            "Telefono": persona.telefono,
            "Edad": persona.edad,
            "Habilitado": "SI" if persona.habilitado_para_turno else "NO"
        }]

        # Convierte la lista, en una tabla con Pandas
        df_persona = pd.DataFrame(persona_dict)

        # ------- DETALLE DE TURNOS -------
        lista_turnos = []
        for turno in turnos:
            hora_formateada = turno.hora.strftime("%H:%M")

            lista_turnos.append({
                "ID Turno": turno.id,
                "Fecha": turno.fecha,
                "Hora": hora_formateada,
                "Estado": turno.estado
            })

        # Convierte la lista, en una tabla con Pandas
        df_turnos = pd.DataFrame(lista_turnos)

        buffer = io.StringIO()

        # Primero escribe los datos de la persona
        df_persona.to_csv(buffer, index=False, sep=";")
        buffer.write("\n\n")

        # Luego los datos de la tabla de turnos
        df_turnos.to_csv(buffer, index=False, sep=";")

        buffer.seek(0)

        # Deja el archivo CSV listo para descargarlo
        return io.BytesIO(buffer.getvalue().encode("utf-8"))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando CSV de turnos por persona: {str(e)}"
        )
    
def generar_pdf_turnos_confirmados(turnos, desde, hasta):
    from datetime import time, datetime
    def hhmm(h):
        return h.strftime("%H:%M") if isinstance(h, (time, datetime)) else str(h)[:5]
    # Agrupar turnos por persona
    por_persona = {}  
    for t in turnos:
        p = getattr(t, "persona", None)
        if p is None:
            continue
        if p.id not in por_persona:
            por_persona[p.id] = {"persona": p, "turnos": []}
        por_persona[p.id]["turnos"].append(t)

    doc = Document()

    # Portada / resumen
    page1 = Page()
    doc.add_page(page1)
    lay1 = SingleColumnLayout(page1)
    lay1.add(Paragraph(
        "Materia: Seminario de Lenguajes",
        font="Helvetica-Bold", font_size=16, font_color=HexColor("003366"),
        horizontal_alignment=Alignment.CENTERED
    ))
    lay1.add(Paragraph(
        "Alumno: Gomez Fernando",
        font="Helvetica-Bold", font_size=14, font_color=HexColor("003366"),
        horizontal_alignment=Alignment.CENTERED
    ))
    lay1.add(Paragraph(
        "DNI: 43.036.843",
        font="Helvetica-Bold", font_size=14, font_color=HexColor("003366"),
        horizontal_alignment=Alignment.CENTERED
    ))
    lay1.add(Paragraph(" "))  # espacio

    lay1.add(Paragraph(
        "Turnos confirmados",
        font="Helvetica-Bold", font_size=22, font_color=HexColor("003366"),
        horizontal_alignment=Alignment.CENTERED
    ))
    lay1.add(Paragraph(
        f"Período: {desde.isoformat()} a {hasta.isoformat()}",
        font_size=14, horizontal_alignment=Alignment.CENTERED
    ))
    lay1.add(Paragraph(
        f"Personas con turnos confirmados: {len(por_persona)}  |  Total de turnos: {len(turnos)}",
        font_size=11, horizontal_alignment=Alignment.CENTERED
    ))
    lay1.add(Paragraph(" "))

    
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)
    layout.add(Paragraph(" "))

    filas_en_pagina = 0
    LIMITE_FILAS = 18

    def _nueva_pagina():
        nonlocal page, layout, filas_en_pagina
        page = Page()
        doc.add_page(page)
        layout = SingleColumnLayout(page)
        layout.add(Paragraph(" "))
        filas_en_pagina = 0

    for _, paquete in sorted(por_persona.items(), key=lambda kv: kv[0]):
        persona = paquete["persona"]
        lista = paquete["turnos"]

        if filas_en_pagina >= LIMITE_FILAS:
            _nueva_pagina()

        layout.add(Paragraph(
            f"NOMBRE: {getattr(persona, 'nombre', '-')}",
            font="Helvetica-Bold", font_size=14, font_color=HexColor("0D1366"),
            horizontal_alignment=Alignment.CENTERED
        ))
        layout.add(Paragraph(
            f"DNI: {getattr(persona, 'dni', '-')}"
            f"  -  EMAIL: {getattr(persona, 'email', '-')}"
            f"  -  TELÉFONO: {getattr(persona, 'telefono', '-')}",
            font_size=11, font_color=HexColor("0D1366"),
            horizontal_alignment=Alignment.CENTERED
        ))

        fecha_nac = getattr(persona, "fecha_de_nacimiento", "")
        edad = getattr(persona, "edad", "")
        habilitado = "SI" if getattr(persona, "habilitado_para_turno", False) else "NO"
        layout.add(Paragraph(
            f"Fecha nac.: {fecha_nac}  |  Edad: {edad}  |  Habilitado: {habilitado}",
            font_size=10, horizontal_alignment=Alignment.CENTERED
        ))
        layout.add(Paragraph(" "))

        encabezados = ["Turno ID", "Fecha", "Hora", "Estado"]
        col_widths = [Decimal("0.20"), Decimal("0.35"), Decimal("0.35"), Decimal("0.35")]

        tabla = FixedColumnWidthTable(
            number_of_rows=len(lista) + 1,
            number_of_columns=len(encabezados),
            column_widths=col_widths
        )

        for h in encabezados:
            tabla.add(TableCell(
                Paragraph(h, font="Helvetica-Bold", font_color=HexColor("003366"))
            ))

        for t in lista:
            tabla.add(TableCell(Paragraph(str(t.id))))
            tabla.add(TableCell(Paragraph(t.fecha.isoformat())))
            tabla.add(TableCell(Paragraph(hhmm(t.hora))))  # <--- reemplazo
            tabla.add(TableCell(Paragraph(t.estado)))

        tabla.set_padding_on_all_cells(5, 5, 5, 5)
        tabla.set_border_color_on_all_cells(HexColor("#CCCCCC"))
        layout.add(tabla)
        layout.add(Paragraph(" "))

        filas_en_pagina += min(len(lista) + 4, LIMITE_FILAS)

    buf = io.BytesIO()
    PDF.dumps(buf, doc)
    buf.seek(0)
    nombre = f"turnos_confirmados_{desde.isoformat()}_{hasta.isoformat()}.pdf"
    return buf, nombre

def generar_csv_turnos_confirmados(turnos, desde, hasta):

    def hhmm(h):
        return h.strftime("%H:%M") if isinstance(h, (time, datetime)) else str(h)[:5]

    # Agrupar por persona
    por_persona = {}  
    for t in turnos:
        p = getattr(t, "persona", None)
        if p is None:
            continue
        if p.id not in por_persona:
            por_persona[p.id] = {"persona": p, "turnos": []}
        por_persona[p.id]["turnos"].append(t)

    
    out = io.StringIO()

    # Datos iniciales
    out.write("Reporte: Turnos confirmados\n")
    out.write(f"Periodo: {desde.isoformat()} a {hasta.isoformat()}\n")
    out.write(f"Total personas con turnos confirmados: {len(por_persona)}\n")
    out.write(f"Total turnos confirmados: {len(turnos)}\n\n")
    
    #Datos persona
    for _, paquete in sorted(por_persona.items(), key=lambda kv: kv[0]):
        p = paquete["persona"]
        lista = paquete["turnos"]

        persona_cols = [
            "persona_id", "nombre", "dni", "email", "telefono",
            "fecha_nacimiento", "edad", "habilitado", "total_turnos_confirmados"
        ]
        persona_vals = [
            getattr(p, "id", ""),
            getattr(p, "nombre", ""),
            getattr(p, "dni", ""),
            getattr(p, "email", ""),
            getattr(p, "telefono", ""),
            getattr(p, "fecha_de_nacimiento", "") or "",
            getattr(p, "edad", "") or "",
            "SI" if getattr(p, "habilitado_para_turno", False) else "NO",
            len(lista),
        ]

        # Fila de encabezado de persona
        out.write(";".join(persona_cols) + "\n")
        # Fila de datos de persona
        out.write(";".join(str(v) for v in persona_vals) + "\n")

        # Encabezado turnos
        out.write("turno_id;fecha;hora;estado\n")
        # Turnos
        for t in lista:
            out.write(f"{t.id};{t.fecha.isoformat()};{hhmm(t.hora)};{t.estado}\n")

        out.write("\n")

    data = out.getvalue().encode("utf-8-sig")
    out.close()
    nombre = f"turnos_confirmados_{desde.isoformat()}_{hasta.isoformat()}.csv"
    return io.BytesIO(data), nombre


def generar_csv_turnos_por_fecha(turnos, fecha):

    def hhmm(h):
        return h.strftime("%H:%M") if isinstance(h, (time, datetime)) else str(h)[:5]

    # Agrupar por persona 
    por_persona = {}  
    for t in sorted(turnos, key=lambda x: (getattr(x, "persona_id", 10**12), x.hora, x.id)):
        p = getattr(t, "persona", None)
        if p is None:
            continue
        if p.id not in por_persona:
            por_persona[p.id] = {"persona": p, "turnos": []}
        por_persona[p.id]["turnos"].append(t)

    total_turnos = sum(len(pkg["turnos"]) for pkg in por_persona.values())
    total_personas = len(por_persona)

    buf_txt = io.StringIO()
    w = csv.writer(buf_txt, delimiter=';', lineterminator='\n')

    # Datos iniciales
    w.writerow(["TOTAL_TURNOS", total_turnos])
    w.writerow(["TOTAL_PERSONAS_CON_TURNOS", total_personas])
    w.writerow([])  # línea en blanco
    w.writerow([f"TURNOS_POR_FECHA: {fecha.isoformat()}"])
    w.writerow([])

    # Datos Persona
    persona_header = [
        "persona_id", "nombre", "dni", "email", "telefono",
        "fecha_nacimiento", "edad", "habilitado", "total_turnos_persona"
    ]
    turnos_header = ["turno_id", "fecha", "hora", "estado"]

    for _, paquete in sorted(por_persona.items(), key=lambda kv: kv[0]):
        p = paquete["persona"]
        lista = paquete["turnos"]

        w.writerow(persona_header)
        w.writerow([
            getattr(p, "id", ""),
            getattr(p, "nombre", ""),
            getattr(p, "dni", ""),
            getattr(p, "email", ""),
            getattr(p, "telefono", ""),
            (getattr(p, "fecha_de_nacimiento", "") or ""),
            (getattr(p, "edad", "") or ""),
            "SI" if getattr(p, "habilitado_para_turno", False) else "NO",
            len(lista),
        ])
        w.writerow([])

        # Tabla de turnos de esa persona
        w.writerow(turnos_header)
        for t in lista:
            w.writerow([
                t.id,
                t.fecha.isoformat(),
                hhmm(t.hora),
                t.estado,
            ])
        w.writerow([])  

    data = buf_txt.getvalue().encode("utf-8-sig") 
    nombre = f"turnos_por_fecha_{fecha.isoformat()}.csv"
    return io.BytesIO(data), nombre
