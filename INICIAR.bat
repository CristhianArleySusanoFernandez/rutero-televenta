@echo off
title Rutero Televenta - Distribuciones Santiago De Tunja
cd /d "%~dp0"

echo.
echo  ==============================================================
echo    RUTERO TELEVENTA - Distribuciones Santiago De Tunja S.A.S
echo  ==============================================================
echo.

REM -- 1. Verificar que existe el entorno virtual ----------------
if not exist ".venv\Scripts\activate.bat" (
    echo  [ERROR] No se encontro el entorno virtual .venv
    echo.
    echo  Este PC aun no tiene instalado el sistema. Pasos:
    echo    1. Instalar Python 3.12 o superior desde python.org
    echo       marcando la casilla "Add Python to PATH"
    echo    2. Abrir una terminal en esta carpeta y ejecutar:
    echo         python -m venv .venv
    echo         .venv\Scripts\pip install -r requirements.txt
    echo    3. Volver a hacer doble clic en INICIAR.bat
    echo.
    pause
    exit /b 1
)

REM -- 2. Activar el entorno virtual -----------------------------
call ".venv\Scripts\activate.bat"

REM -- 3. Verificar dependencias instaladas ----------------------
python -c "import uvicorn, fastapi, supabase" >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Faltan librerias por instalar.
    echo.
    echo  Solucion: abrir una terminal en esta carpeta y ejecutar:
    echo      .venv\Scripts\pip install -r requirements.txt
    echo.
    echo  Luego volver a hacer doble clic en INICIAR.bat
    echo.
    pause
    exit /b 1
)

REM -- 4. Verificar archivo de configuracion .env ----------------
if not exist ".env" (
    echo  [ERROR] Falta el archivo de configuracion .env
    echo.
    echo  Ese archivo tiene las claves de conexion a la base de datos.
    echo  Pidale una copia a quien instalo el sistema y pongala en
    echo  esta misma carpeta con el nombre exacto:  .env
    echo.
    pause
    exit /b 1
)

REM -- 5. Detectar la IP local (la que va en la app del telefono)
set "IP_LOCAL="
for /f %%i in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Dhcp | Select-Object -First 1 -ExpandProperty IPAddress) 2>$null"') do set "IP_LOCAL=%%i"

echo  ==============================================================
if defined IP_LOCAL (
    echo    ESCRIBE ESTA DIRECCION EN LA APP DEL TELEFONO:
    echo.
    echo        ws://%IP_LOCAL%:8000/ws/telefono
    echo.
    echo    IP del PC: %IP_LOCAL%
) else (
    echo    No se pudo detectar la IP automaticamente.
    echo    Busquela con el comando:  ipconfig
    echo    fila "Direccion IPv4" del adaptador de Wi-Fi
)
echo  ==============================================================
echo.
echo    El telefono debe estar conectado a la MISMA red WiFi.
echo.
echo    PARA CERRAR EL SISTEMA: presione Ctrl+C en esta ventana
echo    o simplemente cierre la ventana.
echo    Esta ventana muestra la actividad del servidor.
echo    Dejela abierta mientras trabaja.
echo.
echo  --------------------------------------------------------------
echo.

REM -- 6. Abrir el navegador cuando el servidor ya haya subido ---
start /b cmd /c "ping -n 4 127.0.0.1 >nul & start http://localhost:8000"

REM -- 7. Arrancar el servidor (primer plano, muestra el log) ----
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

REM -- Si uvicorn termina por un error, no cerrar la ventana -----
echo.
echo  El servidor se detuvo. Si fue un error, revise los mensajes de arriba.
pause
