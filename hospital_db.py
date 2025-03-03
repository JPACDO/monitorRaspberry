#!/usr/bin/python3


from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class Paciente(Base):
    __tablename__ = 'pacientes'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    identificacion = Column(String)
    tiempoGuardado =  Column(Integer, default= 2)

    alarmas = relationship('Alarma', back_populates='paciente')
    ekg = relationship('EKG', back_populates='paciente')
    presion = relationship('Presion', back_populates='paciente')
    temperatura = relationship('Temperatura', back_populates='paciente')
    spo2 = relationship('SpO2', back_populates='paciente')
    

class Alarma(Base):
    __tablename__ = 'alarmas'
    id = Column(Integer, primary_key=True)
    tipo = Column(String)
    valor = Column(String)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))

    paciente = relationship('Paciente', back_populates='alarmas')

class EKG(Base):
    __tablename__ = 'ekg'
    id = Column(Integer, primary_key=True)
    valor = Column(String)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))

    paciente = relationship('Paciente', back_populates='ekg')

class Presion(Base):
    __tablename__ = 'presion'
    id = Column(Integer, primary_key=True)
    valor = Column(String)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))

    paciente = relationship('Paciente', back_populates='presion')

class Temperatura(Base):
    __tablename__ = 'temperatura'
    id = Column(Integer, primary_key=True)
    valor = Column(String)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))

    paciente = relationship('Paciente', back_populates='temperatura')

class SpO2(Base):
    __tablename__ = 'spo2'
    id = Column(Integer, primary_key=True)
    valor = Column(String)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))

    paciente = relationship('Paciente', back_populates='spo2')
    

class HospitalDB:
    def __init__(self, db_url='sqlite:///hospital.db?check_same_thread=False'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # Obtener el último paciente o crear uno nuevo
   
        #self.session = self.Session()
        self.paciente = self.get_ultimo_paciente()
        if not self.paciente:
            self.paciente = self.create_paciente('Nuevo Paciente')

    def create_paciente(self, nombre, identificacion=None, tiempoGuardado=2):
        with self.Session() as session:
            paciente = Paciente(nombre=nombre, identificacion=identificacion, tiempoGuardado=int(tiempoGuardado))
            session.add(paciente)
            session.commit()
            session.refresh(paciente)
            print('creado')
            return paciente

    def get_paciente(self, paciente_id):
        with self.Session() as session:
            return session.query(Paciente).get(paciente_id)

    def update_paciente(self, paciente_id, nombre=None, identificacion=None, tiempoGuardado=None):
        with self.Session() as session:
            paciente = session.query(Paciente).get(paciente_id)
            if nombre:
                paciente.nombre = nombre
            if identificacion:
                paciente.identificacion = identificacion
            if tiempoGuardado:
                paciente.tiempoGuardado = int(tiempoGuardado)
            session.commit()
            return paciente

    def delete_paciente(self, paciente_id):
        with self.Session() as session:
            paciente = session.query(Paciente).get(paciente_id)
            session.delete(paciente)
            session.commit()

    def add_alarma(self, paciente_id, tipo, valor):
        with self.Session() as session:
            alarma = Alarma(tipo=tipo, valor=valor, paciente_id=paciente_id, fecha_hora=datetime.now())
            session.add(alarma)
            session.commit()
            return alarma

    def add_ekg(self, paciente_id, valor):
        with self.Session() as session:
            ekg = EKG(valor=valor, paciente_id=paciente_id, fecha_hora=datetime.now())
            session.add(ekg)
            session.commit()
            return ekg

    def add_presion(self, paciente_id, valor):
        with self.Session() as session:
            presion = Presion(valor=valor, paciente_id=paciente_id, fecha_hora=datetime.now())
            session.add(presion)
            session.commit()
            return presion

    def add_temperatura(self, paciente_id, valor):
        with self.Session() as session:
            temperatura = Temperatura(valor=valor, paciente_id=paciente_id, fecha_hora=datetime.now())
            session.add(temperatura)
            session.commit()
            return temperatura

    def add_spo2(self, paciente_id, valor):
        with self.Session() as session:
            spo2 = SpO2(valor=valor, paciente_id=paciente_id, fecha_hora=datetime.now())
            session.add(spo2)
            session.commit()
            return spo2

    def get_pacientes(self):
        with self.Session() as session:
            return session.query(Paciente).all()

    def get_alarmas(self, paciente_id):
        with self.Session() as session:
            return session.query(Alarma).filter(Alarma.paciente_id == paciente_id).order_by(desc(Alarma.id)).all()

    def get_ekgs(self, paciente_id):
        with self.Session() as session:
            return session.query(EKG).filter(EKG.paciente_id == paciente_id).order_by(desc(EKG.id)).all()

    def get_presiones(self, paciente_id):
        with self.Session() as session:
            return session.query(Presion).filter(Presion.paciente_id == paciente_id).order_by(desc(Presion.id)).all()

    def get_temperaturas(self, paciente_id):
        with self.Session() as session:
            return session.query(Temperatura).filter(Temperatura.paciente_id == paciente_id).order_by(desc(Temperatura.id)).all()

    def get_spo2s(self, paciente_id):
        with self.Session() as session:
            return session.query(SpO2).filter(SpO2.paciente_id == paciente_id).order_by(desc(SpO2.id)).all()

    def get_ultimo_paciente(self):
        with self.Session() as session:
            return session.query(Paciente).order_by(desc(Paciente.id)).first()
    
    
        
