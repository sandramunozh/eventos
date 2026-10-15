from datetime import datetime, date, time
from sqlalchemy import String, Integer, Date, DateTime, Text, ForeignKey, Boolean, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Role(Base):
    """Perfil de acceso. Corresponde a la tabla existente ``roles``."""

    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    menus = relationship("RoleMenu", back_populates="role", cascade="all, delete-orphan")


class MenuItem(Base):
    """Opción de menú. Corresponde a la tabla existente ``menu_items``."""

    __tablename__ = "menu_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("menu_items.id"), nullable=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    path: Mapped[str | None] = mapped_column(String(200), nullable=True)
    order_index: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    permisos = relationship("RoleMenu", back_populates="menu_item", cascade="all, delete-orphan")


class RoleMenu(Base):
    """Permisos de un perfil sobre una opción de menú (tabla ``role_menu``)."""

    __tablename__ = "role_menu"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    can_read: Mapped[bool] = mapped_column(Boolean, default=True)
    can_write: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    role = relationship("Role", back_populates="menus")
    menu_item = relationship("MenuItem", back_populates="permisos")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="EVENTOS")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Cuenta(Base):
    """Caché de las cuentas/terceros consultados al servicio WebApiComfamiliar.

    El servicio externo solo permite consultar por número de identificación;
    esta tabla permite listar, filtrar y paginar los clientes ya consultados.
    """

    __tablename__ = "cuentas"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cu_cod: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cu_num_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    cu_pri_nom: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cu_seg_nom: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cu_pri_ape: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cu_seg_ape: Mapped[str | None] = mapped_column(String(100), nullable=True)
    identificacion: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tercero: Mapped[str | None] = mapped_column(String(40), nullable=True)
    nom_tercero: Mapped[str | None] = mapped_column(String(180), nullable=True)
    consultado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    consultado_por_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class AgendaActividad(Base):
    """Actividad de la agenda comercial (opción de menú 'Agenda del día')."""

    __tablename__ = "agenda_actividades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tarea: Mapped[str] = mapped_column(String(60), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="NO INICIADA")
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hora: Mapped[time | None] = mapped_column(Time, nullable=True)
    lugar_empresa: Mapped[str | None] = mapped_column(String(180), nullable=True)
    empresa_nit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    empresa_nombre: Mapped[str | None] = mapped_column(String(180), nullable=True)
    contacto: Mapped[str | None] = mapped_column(String(160), nullable=True)
    correo_contacto: Mapped[str | None] = mapped_column(String(254), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_por_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
