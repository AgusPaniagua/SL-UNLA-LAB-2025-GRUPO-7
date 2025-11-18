import io
from borb.pdf import Document, Page, PDF
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.layout.table.table import Table, TableCell
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.horizontal_rule import HorizontalRule
from borb.pdf.canvas.color.color import HexColor
from decimal import Decimal
import pandas as pd
import utils

def generar_pdf_turnos_cancelados(data: dict):
    """
    Genera un PDF con los turnos cancelados según la estructura JSON que pasaste.
    Devuelve un BytesIO listo para enviar como StreamingResponse en FastAPI.
    """

    doc = Document()
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)
    #Título

    # Títulos existentes    
    layout.add(Paragraph(f"Materia: Seminario Python", font_size=22, font_color=HexColor("003366"), font="Helvetica-Bold"))
    layout.add(Paragraph(f"Alumno: Maximiliano F. Anabalon", font_size=20, font_color=HexColor("003366"), font="Helvetica-Bold"))
    layout.add(Paragraph(" "))
    layout.add(Paragraph(" "))
    layout.add(Paragraph(f"Reporte de Turnos Cancelados - {data['mes'].capitalize()} {data['anio']}", font_size=18))
    layout.add(Paragraph(f"Cantidad total de turnos cancelados: {data['cantidad']}", font_size=12))
    layout.add(Paragraph(" "))  
    layout.add(Paragraph(" "))# Espacio

    # Segunda página con los detalles
    page2 = Page()
    doc.add_page(page2)
    layout2 = SingleColumnLayout(page2)
    layout2.add(Paragraph(" "))
    for persona_data in data["turnos"]:  # lista de PersonaConTurnos (objetos Pydantic)
        persona = persona_data.persona  # DatosPersona (objeto Pydantic)
        layout2.add(Paragraph(f"Persona: {persona.nombre} - DNI: {persona.dni} - EMAIL {persona.email} - TELEFONO: {persona.telefono}", font="Helvetica-Bold", font_size=14,font_color=HexColor("0D1366")))
        if(persona.habilitado_para_turno):
            layout2.add(Paragraph(f"Habilitado para turno: SI", font_size=14,font_color=HexColor("52D93D")))    
        else:
            layout2.add(Paragraph(f"Habilitado para turno: NO", font_size=14,font_color=HexColor("D90909")))    
        #for turno in persona_data.turnos:  # lista de TurnoInfoDni (objetos Pydantic)
        for turno in persona_data.turnos:  # lista de TurnoInfoDni (objetos Pydantic)
            layout2.add(
                Paragraph(
                    f"ID: {turno.id} Fecha: {turno.fecha} Hora: {turno.hora} Estado: {turno.estado}",
                    font_size=10,
                    # font_color=HexColor("2761F5")
                )
            )        
        
    # Guardar en BytesIO
    pdf_bytes = io.BytesIO()
    PDF.dumps(pdf_bytes, doc)
    pdf_bytes.seek(0)
    return pdf_bytes

        # ultimo_mes = hoy - relativedelta(months=1)
        # mes = ultimo_mes.month

def generar_pdf_con_estado_de_personas(data:list):
    documento= Document()
    pagina=Page()
    documento.add_page(pagina)
    diseño=SingleColumnLayout(pagina)

    #Titulo
    utils.agregar_titulo(diseño,"Reporte de estado de personas")
    #Agregamos los encabezados para saber el numero de columnas que vamos a usar
    encabezados = ["ID","Nombre","Email","Dni","Telefono","Edad","Habilitado"]
    #Aca se define el tamaño de cada columa
    tamaño_de_columnas=[
        Decimal("0.08"),
        Decimal("0.20"),
        Decimal("0.45"),
        Decimal("0.25"),
        Decimal("0.25"),
        Decimal("0.15"),
        Decimal("0.25"),
    ]
    #Se crea la tabla
    tabla = utils.agregar_tabla(len(data),len(encabezados),tamaño_de_columnas)

    #Agregamos a las personas y sus datos 
    for encabezado in encabezados:
        tabla.add(
            TableCell(
                Paragraph(encabezado,font="Helvetica-Bold",font_color=HexColor("003366")),
            )
        )
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
        for datos in datos_persona:
            tabla.add(TableCell(Paragraph(str(datos))))
        
    #Separamos un poco y agregamos un poco de color a la tabla
    tabla.set_padding_on_all_cells(5,5,5,5)
    tabla.set_border_color_on_all_cells(HexColor("#CCCCCC"))
    diseño.add(tabla)
    buffer = io.BytesIO()
    PDF.dumps(buffer,documento)
    buffer.seek(0)
    return buffer

def generar_csv_con_estado_de_personas(data:list):
    personas = []
    for persona in data:
        datos_persona={
            "ID":persona.id,
            "Nombre":persona.nombre,
            "Email":persona.email,
            "Dni":persona.dni,
            "Telefono":persona.telefono,
            "Edad":persona.edad,
            "Habilitado":persona.habilitado_para_turno,
        }
        personas.append(datos_persona)
    
    df = pd.DataFrame(personas)
    buffer_encabezado = io.StringIO()
    buffer_encabezado.write(f"Registro de estado de personas\n")
    buffer_encabezado .write(f"\n")
    df.to_csv(buffer_encabezado,index=False,encoding="utf-8")
    buffer_encabezado.seek(0)
    buffer = io.BytesIO(buffer_encabezado.getvalue().encode('utf-8'))
    buffer.seek(0)
    return buffer

def generar_pdf_con_turnos_por_dni(data:list):

    persona_con_turnos=data[0]
    persona=persona_con_turnos.persona
    lista_turnos=persona_con_turnos.turnos

    documento= Document()
    pagina=Page()
    documento.add_page(pagina)
    diseño=SingleColumnLayout(pagina)
    utils.agregar_titulo(diseño,"Reporte de turnos de una persona mediante su dni")
    encabezados_persona = ["ID","Nombre","Email","Dni","Telefono","Edad","Habilitado"]
    encabezados_turno=["ID","Fecha","Hora","Estado"]
    tamaño_de_columnas_persona=[
        Decimal("0.08"),
        Decimal("0.20"),
        Decimal("0.45"),
        Decimal("0.25"),
        Decimal("0.25"),
        Decimal("0.15"),
        Decimal("0.25"),
    ]
    tamaño_de_columnas_turno=[
        Decimal("0.20"),
        Decimal("0.20"),
        Decimal("0.20"),
        Decimal("0.20"),
    ]
    tabla_persona=utils.agregar_tabla(1,len(encabezados_persona),tamaño_de_columnas_persona)
    tabla_turno=utils.agregar_tabla(len(lista_turnos),len(encabezados_turno),tamaño_de_columnas_turno)

    for encabezado in encabezados_persona:
        tabla_persona.add(
            TableCell(
                Paragraph(encabezado,font="Helvetica-Bold",font_color=HexColor("003366")),
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
        datos_turno=[
            turno.id,
            turno.fecha,
            turno.hora,
            turno.estado
        ]
        for dato in datos_turno:
            tabla_turno.add(TableCell(Paragraph(str(dato))))
            
    #Separamos un poco y agregamos un poco de color a la tabla
    tabla_persona.set_padding_on_all_cells(5,5,5,5)
    tabla_persona.set_border_color_on_all_cells(HexColor("#CCCCCC"))
    diseño.add(tabla_persona)
    tabla_turno.set_padding_on_all_cells(5,5,5,5)
    tabla_turno.set_border_color_on_all_cells(HexColor("#CCCCCC"))
    diseño.add(tabla_turno)
    buffer = io.BytesIO()
    PDF.dumps(buffer,documento)
    buffer.seek(0)
    return buffer