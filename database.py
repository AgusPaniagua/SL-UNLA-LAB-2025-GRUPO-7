from sqlalchemy import create_engine, Column, Integer, String , Date, Time, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import date, time

#Creacion y configuracion de la base de datos
engine = create_engine('sqlite:///data_base.db', echo=True) 
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)    

#Creacion de tabla turnos
class Turnos(Base): 
    __tablename__ = 'turnos' 
    id = Column(Integer, primary_key=True) 
    fecha = Column(Date, nullable=False) 
    hora = Column(Time, nullable=False)
    estado = Column(String, nullable=False)
    #persona_id = Column(Integer, nullable=False)
    persona_id = Column(Integer, ForeignKey('personas.id'), nullable=False)
    persona = relationship("Persona", back_populates="turnos")
     

#Creacion de tabla personas
class Persona(Base):
    __tablename__='personas'
    id = Column(Integer,primary_key=True)
    nombre = Column(String,nullable=False)
    email = Column(String,nullable=False,unique=True)
    dni = Column(Integer,nullable=False,unique=True)
    telefono = Column(String,nullable=True)
    fecha_de_nacimiento = Column(Date, nullable=False)
    edad = Column(Integer, nullable=False)
    habilitado_para_turno = Column(Boolean, nullable=False)
    turnos = relationship("Turnos", back_populates="persona")

#Creacion de las tablas en la base de datos
Base.metadata.create_all(engine) 

db = SessionLocal()
# #Creacion de datos para la base datos por si no tiene ningun turno cargado
# if db.query(Turnos).count() == 0:
#     turno1 = Turnos(fecha=date(2025, 9, 10), hora=time(10, 30), estado="pendiente", persona_id=1)
#     turno2 = Turnos(fecha=date(2025, 9, 11), hora=time(14, 0), estado="confirmado", persona_id=2)
    
#     db.add_all([turno1, turno2])
#     db.commit()
#     print("Turnos insertados.")
# else:
#     print("Ya existen turnos en la base.")

#Creacion de datos para la base datos por si no tiene ninguna persona cargada
if db.query(Persona).count() == 0:
    persona1 = Persona(
        nombre="pesona1",
        email="persona1@gmail.com",
        dni=123456789,
        telefono=1122334455,
        fecha_de_nacimiento=date(2000, 1, 1),
        edad=25,
        habilitado_para_turno=True
    )
    persona2 = Persona(
        nombre="pesona2",
        email="persona2@gmail.com",
        dni=234567890,
        telefono=1133445566,
        fecha_de_nacimiento=date(2001, 1, 1),
        edad=24,
        habilitado_para_turno=True
    )
    
    db.add_all([persona1, persona2])
    db.commit()
    print("Personas insertadas.")
else:
    print("Ya existen personas en la base.")

#Creacion de datos para la base datos por si no tiene ningun turno cargado
if db.query(Turnos).count() == 0:
    
    turno1 = Turnos(fecha=date(2025, 9, 10), hora=time(10, 30), estado="pendiente", persona_id=1)
    turno2 = Turnos(fecha=date(2025, 9, 11), hora=time(14, 0), estado="confirmado", persona_id=2)
    
    db.add_all([turno1, turno2])
    db.commit()
    print("Turnos insertados.")
else:
    print("Ya existen turnos en la base.")

db.close()
