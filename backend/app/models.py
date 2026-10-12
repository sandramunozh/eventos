from datetime import datetime, date
from sqlalchemy import String, Integer, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="EVENTOS")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Solicitud(Base):
    __tablename__ = "solicitudes_eventos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    cliente_nombre: Mapped[str] = mapped_column(String(180))
    documento_cliente: Mapped[str | None] = mapped_column(String(40), nullable=True)
    contacto_nombre: Mapped[str] = mapped_column(String(160))
    correo: Mapped[str] = mapped_column(String(254))
    telefono: Mapped[str] = mapped_column(String(40))
    nombre_evento: Mapped[str] = mapped_column(String(200))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    asistentes_estimados: Mapped[int] = mapped_column(Integer)
    descripcion: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(40), default="REGISTRADA")
    creado_por_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    creador = relationship("User")
