import io
from borb.pdf import Document, Page, PDF
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.layout.table.table import Table, TableCell
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.horizontal_rule import HorizontalRule
from borb.pdf.canvas.color.color import HexColor
from decimal import Decimal
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
    
    encabezados = ["ID","Nombre","Email","Dni","Telefono","Edad","Habilitado"]
    numero_de_columnas=len(encabezados)
    tamaño_de_columnas=[
        Decimal("0.08"),
        Decimal("0.20"),
        Decimal("0.45"),
        Decimal("0.25"),
        Decimal("0.25"),
        Decimal("0.15"),
        Decimal("0.25"),
    ]
    tabla = FixedColumnWidthTable(number_of_rows=len(data)+1,number_of_columns=numero_de_columnas,column_widths=tamaño_de_columnas)
    #Agregamos a las personas
    
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
        
    
    tabla.set_padding_on_all_cells(5,5,5,5)
    tabla.set_border_color_on_all_cells(HexColor("#CCCCCC"))
    diseño.add(tabla)
    buffer = io.BytesIO()
    PDF.dumps(buffer,documento)
    buffer.seek(0)
    return buffer