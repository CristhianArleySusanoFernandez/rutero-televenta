"""
Punto de entrada para el ejecutable empaquetado con PyInstaller.
Hace lo mismo que INICIAR.bat: valida el entorno, muestra la IP de red,
abre el navegador y arranca uvicorn en primer plano.
"""
import subprocess
import sys
import threading
import time
import webbrowser

from src.paths import exe_dir

HOST = "0.0.0.0"
PORT = 8000


def detectar_ip_wifi() -> str | None:
    comando = (
        "(Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Dhcp | "
        "Select-Object -First 1 -ExpandProperty IPAddress)"
    )
    try:
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando],
            capture_output=True, text=True, timeout=5,
        )
        ip = resultado.stdout.strip()
        return ip or None
    except Exception:
        return None


def abrir_navegador_diferido() -> None:
    time.sleep(2)
    webbrowser.open(f"http://localhost:{PORT}")


def esperar_enter() -> None:
    try:
        input("Presione ENTER para salir...")
    except EOFError:
        pass


def salir_con_error(mensaje: str) -> None:
    print()
    print(mensaje)
    print()
    esperar_enter()
    sys.exit(1)


def main() -> None:
    base_dir = exe_dir()

    print()
    print(" ==============================================================")
    print("   RUTERO TELEVENTA - Distribuciones Santiago De Tunja S.A.S")
    print(" ==============================================================")
    print()

    env_path = base_dir / ".env"
    if not env_path.exists():
        salir_con_error(
            " [ERROR] Falta el archivo de configuracion .env\n"
            "\n"
            " Ese archivo tiene las claves de conexion a la base de datos.\n"
            " Pidale una copia a quien instalo el sistema y pongala en\n"
            " esta misma carpeta con el nombre exacto:  .env"
        )

    ip_local = detectar_ip_wifi()

    print(" ==============================================================")
    if ip_local:
        print("   ESCRIBE ESTA DIRECCION EN LA APP DEL TELEFONO:")
        print()
        print(f"       ws://{ip_local}:{PORT}/ws/telefono")
        print()
        print(f"   IP del PC: {ip_local}")
    else:
        print("   No se pudo detectar la IP automaticamente.")
        print("   Busquela con el comando:  ipconfig")
        print('   fila "Direccion IPv4" del adaptador de Wi-Fi')
    print(" ==============================================================")
    print()
    print("   El telefono debe estar conectado a la MISMA red WiFi.")
    print()
    print("   PARA CERRAR EL SISTEMA: cierre esta ventana.")
    print("   Esta ventana muestra la actividad del servidor.")
    print("   Dejela abierta mientras trabaja.")
    print()
    print(" --------------------------------------------------------------")
    print()

    # El .env debe existir ANTES de este import: src.config arma Settings()
    # al importarse y falla si faltan SUPABASE_URL/SUPABASE_KEY.
    from src.api.main import app
    import uvicorn

    threading.Thread(target=abrir_navegador_diferido, daemon=True).start()

    try:
        uvicorn.run(app, host=HOST, port=PORT, log_level="info")
    except Exception as e:
        print()
        print(f" El servidor se detuvo con un error: {e}")
        esperar_enter()
        sys.exit(1)

    print()
    print(" El servidor se detuvo.")
    esperar_enter()


if __name__ == "__main__":
    main()
