from datetime import date, datetime, time
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


class TrabajadorFilaOutput(BaseModel):
    LLAVE: str | None = None
    TIPO: str | None = None
    CUCOD: int | None = None
    CUNUMID: str | None = None
    NOMBRE: str | None = None
    CUPRIAPE: str | None = None
    CUSEGAPE: str | None = None
    CUPRINOM: str | None = None
    CUSEGNOM: str | None = None
    CUGENERO: str | None = None
    CUFECNACI: str | None = None
    CATTRAB: str | None = None
    CUCODTRABAJADOR: int | None = None
    GFCODGRUFA: int | None = None
    SUCURSAL: int | None = None
    TRTIPCONTR: str | None = None
    EMCODEMPRE: int | None = None
    ESTADO_PAGO: str | None = None
    TRCODTRABA: str | None = None
    CUCLASIFIC: str | None = None
    EMPORCAJA: str | None = None


class CondicionOutput(BaseModel):
    regla: str
    valor: str | int | None = None
    cumple: bool


class MiembroGrupoOutput(BaseModel):
    TIPO: str | None = None
    CUCOD: int | None = None
    CUNUMID: str | None = None
    NOMBRE: str | None = None


class SubsidioRegistroOutput(BaseModel):
    registro: int
    fecha: date
    tipo_venta: str | None = None
    valor_tar: float | None = None
    valor_des: float | None = None
    porcentaje: float | None = None
    categoria: str | None = None
    grupo: int | None = None
    voucher: str | None = None
    mismo_dia: bool


class SubsidiosDiaMesOutput(BaseModel):
    P: int = 0
    R: int = 0


class SubsidiosOutput(BaseModel):
    mismo_dia: SubsidiosDiaMesOutput
    mismo_mes: SubsidiosDiaMesOutput
    registros: list[SubsidioRegistroOutput]


class TrabajadorConsultaOutput(BaseModel):
    documento: str
    fecha: date
    encontrado: bool
    tipo_registro: str = "T"
    cumple_condiciones: bool
    trabajador: TrabajadorFilaOutput | None = None
    trabajador_asociado: TrabajadorFilaOutput | None = None
    condiciones: list[CondicionOutput] = Field(default_factory=list)
    grupo_familiar: list[MiembroGrupoOutput] = Field(default_factory=list)
    beneficiarios: list[MiembroGrupoOutput] = Field(default_factory=list)
    subsidios: SubsidiosOutput


TAREAS_AGENDA = {
    "LLAMADA TELEFÓNICA",
    "VISITA",
    "FERIA DE SERVICIOS",
    "STAND INFORMATIVO",
    "ACOMPAÑAMIENTO EVENTO",
    "CHARLA DE SERVICIOS",
    "MODELO (RELACIONAMIENTO)",
    "VISITA VIRTUAL",
    "CHARLA DE SERVICIOS VIRTUAL",
    "ACOMPAÑAR. EVENTO VIRTUAL",
}
ESTADOS_AGENDA = {"NO INICIADA", "CANCELADA", "REALIZADA", "NO EFECTIVA", "CREADA ERROR"}


class AgendaCreate(BaseModel):
    tarea: str = Field(min_length=3, max_length=60)
    estado: str = Field(default="NO INICIADA", max_length=30)
    fecha: date
    hora: time | None = None
    lugar_empresa: str | None = Field(default=None, max_length=180)
    empresa_nit: str | None = Field(default=None, max_length=40)
    empresa_nombre: str | None = Field(default=None, max_length=180)
    contacto: str | None = Field(default=None, max_length=160)
    correo_contacto: EmailStr | None = None
    telefono: str | None = Field(default=None, min_length=6, max_length=40)
    descripcion: str | None = Field(default=None, max_length=20000)

    @model_validator(mode="after")
    def validar_listas(self):
        if self.tarea.strip().upper() not in TAREAS_AGENDA:
            raise ValueError(f"Tarea no válida. Opciones: {', '.join(sorted(TAREAS_AGENDA))}")
        if self.estado.strip().upper() not in ESTADOS_AGENDA:
            raise ValueError(f"Estado no válido. Opciones: {', '.join(sorted(ESTADOS_AGENDA))}")
        return self


class AgendaUpdate(BaseModel):
    tarea: str | None = Field(default=None, min_length=3, max_length=60)
    estado: str | None = Field(default=None, max_length=30)
    fecha: date | None = None
    hora: time | None = None
    lugar_empresa: str | None = Field(default=None, max_length=180)
    empresa_nit: str | None = Field(default=None, max_length=40)
    empresa_nombre: str | None = Field(default=None, max_length=180)
    contacto: str | None = Field(default=None, max_length=160)
    correo_contacto: EmailStr | None = None
    telefono: str | None = Field(default=None, min_length=6, max_length=40)
    descripcion: str | None = Field(default=None, max_length=20000)

    @model_validator(mode="after")
    def validar_listas(self):
        if self.tarea is not None and self.tarea.strip().upper() not in TAREAS_AGENDA:
            raise ValueError(f"Tarea no válida. Opciones: {', '.join(sorted(TAREAS_AGENDA))}")
        if self.estado is not None and self.estado.strip().upper() not in ESTADOS_AGENDA:
            raise ValueError(f"Estado no válido. Opciones: {', '.join(sorted(ESTADOS_AGENDA))}")
        return self


class AgendaOutput(BaseModel):
    id: int
    tarea: str
    estado: str
    fecha: date
    hora: time | None
    lugar_empresa: str | None
    empresa_nit: str | None
    empresa_nombre: str | None
    contacto: str | None
    correo_contacto: str | None
    telefono: str | None
    descripcion: str | None
    creado_en: datetime
    model_config = ConfigDict(from_attributes=True)


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
