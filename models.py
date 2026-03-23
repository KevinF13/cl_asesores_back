from sqlalchemy import Column, Integer, String, Date, Time, Text, ForeignKey, Numeric, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    rol = Column(String(20), nullable=False)  # 'admin' o 'asesor'
    nombre = Column(String(100), nullable=True)

    # Campos que sí existen en tu BD
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=True, server_default=func.now())
    updated_at = Column(DateTime, nullable=True)

class RegistroKPI(Base):
    __tablename__ = "registros_asesores"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Identificación y Tipo de gestión
    kpi = Column(String(100), nullable=False)
    razon_social = Column(String(255), nullable=True)
    nombre_comercial = Column(String(255), nullable=True)
    a_quien_visito = Column(String(255), nullable=True)
    area = Column(String(100), nullable=True)
    telefono = Column(String(50), nullable=True)

    # Métricas Numéricas
    clientes_nuevos = Column(Integer, default=0)
    prospectos_new = Column(Integer, default=0)
    num_clientes_visitados = Column(Integer, default=0)
    llamadas_clientes = Column(Integer, default=0)
    llamadas_cobranzas = Column(Integer, default=0)

    # Valores Financieros
    us_venta = Column(Numeric(12, 2), default=0.0)
    us_cobro = Column(Numeric(12, 2), default=0.0)
    viajes = Column(Numeric(12, 2), default=0.0)
    alimentacion = Column(Numeric(12, 2), default=0.0)

    # Detalles y Planificación
    desarrollo_visita = Column(Text, nullable=True)
    pendientes = Column(Text, nullable=True)
    fecha_ingreso = Column(Date, nullable=False)
    hora_ingreso = Column(Time, nullable=False)
    fecha_prox_visita = Column(String(100), nullable=True)

    # Auditoría
    fecha_creacion = Column(DateTime, nullable=True, server_default=func.now())