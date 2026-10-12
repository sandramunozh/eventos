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
`mysql+pymysql://eventos_app:URL_ENCODED_PASSWORD@127.0.0.1:3306/gestion_eventos`
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
