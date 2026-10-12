from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

class LoginInput(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=1, max_length=200)

class UserOutput(BaseModel):
    id: int
    username: str
    role: str
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
