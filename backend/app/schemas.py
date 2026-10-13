from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class PerfilOutput(BaseModel):
    """Perfil de acceso (tabla ``roles``)."""

    id: int
    nombre: str = Field(validation_alias="name")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PerfilCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)


class MenuItemOutput(BaseModel):
    id: int
    etiqueta: str = Field(validation_alias="label")
    icono: str | None = Field(default=None, validation_alias="icon")
    ruta: str | None = Field(default=None, validation_alias="path")
    orden: int = Field(default=0, validation_alias="order_index")
    hijos: list["MenuItemOutput"] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


MenuItemOutput.model_rebuild()


class PermisoItem(BaseModel):
    menu_item_id: int
    is_visible: bool = True
    can_read: bool = True
    can_write: bool = False
    can_delete: bool = False


class PerfilPermisosInput(BaseModel):
    permisos: list[PermisoItem] = Field(default_factory=list)


class LoginInput(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class UserOutput(BaseModel):
    id: int
    username: str
    role: str
    model_config = ConfigDict(from_attributes=True)


class UsuarioRolInput(BaseModel):
    role: str = Field(min_length=2, max_length=30)


class CuentaOutput(BaseModel):
    id: int
    cu_cod: int | None = None
    cu_num_id: str
    cu_pri_nom: str | None = None
    cu_seg_nom: str | None = None
    cu_pri_ape: str | None = None
    cu_seg_ape: str | None = None
    identificacion: str | None = None
    tercero: str | None = None
    nom_tercero: str | None = None
    consultado_en: datetime
    model_config = ConfigDict(from_attributes=True)


class CuentasPaginaOutput(BaseModel):
    items: list[CuentaOutput]
    total: int
    page: int
    page_size: int
    pages: int


class SolicitudCreate(BaseModel):
    cliente_nombre: str = Field(min_length=2, max_length=180)
    documento_cliente: str | None = Field(default=None, max_length=40)
    contacto_nombre: str = Field(min_length=2, max_length=160)
    correo: EmailStr
    telefono: str = Field(min_length=7, max_length=40)
    nombre_evento: str = Field(min_length=3, max_length=200)
    fecha_inicio: date
    fecha_fin: date
    asistentes_estimados: int = Field(ge=1, le=100000)
    descripcion: str = Field(min_length=5, max_length=5000)

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha final no puede ser anterior a la fecha inicial.")
        return self


class SolicitudOutput(BaseModel):
    id: int
    numero: str
    cliente_nombre: str
    documento_cliente: str | None
    contacto_nombre: str
    correo: str
    telefono: str
    nombre_evento: str
    fecha_inicio: date
    fecha_fin: date
    asistentes_estimados: int
    descripcion: str
    estado: str
    creado_en: datetime
    model_config = ConfigDict(from_attributes=True)
