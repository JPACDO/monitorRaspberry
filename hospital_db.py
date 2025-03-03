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
    def __init__(self, db_url='sqlite:///hospital.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # Obtener el último paciente o crear uno nuevo
        self.session = self.Session()
        self.paciente = self.get_ultimo_paciente()
        if not self.paciente:
            self.paciente = self.create_paciente('Nuevo Paciente')

    def create_paciente(self, nombre, identificacion=None, tiempoGuardado=2):
        paciente = Paciente(nombre=nombre, identificacion=identificacion, tiempoGuardado=int(tiempoGuardado))
        self.session.add(paciente)
        self.session.commit()
        return paciente

    def get_paciente(self, paciente_id):
        return self.session.query(Paciente).get(paciente_id)

    def update_paciente(self, paciente_id, nombre=None, identificacion=None, tiempoGuardado=None):
        paciente = self.session.query(Paciente).get(paciente_id)
        if nombre:
            paciente.nombre = nombre
        if identificacion:
            paciente.identificacion = identificacion
        if tiempoGuardado:
            paciente.tiempoGuardado = int(tiempoGuardado)
        self.session.commit()
        return paciente

    def delete_paciente(self, paciente_id):
        paciente = self.session.query(Paciente).get(paciente_id)
        self.session.delete(paciente)
        self.session.commit()

    def add_alarma(self, paciente_id, tipo, valor):
        alarma = Alarma(tipo=tipo, valor=valor, paciente_id=paciente_id)
        self.session.add(alarma)
        self.session.commit()
        return alarma

    def add_ekg(self, paciente_id, valor):
        ekg = EKG(valor=valor, paciente_id=paciente_id)
        self.session.add(ekg)
        self.session.commit()
        return ekg

    def add_presion(self, paciente_id, valor):
        presion = Presion(valor=valor, paciente_id=paciente_id)
        self.session.add(presion)
        self.session.commit()
        return presion

    def add_temperatura(self, paciente_id, valor):
        temperatura = Temperatura(valor=valor, paciente_id=paciente_id)
        self.session.add(temperatura)
        self.session.commit()
        return temperatura

    def add_spo2(self, paciente_id, valor):
        spo2 = SpO2(valor=valor, paciente_id=paciente_id)
        self.session.add(spo2)
        self.session.commit()
        return spo2

    def get_pacientes(self):
        return self.session.query(Paciente).all()

    def get_alarmas(self, paciente_id):
        return self.session.query(Alarma).filter(Alarma.paciente_id == paciente_id).all()

    def get_ekgs(self, paciente_id):
        return self.session.query(EKG).filter(EKG.paciente_id == paciente_id).all()

    def get_presiones(self, paciente_id):
        return self.session.query(Presion).filter(Presion.paciente_id == paciente_id).all()

    def get_temperaturas(self, paciente_id):
        return self.session.query(Temperatura).filter(Temperatura.paciente_id == paciente_id).all()

    def get_spo2s(self, paciente_id):
        return self.session.query(SpO2).filter(SpO2.paciente_id == paciente_id).all()

    def get_ultimo_paciente(self):
        return self.session.query(Paciente).order_by(desc(Paciente.id)).first()
    
    
        
