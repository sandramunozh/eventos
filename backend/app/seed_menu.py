"""Sincroniza perfiles (roles) y permisos de menú sobre el esquema existente.

Usa las tablas ya presentes en la base de datos:
    roles(id, name)
    menu_items(id, parent_id, label, icon, path, order_index, is_active)
    role_menu(id, role_id, menu_item_id, is_visible, can_read, can_write, can_delete)

Uso (desde la carpeta backend, con el entorno virtual activo):
    python -m app.seed_menu

Es idempotente: puede ejecutarse varias veces sin duplicar datos.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal
from app.models import Role, MenuItem, RoleMenu

# Estructura usada únicamente cuando la tabla menu_items está vacía.
MENU: list[dict] = [
    {
        "label": "Gestion comercial",
        "icon": "briefcase",
        "hijos": [
            {"label": "Cuentas", "path": "/cuenta_cr.faces"},
            {"label": "Consulta de trabajadores", "path": "/consulta_trabajadores.faces"},
        ],
    },
    {
        "label": "Agenda",
        "icon": "calendar",
        "hijos": [{"label": "Agenda del dia", "path": "/agenda_cr.faces"}],
    },
    {
        "label": "Items",
        "icon": "pencil",
        "hijos": [
            {"label": "Prestadores de servicio", "path": "/prestador_servicios_cr.faces"},
            {"label": "Grupos de items", "path": "/grupo_item.faces"},
            {"label": "Combo alimentacion", "path": "/combo_alimentacion.faces"},
            {"label": "Servicios", "path": "/servicio_cr.faces"},
            {"label": "Items servicio", "path": "/itemservicio_consulta_cr.faces"},
            {"label": "Actividades MUF", "path": "/actividades_muf.faces"},
            {"label": "Programacion Actividades MUF", "path": "/actividades_muf_programacion.faces"},
        ],
    },
    {
        "label": "Proceso de venta",
        "icon": "shopping-cart",
        "hijos": [
            {"label": "Estadistica", "path": "/venta_estadistica.faces"},
            {"label": "Contratos", "path": "/venta_contrato_cr.faces"},
            {"label": "Cotizaciones", "path": "/venta_cr.faces"},
            {"label": "Plan de bienestar", "path": "/plan_bienestar.faces"},
            {"label": "Empresas con plan de bienestar", "path": "/plan_bienestar_cr.faces"},
            {"label": "Orden de servicio interna", "path": "/venta_orden_servicio_interna_cr.faces"},
            {"label": "Reservas de alojamiento", "path": "/consultar_reservas_alojamiento.faces"},
            {"label": "Pasadias y reservas", "path": "/venta_pasadia_cr.faces"},
            {"label": "Consultar disponibilidad ubicaciones/espacios", "path": "/reservas_cr_seleccion_ubicacion.faces"},
            {"label": "Consulta orden de servicio", "path": "/orden_servicio.faces"},
            {"label": "Relac/cons Sin orden", "path": "/relacion_consumo_cr.faces?tccod=2"},
            {"label": "Relac/cons Con orden", "path": "/venta_relacion_consumo_cr.faces"},
            {"label": "Relac/cons Consulta", "path": "/venta_relacion_consumo_cr_informe.faces?filtrarPorCandidato=N"},
            {"label": "Solicitudes sin respuesta", "path": "/solicitudes_sin_respuesta.faces"},
            {"label": "Parametros CRM", "path": "/parametroscrm.faces"},
        ],
    },
    {
        "label": "Agencia de viajes",
        "icon": "plane",
        "hijos": [
            {"label": "Solicitud planes turisticos", "path": "/solicitud_plan_cr.faces"},
            {"label": "Cotizaciones MUF", "path": "/cotizaciones_muf_cr.faces"},
        ],
    },
    {
        "label": "Orden de servicio",
        "icon": "clipboard-list",
        "hijos": [{"label": "Solicitudes sin respuesta", "path": "/solicitudes_sin_respuesta_os.faces"}],
    },
    {
        "label": "Reservas",
        "icon": "book-open",
        "hijos": [
            {"label": "Reservas", "path": "/reservas_cr_seleccion_ubicacion.faces"},
            {"label": "Reserva de salones", "path": "/reservas_salones_capacitacion.faces"},
            {"label": "Calendario de reservas", "path": "/calendario_reservas_proceso_venta.faces"},
            {"label": "Consultar disponibilidad", "path": "/consultar_disponibilidad_ubicacion_cr.faces"},
            {"label": "Informe estadistico", "path": "/reservas_informe_estadistico.faces"},
            {"label": "Relacion espectaculos valores", "path": "/reservas_relacion_espectaculos_valores.faces"},
            {"label": "Notificaciones", "path": "/notificaciones_cr.faces"},
        ],
    },
    {
        "label": "Cartera",
        "icon": "coins",
        "hijos": [
            {"label": "Saldos por cuenta", "path": "/saldoscuenta.faces"},
            {"label": "Saldos cuentas compañia", "path": "/jdesaldoscuentas.faces"},
            {"label": "Lista chequeo aprobacion", "path": "/cartera_chequeo_aprobacion_cr.faces"},
            {"label": "Consulta orden servicio", "path": "/informecarteraordenservicio.faces"},
        ],
    },
    {
        "label": "Informes",
        "icon": "bar-chart",
        "hijos": [
            {"label": "Ejecucion contratos", "path": "/informes_ejecucion_contratos.faces"},
            {"label": "Dashboard", "path": "/dashboardComercial.faces"},
            {"label": "Dashboard Cotizaciones", "path": "/dashboard_cotizaciones.faces"},
            {"label": "Informes de actividades", "path": "/informes_actividades_area.faces"},
            {
                "label": "Movimiento MUF",
                "hijos": [
                    {"label": "Movimiento por cuenta", "path": "/movimientoMufCuentaInforme.faces"},
                    {"label": "Movimiento entre fechas", "path": "/movimiento_muf_cr_entre_fechas_con_cotizaciones.faces"},
                ],
            },
            {"label": "Cotizaciones sin facturar", "path": "/facturacion_consulta_pv_sin_facturar.faces"},
            {"label": "Estadisticos", "path": "/informes_estadisticos_proceso_venta.faces"},
            {"label": "Semaforo", "path": "/semaforo_proceso_venta.faces"},
            {"label": "Agenda visitas", "path": "/informes_visitas_unidad_comercial.faces"},
            {"label": "Programacion eventos", "path": "/programacion_cr_seleccion_ubicacion.faces"},
        ],
    },
    {
        "label": "Configuracion",
        "icon": "wrench",
        "hijos": [
            {"label": "Areas servicio MUF", "path": "/areas_servicio_muf.faces"},
            {"label": "Estado proceso venta", "path": "/estado_proceso_venta_cr.faces"},
            {"label": "Usuario", "path": "/usuario_autenticado.faces"},
            {"label": "Procesos nomina", "path": "/proceso_nomina_cr.faces"},
            {"label": "Ubicacion", "path": "/ubicacion_cr.faces"},
            {"label": "Lista actividades agenda", "path": "/lista_actividades_cr.faces"},
            {"label": "Rangos reserva", "path": "/tbranres_cr.faces"},
            {"label": "Tabla comisiones", "path": "/tablacomisiones.faces"},
            {"label": "Periodo comision", "path": "/periodocomision.faces"},
        ],
    },
    {"label": "Login", "icon": "log-in", "path": "http://sigec.comfamiliar.com/"},
    {"label": "Sec", "icon": "shield", "path": "http://sec.comfamiliar.com"},
]

# Perfiles de ejemplo. ``None`` significa acceso a todo el menú.
# Las claves son nombres de perfil (roles.name) y los valores, las etiquetas
# de las opciones raíz que se conceden (con todos sus descendientes).
ROLE_GRUPOS: dict[str, list[str] | None] = {
    "ADMIN": None,
    "EVENTOS": ["Agenda", "Proceso de venta", "Reservas", "Informes"],
}


def _sincronizar_menu(db: Session, nodos: list[dict], parent_id: int | None = None) -> None:
    for orden, nodo in enumerate(nodos):
        existente = db.scalar(
            select(MenuItem).where(
                MenuItem.label == nodo["label"],
                MenuItem.parent_id == parent_id,
            )
        )
        if existente is None:
            existente = MenuItem(
                label=nodo["label"],
                icon=nodo.get("icon"),
                path=nodo.get("path"),
                order_index=orden,
                parent_id=parent_id,
                is_active=True,
            )
            db.add(existente)
            db.flush()
        else:
            existente.icon = nodo.get("icon")
            existente.path = nodo.get("path")
            existente.order_index = orden
            existente.is_active = True
        if nodo.get("hijos"):
            _sincronizar_menu(db, nodo["hijos"], existente.id)


def _ids_por_grupos(items: list[MenuItem], grupos: list[str]) -> set[int]:
    hijos_por_padre: dict[int | None, list[MenuItem]] = {}
    for item in items:
        hijos_por_padre.setdefault(item.parent_id, []).append(item)

    ids: set[int] = set()

    def recorrer(item: MenuItem) -> None:
        ids.add(item.id)
        for hijo in hijos_por_padre.get(item.id, []):
            recorrer(hijo)

    for grupo in grupos:
        raiz = next((i for i in items if i.parent_id is None and i.label == grupo), None)
        if raiz is not None:
            recorrer(raiz)
    return ids


def _asegurar_perfiles(db: Session, items: list[MenuItem]) -> None:
    todos_ids = {item.id for item in items}
    for nombre, grupos in ROLE_GRUPOS.items():
        rol = db.scalar(select(Role).where(Role.name == nombre))
        if rol is None:
            rol = Role(name=nombre)
            db.add(rol)
            db.flush()
        deseados = todos_ids if grupos is None else _ids_por_grupos(items, grupos)
        existentes = {
            fila.menu_item_id: fila
            for fila in db.scalars(select(RoleMenu).where(RoleMenu.role_id == rol.id)).all()
        }
        for item_id in todos_ids:
            visible = item_id in deseados
            fila = existentes.get(item_id)
            if fila is None:
                db.add(
                    RoleMenu(
                        role_id=rol.id,
                        menu_item_id=item_id,
                        is_visible=visible,
                        can_read=visible,
                        can_write=grupos is None,
                        can_delete=False,
                    )
                )
            else:
                fila.is_visible = visible
                fila.can_read = visible


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        hay_menu = db.scalar(select(MenuItem.id).limit(1)) is not None
        if not hay_menu:
            _sincronizar_menu(db, MENU)
            db.flush()
        items = list(db.scalars(select(MenuItem)).all())
        _asegurar_perfiles(db, items)
        db.commit()
    print("Perfiles, menú y permisos sincronizados correctamente.")


if __name__ == "__main__":
    seed()
