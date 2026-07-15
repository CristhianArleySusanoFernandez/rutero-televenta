"""
Simulador de la app Android para probar el WebSocket sin tener el teléfono real.

Sigue el contrato docs/contrato_websocket.md v1.0:
  - Envía 'registro' al conectar
  - Envía 'disponible' cuando está listo
  - Responde a 'llamar' con OFFHOOK + IDLE (después de DURACION_LLAMADA_SEG)
  - Envía 'salud' cada 30s

Uso:
    py tools/simulador_telefono.py [opciones]

Opciones:
    --id      telefono_id a usar          (default: "simulador_01")
    --host    host del servidor           (default: "localhost")
    --port    puerto del servidor         (default: 8000)
    --dur     duración simulada en seg.   (default: 5)
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone

# ── Colores ANSI para la consola ──────────────────────────────
C_RESET  = "\033[0m"
C_CYAN   = "\033[96m"   # mensajes que ENVIAMOS
C_GREEN  = "\033[92m"   # mensajes que RECIBIMOS
C_YELLOW = "\033[93m"   # eventos internos / info
C_RED    = "\033[91m"   # errores / advertencias
C_GRAY   = "\033[90m"   # separadores / timestamps


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _log(color: str, prefijo: str, msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{C_GRAY}[{ts}]{C_RESET} {color}{prefijo}{C_RESET} {msg}")


def _log_envio(payload: dict) -> None:
    _log(C_CYAN, "▲ ENVÍO  ", json.dumps(payload, ensure_ascii=False))


def _log_recibo(payload: dict) -> None:
    _log(C_GREEN, "▼ RECIBO ", json.dumps(payload, ensure_ascii=False))


def _log_info(msg: str) -> None:
    _log(C_YELLOW, "● INFO   ", msg)


def _log_error(msg: str) -> None:
    _log(C_RED, "✖ ERROR  ", msg)


def _log_sep() -> None:
    print(f"{C_GRAY}{'─' * 70}{C_RESET}")


# ── Simulador principal ───────────────────────────────────────

async def simular(telefono_id: str, host: str, port: int, dur_seg: int) -> None:
    try:
        import websockets
    except ImportError:
        _log_error("Falta la librería 'websockets'. Instálala con:  py -m pip install websockets")
        sys.exit(1)

    uri = f"ws://{host}:{port}/ws/telefono"
    _log_info(f"Conectando a {uri} como telefono_id='{telefono_id}'")
    _log_sep()

    try:
        async with websockets.connect(uri) as ws:
            _log_info("Conexión WebSocket establecida.")

            # Cola interna para que el listener le pase órdenes al loop principal
            cola_ordenes: asyncio.Queue[dict] = asyncio.Queue()

            # ── Tarea 1: escuchar mensajes del servidor ────────────
            async def escuchar():
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        _log_error(f"Mensaje no JSON recibido: {raw[:120]}")
                        continue
                    _log_recibo(msg)
                    tipo = msg.get("tipo")
                    if tipo in ("llamar", "colgar"):
                        await cola_ordenes.put(msg)

            tarea_escucha = asyncio.create_task(escuchar())

            # ── Paso 1: registro ───────────────────────────────────
            _log_sep()
            _log_info("Paso 1 — enviando 'registro'")
            registro = {
                "tipo": "registro",
                "telefono_id": telefono_id,
                "ts": _ts(),
                "modelo": "Simulador Python",
                "android_version": "Simulado",
                "sdk_int": 34,
                "bateria": 100,
                "app_version": "sim-1.0",
            }
            await ws.send(json.dumps(registro))
            _log_envio(registro)

            await asyncio.sleep(0.3)

            # ── Paso 2: disponible ─────────────────────────────────
            _log_sep()
            _log_info("Paso 2 — enviando 'disponible'")
            disponible = {
                "tipo": "disponible",
                "telefono_id": telefono_id,
                "ts": _ts(),
            }
            await ws.send(json.dumps(disponible))
            _log_envio(disponible)

            _log_sep()
            _log_info(
                f"Listo. Esperando órdenes del servidor...\n"
                f"         Dispara una llamada con:\n"
                f"           curl -X POST http://{host}:{port}/telefono/{telefono_id}/llamar"
                f" -H \"Content-Type: application/json\""
                f" -d '{{\"numero\":\"+57300000000\",\"nombre_contacto\":\"Cliente Prueba\"}}'"
            )
            _log_sep()

            # ── Loop principal: heartbeat + espera de órdenes ──────
            bateria = 100
            segundos_sin_salud = 0

            while True:
                try:
                    orden = await asyncio.wait_for(cola_ordenes.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    segundos_sin_salud += 1
                    if segundos_sin_salud >= 30:
                        # ── Heartbeat salud ────────────────────────
                        bateria = max(0, bateria - 1)
                        salud = {
                            "tipo": "salud",
                            "telefono_id": telefono_id,
                            "ts": _ts(),
                            "bateria": bateria,
                            "cargando": False,
                            "en_llamada": False,
                        }
                        await ws.send(json.dumps(salud))
                        _log_envio(salud)
                        segundos_sin_salud = 0
                    continue

                # ── Procesar orden recibida ────────────────────────
                tipo_orden = orden.get("tipo")

                if tipo_orden == "llamar":
                    llamada_id = orden.get("llamada_id", "???")
                    numero     = orden.get("numero", "???")
                    nombre     = orden.get("nombre_contacto") or ""

                    _log_sep()
                    _log_info(
                        f"Orden 'llamar' recibida — marcando {numero}"
                        + (f" ({nombre})" if nombre else "")
                    )

                    # OFFHOOK — empezó a marcar
                    await asyncio.sleep(0.5)
                    offhook = {
                        "tipo": "estado_llamada",
                        "telefono_id": telefono_id,
                        "ts": _ts(),
                        "llamada_id": llamada_id,
                        "estado": "OFFHOOK",
                        "duracion_seg": None,
                    }
                    await ws.send(json.dumps(offhook))
                    _log_envio(offhook)

                    _log_info(f"Simulando llamada de {dur_seg}s...")
                    await asyncio.sleep(dur_seg)

                    # IDLE — llamada terminó
                    idle = {
                        "tipo": "estado_llamada",
                        "telefono_id": telefono_id,
                        "ts": _ts(),
                        "llamada_id": llamada_id,
                        "estado": "IDLE",
                        "duracion_seg": dur_seg,
                    }
                    await ws.send(json.dumps(idle))
                    _log_envio(idle)

                    _log_sep()
                    _log_info("Llamada finalizada. Enviando 'disponible' de nuevo.")

                    # disponible de nuevo
                    disponible2 = {
                        "tipo": "disponible",
                        "telefono_id": telefono_id,
                        "ts": _ts(),
                    }
                    await ws.send(json.dumps(disponible2))
                    _log_envio(disponible2)
                    _log_sep()
                    _log_info("Esperando siguiente orden...")

                elif tipo_orden == "colgar":
                    _log_sep()
                    _log_info(
                        f"Orden 'colgar' recibida — llamada_id={orden.get('llamada_id')}\n"
                        "         (simulador ignora colgar activamente; Android lo gestionaría con TelecomManager)"
                    )

                else:
                    _log_info(f"Tipo de orden desconocido '{tipo_orden}' — ignorado (contrato §1)")

    except (ConnectionRefusedError, OSError) as e:
        _log_error(f"No se pudo conectar a {uri}: {e}")
        _log_error("¿Está corriendo el servidor?  py -m uvicorn src.api.main:app --reload")
        sys.exit(1)
    except KeyboardInterrupt:
        _log_sep()
        _log_info("Simulador detenido por el usuario (Ctrl+C).")


# ── Entrada ───────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simulador de app Android para el WebSocket de Televenta"
    )
    parser.add_argument("--id",   default="simulador_01",  help="telefono_id (default: simulador_01)")
    parser.add_argument("--host", default="localhost",      help="Host del servidor (default: localhost)")
    parser.add_argument("--port", default=8000, type=int,  help="Puerto del servidor (default: 8000)")
    parser.add_argument("--dur",  default=5,    type=int,  help="Duración simulada de llamada en segundos (default: 5)")
    args = parser.parse_args()

    asyncio.run(simular(args.id, args.host, args.port, args.dur))
