from sqlalchemy import create_engine, Column, Integer, String , Date, Time
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import date, time

engine = create_engine('sqlite:///data_base.db', echo=True) 
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)    


class Turnos(Base): 
    __tablename__ = 'turnos' 
    id = Column(Integer, primary_key=True) 
    fecha = Column(Date, nullable=False) 
    hora = Column(Time, nullable=False)
    estado = Column(String, nullable=False)
    persona_id = Column(Integer, nullable=False)  

Base.metadata.create_all(engine) 

db = SessionLocal()

if db.query(Turnos).count() == 0:
    turno1 = Turnos(fecha=date(2025, 9, 10), hora=time(10, 30), estado="pendiente", persona_id=1)
    turno2 = Turnos(fecha=date(2025, 9, 11), hora=time(14, 0), estado="confirmado", persona_id=2)
    
    db.add_all([turno1, turno2])
    db.commit()
    print("Turnos insertados.")
else:
    print("Ya existen turnos en la base.")

db.close()
