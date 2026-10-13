from contextlib import asynccontextmanager
from datetime import datetime
from math import ceil
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, func, or_, and_, cast, String
from app.config import settings
from app.database import Base, engine, get_db
from app.models import User, Solicitud, MenuItem, Role, RoleMenu, Cuenta
from app.schemas import (
    LoginInput,
    UserOutput,
    UsuarioRolInput,
    SolicitudCreate,
    SolicitudOutput,
    MenuItemOutput,
    PerfilCreate,
    PerfilOutput,
    PerfilPermisosInput,
    CuentaOutput,
    CuentasPaginaOutput,
)
from app.security import verify_password, create_access_token, get_current_user, require_roles
from app.terceros import consultar_tercero_externo, limpiar_identificacion, normalizar_tercero

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
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


def _construir_arbol_menu(items: list[MenuItem]) -> list[MenuItemOutput]:
    hijos_por_padre: dict[int | None, list[MenuItem]] = {}
    for item in items:
        hijos_por_padre.setdefault(item.parent_id, []).append(item)

    def construir(item: MenuItem) -> MenuItemOutput:
        hijos = sorted(hijos_por_padre.get(item.id, []), key=lambda x: (x.order_index or 0, x.id))
        return MenuItemOutput(
            id=item.id,
            etiqueta=item.label,
            icono=item.icon,
            ruta=item.path,
            orden=item.order_index or 0,
            hijos=[construir(hijo) for hijo in hijos],
        )

    raices = sorted(hijos_por_padre.get(None, []), key=lambda x: (x.order_index or 0, x.id))
    return [construir(raiz) for raiz in raices]


def require_menu_access(path: str):
    """Exige que el perfil del usuario tenga visible (y lectura) la opción de menú indicada."""
    def dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        permitido = db.scalar(
            select(RoleMenu.id)
            .join(MenuItem, MenuItem.id == RoleMenu.menu_item_id)
            .join(Role, Role.id == RoleMenu.role_id)
            .where(
                Role.name == user.role,
                MenuItem.path == path,
                RoleMenu.is_visible == True,
                RoleMenu.can_read == True,
            )
        )
        if permitido is None:
            raise HTTPException(status_code=403, detail="Su perfil no tiene permisos para esta opción del menú.")
        return user
    return dependency


def _guardar_cuenta(db: Session, data: dict, usuario_id: int) -> None:
    num = str(data.get("cuNumId") or "").strip()
    if not num:
        return
    cuenta = db.scalar(select(Cuenta).where(Cuenta.cu_num_id == num))
    if cuenta is None:
        cuenta = Cuenta(cu_num_id=num)
        db.add(cuenta)
    try:
        cuenta.cu_cod = int(data.get("cuCod") or 0) or None
    except (TypeError, ValueError):
        cuenta.cu_cod = None
    cuenta.cu_pri_nom = str(data.get("cuPriNom") or "").strip() or None
    cuenta.cu_seg_nom = str(data.get("cuSegNom") or "").strip() or None
    cuenta.cu_pri_ape = str(data.get("cuPriApe") or "").strip() or None
    cuenta.cu_seg_ape = str(data.get("cuSegApe") or "").strip() or None
    cuenta.identificacion = str(data.get("identificacion") or "").strip() or None
    cuenta.tercero = str(data.get("tercero") or "").strip() or None
    cuenta.nom_tercero = str(data.get("nomTercero") or "").strip() or None
    cuenta.consultado_en = datetime.utcnow()
    cuenta.consultado_por_id = usuario_id
    db.commit()


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


@app.get(f"{settings.api_prefix}/menu", response_model=list[MenuItemOutput])
def get_menu(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Menú visible para el perfil (role) del usuario autenticado."""
    role = db.scalar(select(Role).where(Role.name == user.role))
    if role is None:
        return []

    permitidos = set(
        db.scalars(
            select(RoleMenu.menu_item_id).where(
                RoleMenu.role_id == role.id,
                RoleMenu.is_visible == True,
            )
        ).all()
    )
    if not permitidos:
        return []

    todos = list(db.scalars(select(MenuItem).where(MenuItem.is_active == True)).all())

    def tiene_descendiente_permitido(item_id: int) -> bool:
        for item in todos:
            if item.parent_id == item_id:
                if item.id in permitidos or tiene_descendiente_permitido(item.id):
                    return True
        return False

    visibles = [item for item in todos if item.id in permitidos or tiene_descendiente_permitido(item.id)]
    return _construir_arbol_menu(visibles)


@app.get(f"{settings.api_prefix}/menu-items", response_model=list[MenuItemOutput])
def menu_completo(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    todos = list(db.scalars(select(MenuItem).where(MenuItem.is_active == True)).all())
    return _construir_arbol_menu(todos)


@app.get(f"{settings.api_prefix}/perfiles", response_model=list[PerfilOutput])
def listar_perfiles(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    return list(db.scalars(select(Role).order_by(Role.name)).all())


@app.post(f"{settings.api_prefix}/perfiles", response_model=PerfilOutput, status_code=201)
def crear_perfil(payload: PerfilCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    if db.scalar(select(Role).where(Role.name == payload.nombre)):
        raise HTTPException(status_code=409, detail="Ya existe un perfil con ese nombre")
    perfil = Role(name=payload.nombre)
    db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil


@app.get(f"{settings.api_prefix}/perfiles/{{perfil_id}}/permisos", response_model=list[int])
def obtener_permisos(perfil_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    if not db.get(Role, perfil_id):
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return list(
        db.scalars(
            select(RoleMenu.menu_item_id).where(
                RoleMenu.role_id == perfil_id,
                RoleMenu.is_visible == True,
            )
        ).all()
    )


@app.put(f"{settings.api_prefix}/perfiles/{{perfil_id}}/permisos", response_model=list[int])
def asignar_permisos(perfil_id: int, payload: PerfilPermisosInput, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    if not db.get(Role, perfil_id):
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    menu_validos = set(db.scalars(select(MenuItem.id)).all())
    db.execute(delete(RoleMenu).where(RoleMenu.role_id == perfil_id))
    visibles: list[int] = []
    for permiso in payload.permisos:
        if permiso.menu_item_id not in menu_validos:
            continue
        db.add(
            RoleMenu(
                role_id=perfil_id,
                menu_item_id=permiso.menu_item_id,
                is_visible=permiso.is_visible,
                can_read=permiso.can_read,
                can_write=permiso.can_write,
                can_delete=permiso.can_delete,
            )
        )
        if permiso.is_visible:
            visibles.append(permiso.menu_item_id)
    db.commit()
    return visibles


@app.get(f"{settings.api_prefix}/usuarios", response_model=list[UserOutput])
def listar_usuarios(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    return list(db.scalars(select(User).order_by(User.username)).all())


@app.patch(f"{settings.api_prefix}/usuarios/{{user_id}}/rol", response_model=UserOutput)
def asignar_rol_usuario(user_id: int, payload: UsuarioRolInput, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    usuario = db.get(User, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not db.scalar(select(Role).where(Role.name == payload.role)):
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    usuario.role = payload.role
    db.commit()
    db.refresh(usuario)
    return usuario


@app.get(f"{settings.api_prefix}/cuentas", response_model=CuentasPaginaOutput)
def listar_cuentas(
    page: int = 1,
    page_size: int = 20,
    numero_identificacion: str = "",
    nombre: str = "",
    codigo: str = "",
    tercero: str = "",
    nom_tercero: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(require_menu_access("/cuenta_cr.faces")),
):
    """Consulta paginada de clientes consultados, con filtros por campo."""
    page = max(1, page)
    page_size = max(1, min(page_size, 50))

    conds = []
    if numero_identificacion:
        patron = f"%{numero_identificacion.strip()}%"
        conds.append(or_(Cuenta.cu_num_id.like(patron), Cuenta.identificacion.like(patron)))
    if nombre:
        patron = f"%{nombre.strip()}%"
        conds.append(
            or_(
                Cuenta.cu_pri_nom.like(patron),
                Cuenta.cu_seg_nom.like(patron),
                Cuenta.cu_pri_ape.like(patron),
                Cuenta.cu_seg_ape.like(patron),
                Cuenta.nom_tercero.like(patron),
            )
        )
    if codigo:
        conds.append(cast(Cuenta.cu_cod, String).like(f"%{codigo.strip()}%"))
    if tercero:
        conds.append(Cuenta.tercero.like(f"%{tercero.strip()}%"))
    if nom_tercero:
        conds.append(Cuenta.nom_tercero.like(f"%{nom_tercero.strip()}%"))

    consulta = select(Cuenta)
    if conds:
        consulta = consulta.where(and_(*conds))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Cuenta.cu_num_id.asc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return CuentasPaginaOutput(
        items=[CuentaOutput.model_validate(f) for f in filas],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


@app.get(f"{settings.api_prefix}/cuentas/tercero/{{numero_identificacion}}")
def consultar_cuenta_tercero(
    numero_identificacion: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_menu_access("/cuenta_cr.faces")),
):
    """Proxy hacia WebApiComfamiliar (api/Facturacion/Tercero/{id}) con caché local."""
    limpio = limpiar_identificacion(numero_identificacion)
    if not limpio:
        raise HTTPException(status_code=400, detail="El número de identificación es requerido y debe tener entre 4 y 20 caracteres alfanuméricos.")
    if not settings.external_api_base_url or not settings.external_api_auth_url or not settings.external_api_username:
        return {
            "result": -1,
            "message": "Servicio externo no configurado. Defina EXTERNAL_API_BASE_URL, EXTERNAL_API_AUTH_URL y EXTERNAL_API_USERNAME en backend/.env.",
            "data": None,
        }
    _status_http, body = consultar_tercero_externo(limpio)
    data = normalizar_tercero(body.get("data")) if isinstance(body, dict) else None
    if body.get("result") == 1 and data:
        _guardar_cuenta(db, data, user.id)
    return {
        "result": body.get("result", -1),
        "message": body.get("message", ""),
        "data": data,
    }
