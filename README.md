# Sistema de Gestión de Eventos – Parque Consotá
Starter de desarrollo: FastAPI + SQLAlchemy + MySQL + React + TypeScript + Vite. Instalación directa en Linux, sin Docker.

## Alcance de esta primera versión
- API FastAPI.
- Inicio de sesión local con JWT de acceso.
- Roles básicos `ADMIN` y `EVENTOS`.
- Crear y consultar solicitudes de eventos autenticadas.
- Migraciones Alembic preparadas para añadirse en la siguiente iteración.
- Frontend React responsivo con inicio de sesión y formulario/listado de solicitudes.
- Configuración de ejemplo para systemd y Nginx.

**No es una versión lista para producción.** Antes de ponerla en uso real, Tecnología debe revisar autenticación, HTTPS, política de contraseñas, CSRF si se migra a cookies, registros, respaldos, migraciones y pruebas de seguridad. El frontend inicial conserva el token en `sessionStorage` para facilitar la prueba; para producción se recomienda migrar a cookies `HttpOnly`, `Secure`, `SameSite` y protección CSRF.

## Requisitos
- Linux Ubuntu/Debian administrado por Tecnología.
- Python 3.11 o versión aprobada compatible.
- Node.js LTS y npm para compilar el frontend.
- MySQL existente y autorizado.
- Nginx instalado por Tecnología.
- Git opcional pero recomendado.
- Un dominio interno y certificado TLS confiable para los equipos institucionales.

## Desarrollo local
### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env con una base de datos de desarrollo y una clave JWT segura.
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Documentación API: `http://127.0.0.1:8000/docs`.

### Crear el primer administrador
En otra terminal, dentro de `backend` y con el entorno virtual activo:
```bash
python -m app.create_admin
```
El comando solicita usuario y contraseña de forma interactiva. No usar credenciales de ejemplo en producción.

### Perfiles de acceso y menú por permisos
La barra lateral de menú es responsiva y se construye desde la base de datos según el
perfil (rol) del usuario autenticado. Se apoya en tres tablas:

- `roles`: perfiles de acceso (por ejemplo `ADMIN`, `EVENTOS`).
- `menu_items`: opciones de menú con relación padre/hijo (`parent_id`) para soportar
  submenús de varios niveles (`label`, `icon`, `path`, `order_index`, `is_active`).
- `role_menu`: permisos por perfil y opción (`is_visible`, `can_read`, `can_write`,
  `can_delete`).

`users.role` almacena el nombre del perfil. El endpoint `GET /api/v1/menu` devuelve
solo las opciones visibles para el perfil del usuario, incluyendo los nodos padre
necesarios para llegar a un submenú permitido.

Para crear perfiles, el árbol de menú de ejemplo y sus permisos (idempotente):
```bash
python -m app.seed_menu
```

Endpoints de administración de perfiles (requieren perfil `ADMIN`):
- `GET  /api/v1/perfiles` y `POST /api/v1/perfiles`.
- `GET  /api/v1/perfiles/{id}/permisos` y `PUT /api/v1/perfiles/{id}/permisos`.
- `GET  /api/v1/menu-items` (árbol completo) y `GET /api/v1/usuarios`.
- `PATCH /api/v1/usuarios/{id}/rol` para asignar el perfil a un usuario.

### Consulta de cuentas (terceros) — opción de menú "Cuentas"
La ruta `/cuenta_cr.faces` de la nueva aplicación permite consultar los datos de
un tercero por número de identificación y muestra el resultado en tarjetas:
identificación, titular, código de cuenta MUF y la coincidencia en JDE
(identificación, tercero ABAN8 y nombre), cuando existe.

El servicio externo WebApiComfamiliar (módulo Facturación) solo permite consultar
por número de identificación (`GET api/Facturacion/Tercero/{id}` con Bearer Token).
El backend actúa como proxy, limpia separadores de miles y registra cada consulta
en la tabla `cuentas`. Endpoints:

- `GET /api/v1/cuentas/tercero/{numero_identificacion}` — proxy al servicio externo
  (usado por la página).
- `GET /api/v1/cuentas` — consulta paginada con filtros (`page`, `page_size`,
  `numero_identificacion`, `nombre`, `codigo`, `tercero`, `nom_tercero`),
  disponible como API para futuras pantallas; la página actual no la usa.

Ambos endpoints exigen que el perfil del usuario tenga visible la opción de menú
`/cuenta_cr.faces` (`role_menu.is_visible` y `can_read`).

El servicio externo requiere Bearer Token. El backend lo genera automáticamente
con las credenciales institucionales (`POST /api/login/authenticate`), lo cachea
en memoria hasta 60 segundos antes de su expiración (~2 h según el claim `exp`
del JWT) y lo regenera si el servicio responde 401. La respuesta real llega en
PascalCase (`CuCod`, `CuNumId`, ...); el backend la normaliza al contrato
camelCase documentado antes de devolverla al frontend.

Variables del backend para el servicio externo (valores reales SOLO en `backend/.env`,
que está en `.gitignore` y nunca se sube al repositorio):
```
EXTERNAL_API_BASE_URL=https://webapinet.comfamiliar.com/api
EXTERNAL_API_AUTH_URL=https://webapinet.comfamiliar.com/api/login/authenticate
EXTERNAL_API_USERNAME=USUARIO_INSTITUCIONAL
EXTERNAL_API_PASSWORD=CLAVE_INSTITUCIONAL
EXTERNAL_API_TIMEOUT=15
```
Las credenciales externas viven únicamente en el backend; el navegador nunca las
recibe. No escribir credenciales en el código fuente, en el frontend ni en el
repositorio.

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
El archivo `.env` del frontend debe apuntar a la URL de API del entorno. Para desarrollo, puede ser `http://127.0.0.1:8000/api/v1`.

## Preparación de MySQL
Tecnología debe crear una base de datos y un usuario exclusivos, con privilegios mínimos. Ejemplo que debe adaptarse y ejecutarse por el DBA:
```sql
CREATE DATABASE gestion_eventos
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'eventos_app'@'localhost' IDENTIFIED BY 'REEMPLAZAR_POR_UN_SECRETO_LARGO';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
  ON gestion_eventos.* TO 'eventos_app'@'localhost';
FLUSH PRIVILEGES;
```
Si MySQL está en otro servidor, no usar `localhost`: restringir el origen a la IP del servidor de aplicación y exigir cifrado de conexión cuando corresponda. No abrir MySQL a Internet.

## Variables del backend
Configurar `backend/.env` desde `.env.example`. `DATABASE_URL` debe tener el formato:
`mysql+pymysql://eventos_app:URL_ENCODED_PASSWORD@127.0.0.1:3309/gestion_eventos`
(usar el puerto real del servidor MySQL; en la instalación XAMPP/Consotá es `3309`).
Codificar caracteres especiales de la contraseña para URL. No subir `.env` a Git ni enviarlo por correo.

## Instalación en producción (resumen para Tecnología)
1. Revisar y aprobar el código fuente.
2. Crear usuario Linux de servicio sin inicio de sesión interactivo.
3. Instalar Python, crear el entorno virtual en `/opt/gestion-eventos/backend/.venv`.
4. Instalar dependencias fijadas en `requirements.txt`.
5. Configurar secretos y variables en un archivo protegido, por ejemplo `/etc/gestion-eventos/backend.env`, propiedad `root`, permisos `640`.
6. Crear base de datos y usuario MySQL con privilegios mínimos.
7. Ejecutar pruebas y crear tablas mediante migraciones. Este starter usa `create_all` para facilitar el prototipo; sustituirlo por Alembic antes de producción.
8. Compilar el frontend con `npm ci && npm run build`.
9. Publicar `frontend/dist` en `/var/www/gestion-eventos`.
10. Instalar el archivo `deploy/systemd/gestion-eventos-api.service` adaptando rutas y usuario.
11. Instalar `deploy/nginx/gestion-eventos.conf` y configurar el certificado TLS interno.
12. Validar desde la red/VPN institucional, revisar logs y probar recuperación de backup.

### Comandos de diagnóstico (solo lectura)
```bash
cat /etc/os-release
python3 --version
node --version
npm --version
mysql --version
nginx -v
systemctl status nginx
ss -lnt
```
La ausencia de Nginx en `systemctl` puede significar que no está instalado. La instalación requiere autorización de Tecnología.

### Instalación de paquetes
No ejecutar en producción sin autorización. Tecnología puede usar el gestor aprobado:
```bash
sudo apt update
sudo apt install nginx python3-venv python3-pip
```
Node.js debe instalarse desde la fuente aprobada por la organización y una versión LTS compatible.

## nginx en Windows (pruebas locales)

### Inicio rápido con `iniciar.bat`
En Windows, ejecutar `iniciar.bat` desde la raíz del proyecto. El script es
idempotente: detecta lo que ya corre, inicia lo faltante y valida todo al final:

1. MySQL de XAMPP (puerto 3309): servicio de Windows `mysql` y, si no hay
   permisos, arranque manual con `mysqld`.
2. API FastAPI (8000): uvicorn en su propia ventana; valida `GET /health`
   (200) y un login con credenciales falsas (401 = base de datos accesible).
3. Frontend de desarrollo (5173): `npm run dev` en su propia ventana.
4. nginx (8081): compila el frontend si falta `dist`, sirve el build y valida
   la SPA, la ruta `/cuenta_cr.faces` y el proxy `/health`.
5. Imprime el resumen y abre `http://127.0.0.1:8081`. Con el argumento
   `--auto` omite la pausa y la apertura del navegador (para automatización).

Instalación local ya realizada en este equipo para servir el build del frontend
con el mismo comportamiento de producción (plantilla: `deploy/nginx/gestion-eventos.conf`).

1. Descargar la versión estable de `https://nginx.org/download/` (usada: `nginx-1.26.3.zip`) y extraer en `C:\nginx`.
2. La configuración vive en `C:\nginx\conf\nginx.conf`: sirve `C:/eventos/frontend/dist`,
   envía `/api/` y `/health` a `http://127.0.0.1:8000` y aplica
   `try_files $uri $uri/ /index.html` para que las rutas `.faces` carguen la SPA.
3. Reconstruir el frontend tras cambios: `cd frontend && npm run build`.
4. Administración (desde `C:\nginx`):
   - Probar configuración: `.\nginx.exe -t`
   - Iniciar: `Start-Process -FilePath C:\nginx\nginx.exe -WorkingDirectory C:\nginx`
   - Recargar configuración: `.\nginx.exe -s reload`
   - Detener: `.\nginx.exe -s stop`
5. App local: `http://127.0.0.1:8081` (el puerto 80 lo ocupa un servicio del sistema
   http.sys; liberarlo o cambiar de puerto requiere administrador).
6. Acceso desde la red: cambiar `listen 127.0.0.1:8081;` por `listen 8081;` y, como
   administrador, abrir el firewall:
   `netsh advfirewall firewall add rule name="nginx 8081" dir=in action=allow protocol=TCP localport=8081`
7. Iniciar con Windows (servicio): descargar NSSM (https://nssm.cc/download), y como
   administrador:
   ```
   nssm install nginx C:\nginx\nginx.exe
   nssm set nginx AppDirectory C:\nginx
   nssm start nginx
   ```

La plataforma de producción institucional sigue siendo Linux con systemd y Nginx
(según `deploy/systemd/` y `deploy/nginx/`).

## Endpoints iniciales
- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/solicitudes`
- `GET /api/v1/solicitudes`

## Modelo inicial de solicitud
- cliente/empresa
- documento/NIT (opcional en prototipo)
- contacto
- correo
- teléfono
- nombre del evento
- fecha de inicio y fin
- cantidad estimada de asistentes
- descripción
- estado inicial `REGISTRADA`

Este modelo es el primer paso y deberá ampliarse con espacios, servicios, adjuntos, viabilidad, aprobaciones y formatos institucionales verificados.
