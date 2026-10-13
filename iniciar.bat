@echo off
setlocal EnableExtensions
title Gestion de Eventos - Parque Consota

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"
set "NGINX_DIR=C:\nginx"
set "XAMPP_DIR=C:\xampp"
set "P_MYSQL=3309"
set "P_API=8000"
set "P_VITE=5173"
set "P_NGINX=8081"
set "ST_MYSQL=--"
set "ST_API=--"
set "ST_VITE=--"
set "ST_NGINX=--"

echo.
echo   ======================================================
echo     GESTION DE EVENTOS - PARQUE CONSOTA
echo     MySQL %P_MYSQL%  -  API %P_API%  -  Dev %P_VITE%  -  nginx %P_NGINX%
echo   ======================================================
echo.

if not exist "%BACKEND_DIR%\.env" (
    echo   [AVISO] Falta backend\.env: copie .env.example y configurelo.
    echo.
)

echo   [1/5] MySQL - XAMPP (puerto %P_MYSQL%)
call :puerto_up %P_MYSQL%
if errorlevel 1 goto mysql_iniciar
echo         Ya esta en ejecucion.
set "ST_MYSQL=YA"
goto paso2

:mysql_iniciar
echo         Detenido. Iniciando servicio de Windows "mysql"...
net start mysql >nul 2>&1
call :esperar_puerto %P_MYSQL% 20
if errorlevel 1 goto mysql_manual
echo         Iniciado como servicio.
set "ST_MYSQL=OK"
goto paso2

:mysql_manual
echo         Servicio no disponible o sin permisos de administrador.
echo         Iniciando mysqld de XAMPP en modo manual...
start "MySQL XAMPP (%P_MYSQL%)" /min /D "%XAMPP_DIR%" cmd /c "mysql\bin\mysqld.exe --defaults-file=mysql\bin\my.ini --standalone"
call :esperar_puerto %P_MYSQL% 30
if errorlevel 1 goto mysql_falla
echo         Iniciado en modo manual (XAMPP).
set "ST_MYSQL=OK"
goto paso2

:mysql_falla
echo         [FALLA] No fue posible iniciar MySQL.
set "ST_MYSQL=FALLA"

:paso2
echo.
echo   [2/5] API FastAPI (puerto %P_API%)
call :puerto_up %P_API%
if errorlevel 1 goto api_iniciar
echo         Ya esta en ejecucion.
set "ST_API=YA"
goto api_validar

:api_iniciar
echo         Iniciando uvicorn en una ventana nueva...
start "API FastAPI (%P_API%)" /D "%BACKEND_DIR%" cmd /k python -m uvicorn app.main:app --host 127.0.0.1 --port %P_API%
call :esperar_puerto %P_API% 30
if errorlevel 1 goto api_falla

:api_validar
call :http_get "http://127.0.0.1:%P_API%/health" HC
echo         GET /health : HTTP %HC%
if "%HC%"=="200" goto api_login
set "ST_API=FALLA"
goto paso3

:api_login
call :login_test
echo         Login de validacion (credenciales falsas) : HTTP %LOGIN_CODE%
if "%LOGIN_CODE%"=="401" goto api_ok
if "%LOGIN_CODE%"=="500" echo         [AVISO] La API responde 500: revise la conexion a la base de datos.
set "ST_API=FALLA"
goto paso3

:api_ok
echo         Base de datos accesible desde la API (401 esperado).
set "ST_API=OK"
goto paso3

:api_falla
echo         [FALLA] La API no respondio en el puerto %P_API%.
set "ST_API=FALLA"

:paso3
echo.
echo   [3/5] Frontend de desarrollo - Vite (puerto %P_VITE%)
call :puerto_up %P_VITE%
if errorlevel 1 goto vite_iniciar
echo         Ya esta en ejecucion.
set "ST_VITE=YA"
goto paso4

:vite_iniciar
if not exist "%FRONTEND_DIR%\package.json" goto vite_falta
echo         Iniciando npm run dev en una ventana nueva...
if exist "%FRONTEND_DIR%\node_modules" goto vite_arrancar
echo         Instalando dependencias de frontend con npm install...
pushd "%FRONTEND_DIR%"
call npm install
popd

:vite_arrancar
start "Frontend dev Vite (%P_VITE%)" /D "%FRONTEND_DIR%" cmd /k npm run dev
call :esperar_puerto %P_VITE% 40
if errorlevel 1 goto vite_falla
set "ST_VITE=OK"
goto paso4

:vite_falta
echo         [AVISO] No existe frontend\package.json; se omite.
set "ST_VITE=OMITIDO"
goto paso4

:vite_falla
echo         [FALLA] Vite no respondio en el puerto %P_VITE%.
set "ST_VITE=FALLA"

:paso4
echo.
echo   [4/5] nginx - build de produccion (puerto %P_NGINX%)
if not exist "%NGINX_DIR%\nginx.exe" goto nginx_falta
call :puerto_up %P_NGINX%
if errorlevel 1 goto nginx_iniciar
echo         Ya esta en ejecucion.
set "ST_NGINX=YA"
goto nginx_validar

:nginx_iniciar
if exist "%FRONTEND_DIR%\dist\index.html" goto nginx_arrancar
echo         Compilando frontend (npm run build)...
pushd "%FRONTEND_DIR%"
if not exist node_modules call npm install
call npm run build
popd
if not exist "%FRONTEND_DIR%\dist\index.html" goto nginx_falla

:nginx_arrancar
start "nginx (%P_NGINX%)" /min /D "%NGINX_DIR%" nginx.exe
call :esperar_puerto %P_NGINX% 20
if errorlevel 1 goto nginx_falla
echo         nginx iniciado.

:nginx_validar
call :http_get "http://127.0.0.1:%P_NGINX%/" HC2
echo         SPA raiz : HTTP %HC2%
if "%HC2%"=="200" goto nginx_faces
set "ST_NGINX=FALLA"
goto paso5

:nginx_faces
call :http_get "http://127.0.0.1:%P_NGINX%/cuenta_cr.faces" HC3
call :http_get "http://127.0.0.1:%P_NGINX%/health" HC4
echo         /cuenta_cr.faces : HTTP %HC3%   /health via proxy : HTTP %HC4%
if not "%HC3%"=="200" goto nginx_falla2
if not "%HC4%"=="200" goto nginx_falla2
set "ST_NGINX=OK"
goto paso5

:nginx_falla2
set "ST_NGINX=FALLA"
goto paso5

:nginx_falta
echo         [AVISO] nginx no esta instalado en %NGINX_DIR%; se omite.
set "ST_NGINX=OMITIDO"
goto paso5

:nginx_falla
echo         [FALLA] nginx no responde en el puerto %P_NGINX%.
set "ST_NGINX=FALLA"

:paso5
echo.
echo   [5/5] RESUMEN
echo         MySQL XAMPP (%P_MYSQL%)  : %ST_MYSQL%
echo         API FastAPI (%P_API%)    : %ST_API%
echo         Vite dev (%P_VITE%)      : %ST_VITE%
echo         nginx prod (%P_NGINX%)   : %ST_NGINX%
echo.
echo         Aplicacion (produccion local) : http://127.0.0.1:%P_NGINX%
echo         Aplicacion (desarrollo)       : http://127.0.0.1:%P_VITE%
echo         Documentacion API            : http://127.0.0.1:%P_API%/docs
echo.
if "%ST_MYSQL%"=="FALLA" echo   Revise XAMPP MySQL (puerto %P_MYSQL%).
if "%ST_API%"=="FALLA" echo   Revise la ventana de la API y backend\.env.
if "%ST_NGINX%"=="FALLA" echo   Revise C:\nginx\conf\nginx.conf.
if "%ST_VITE%"=="FALLA" echo   Revise la ventana de Vite y frontend\node_modules.

if "%ST_NGINX%"=="OK" (set "ABRIR=http://127.0.0.1:%P_NGINX%") else (set "ABRIR=http://127.0.0.1:%P_VITE%")
if "%~1"=="--auto" goto fin
start "" %ABRIR%
echo   Presione una tecla para cerrar esta ventana...
pause >nul

:fin
endlocal
exit /b 0

:puerto_up
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %~1 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
exit /b

:esperar_puerto
setlocal
set "EP_N=0"
:esperar_puerto_bucle
call :puerto_up %~1
if not errorlevel 1 (endlocal & exit /b 0)
set /a EP_N+=1
if %EP_N% geq %~2 (endlocal & exit /b 1)
ping -n 2 127.0.0.1 >nul
goto esperar_puerto_bucle

:http_get
set "%~2="
for /f %%c in ('curl.exe -s -m 8 -o NUL -w "%%{http_code}" "%~1"') do set "%~2=%%c"
if not defined %~2 set "%~2=000"
exit /b 0

:login_test
set "LOGIN_CODE="
for /f %%c in ('curl.exe -s -m 10 -o NUL -w "%%{http_code}" -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "username=validacion_iniciar_bat" -d "password=validacion" "http://127.0.0.1:%P_API%/api/v1/auth/login"') do set "LOGIN_CODE=%%c"
if not defined LOGIN_CODE set "LOGIN_CODE=000"
exit /b 0
