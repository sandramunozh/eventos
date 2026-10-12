from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.config import settings
from app.database import Base, engine, get_db
from app.models import User, Solicitud
from app.schemas import LoginInput, UserOutput, SolicitudCreate, SolicitudOutput
from app.security import verify_password, create_access_token, get_current_user, require_roles

@asynccontextmanager
async def lifespan(app: FastAPI):
    # SOLO para prototipo. En producción, reemplazar create_all por migraciones Alembic.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post(f"{settings.api_prefix}/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == form.username))
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos")
    return {"access_token": create_access_token(user), "token_type": "bearer", "user": UserOutput.model_validate(user)}

@app.get(f"{settings.api_prefix}/auth/me", response_model=UserOutput)
def me(user: User = Depends(get_current_user)):
    return user

@app.post(f"{settings.api_prefix}/solicitudes", response_model=SolicitudOutput, status_code=201)
def crear_solicitud(payload: SolicitudCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    numero = "EV-" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    solicitud = Solicitud(**payload.model_dump(), numero=numero, estado="REGISTRADA", creado_por_id=user.id)
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    return solicitud

@app.get(f"{settings.api_prefix}/solicitudes", response_model=list[SolicitudOutput])
def listar_solicitudes(db: Session = Depends(get_db), user: User = Depends(get_current_user), limite: int = 100):
    limite = max(1, min(limite, 200))
    return list(db.scalars(select(Solicitud).order_by(Solicitud.creado_en.desc()).limit(limite)).all())

@app.get(f"{settings.api_prefix}/solicitudes/{{solicitud_id}}", response_model=SolicitudOutput)
def obtener_solicitud(solicitud_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    solicitud = db.get(Solicitud, solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return solicitud

@app.patch(f"{settings.api_prefix}/solicitudes/{{solicitud_id}}/estado")
def cambiar_estado(solicitud_id: int, estado: str, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "EVENTOS"))):
    permitidos = {"EN_REVISION", "INCOMPLETA", "VIABLE", "NO_VIABLE", "CANCELADA"}
    if estado not in permitidos:
        raise HTTPException(status_code=400, detail="Estado no permitido en este módulo")
    solicitud = db.get(Solicitud, solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    solicitud.estado = estado
    db.commit()
    return {"id": solicitud.id, "estado": solicitud.estado}
