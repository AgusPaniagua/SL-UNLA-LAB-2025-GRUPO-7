# SL-UNLA-LAB-2025-GRUPO-7

Proyecto API REST para Python

Link al video de la exposicion del hito 2
https://www.youtube.com/watch?v=qbBFKTzOpJI

Link a la collections de Postman
[https://www.postman.com/aguspaniagua1998-3456770/workspace/endpoints-grupo-7](https://aguspaniagua1998-3456770.postman.co/workspace/agustin's-Workspace~143e45a0-6c8c-4122-80dc-c778cd753c5d/collection/48633848-99106b86-c98a-4c0a-8d8c-bb7cff05e304?action=share&source=copy-link&creator=48493596)

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
    - `PUT /turnos/{id}/confirmar`- Confirmar turno
    - `GET /reportes/turnos-cancelados?min=5`- Trae personas con 5 turnos cancelados como mínimo
**Maximiliano Fabián Anabalon**  
    - `GET /turnos/` — Leer turnos 
    - `GET /turnos/{turno_id}` — Obtener turno por ID  
    - `PUT /turnos/{turno_id}` — Actualizar turno
    - `DELETE /turnos/{turno_id}` — Eliminar turno
    - `GET /reportes/turnos-por-fecha?fecha=YYYY-MM-DD`- Trae los turnos de una fecha
    - `GET /reportes/turnos-cancelados-por-mes`-Trae los turnos cancelados del mes actual
**Fernando Antonio Gomez**  
    - `GET /turnos_disponibles` — Calcular/obtener turnos disponibles para una fecha
    - `GET /reportes/turnos-confirmados?desde=YYYY-MM-DD&hasta=YYYY-MM-DD`-Turnos confirmados desde/hasta
    - `PUT /turnos/{id}/cancelar`- Cancelar turno
**Paniagua Agustín Marcelo**  
    - `GET /personas/` — Traer personas  
    - `GET /personas/{persona_id}` — Obtener persona por ID  
    - `PUT /personas/{persona_id}` — Modificar persona  
    - `DELETE /personas/{persona_id}` — Eliminar persona
    - `GET /reportes/turnos-por-persona?dni=12345678`- Trae turnos de una persona
    - `GET /reportes/estado-personas?habilitada=true/false`-Trae Personas habilitadas/inhabilitadas para turno
