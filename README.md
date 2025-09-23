# SL-UNLA-LAB-2025-GRUPO-7

Proyecto API REST para Python

---

# Instalación

1. Clonar este repositorio:

   git clone https://github.com/AgusPaniagua/SL-UNLA-LAB-2025-GRUPO-7.git

2. Crear entorno virtual:

    .Linux/Mac:
        python3 -m venv venv

    .Windows:
        python -m venv venv

3. Activar entorno virtual:

    Linux/Mac:
        source venv/bin/activate

    Windows:
        venv\Scripts\activate

4. Instalar dependencias:

    pip install -r requirements.txt

5. Levantar la aplicación:
    uvicorn app:app --reload

# Integrantes

    -Juan ignacio amalfitano, 45397013

    -Maximiliano Fabián Anabalon, 32670577

    -Fernando Antonio Gomez, 43036843

    -Paniagua Agustin Marcelo, 41080379

# Funcionalidades

**Juan Ignacio Amalfitano** 
    - `POST /personas` — Crear persona  
    - `POST /turnos` — Crear turno

**Maximiliano Fabián Anabalon**  
    - `GET /turnos/` — Leer turnos 
    - `GET /turnos/{turno_id}` — Obtener turno por ID  
    - `PUT /turnos/{turno_id}` — Actualizar turno
    - `DELETE /turnos/{turno_id}` — Eliminar turno

**Fernando Antonio Gomez**  
    - `GET /turnos_disponibles` — Calcular/obtener turnos disponibles para una fecha

**Paniagua Agustín Marcelo**  
    - `GET /personas/` — Traer personas  
    - `GET /personas/{persona_id}` — Obtener persona por ID  
    - `PUT /personas/{persona_id}` — Modificar persona  
    - `DELETE /personas/{persona_id}` — Eliminar persona