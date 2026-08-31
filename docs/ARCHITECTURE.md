# ARCHITECTURE.md

> Arquitectura REAL actual del proyecto, tal como existe en el código hoy. No es una propuesta de arquitectura futura.

## Capas

### `src/domain/`
Sin dependencias externas.
- `entities/`: `Cliente`, `Llamada`, `Novedad`, `NotaCliente`, `SesionTelefono` (dataclasses).
- `ports/`: interfaces ABC — `LlamadaRepository`, `ClienteRepository`, `NotaClienteRepository`, `AsesorRepository`, `RuteroParser`, `TelefonoGateway`.
- `value_objects/`: `EstadoLlamada`, `TipoNovedad` (Enums `str`).
- `servicios/dia_visita.py`: funciones puras (`parsear_dia_visita`, `fecha_del_dia_en_semana`), sin estado ni I/O.
- `servicios/fecha_colombia.py`: `hoy_colombia()` (fecha) y `ahora_colombia()` (datetime), ambas en zona `America/Bogota` (`ZoneInfo`, con fallback a offset fijo `-5` si no hay tzdata disponible). Puras, sin I/O.
- `servicios/franja_horaria.py`: `esta_fuera_de_franja(franja_desde, franja_hasta, ahora)` — compara horas del reloj (tipo `time`), devuelve `None`/`True`/`False`; cubre franjas que cruzan medianoche. Pura, sin I/O ni dependencia de zona horaria (recibe la hora ya resuelta).
- `servicios/telefono_colombia.py`: `normalizar_telefono_whatsapp(numero)` — deja solo dígitos y antepone `57`; `None` si no resulta un móvil colombiano de 10 dígitos. Pura, sin I/O.

### `src/application/use_cases/`
Depende únicamente de `domain` (importa puertos, entidades, value objects). No conoce FastAPI ni Supabase directamente. 25 archivos en el directorio (24 casos de uso en clase + `calcular_stats_rutero.py`, que son funciones de stats/filtrado, no una clase) — recuento real vía `ls src/application/use_cases/*.py`. Los ya existentes: `CargarRutero`, `ObtenerRuteroDia`, `ObtenerSiguienteCliente`, `ObtenerClienteEspecifico`, `OrdenarLlamadaCliente`, `RegistrarLlamada`, `RegistrarNoContesta`, `CorregirResultado`, `RegistrarNovedad`, `RegistrarFinLlamada`, `EliminarRuteroDia`, `GestionarNotasCliente`, `ExportarReporte`, `ListarAsesores`, `SeleccionarAsesor`, `ObtenerHistorial`, `ObtenerDatosTarjetaCliente`. Nuevos desde el checkpoint anterior: `ObtenerDashboardNovedades`, `BuscarClientes`, `ObtenerHistorialClienteAsesor`, `AnularNovedad`, `EditarCliente`, `ExportarRuteroExcel`, `EditarFranjaHoraria`.

### `src/infrastructure/adapters/`
Implementaciones concretas de los puertos de `domain`:
- `supabase_cliente_repository.py`, `supabase_llamada_repository.py`, `supabase_nota_cliente_repository.py`, `supabase_asesor_repository.py` → implementan los repos usando el cliente Supabase (PostgREST).
- `excel_rutero_parser.py` → implementa `RuteroParser` usando pandas/openpyxl.
- `websocket_telefono_gateway.py` → implementa `TelefonoGateway` sobre WebSocket nativo de FastAPI.
- `src/infrastructure/supabase_client.py` → singleton lazy del cliente Supabase (`create_client(supabase_url, supabase_key)`), credenciales desde `src/config.py` (`pydantic-settings`).

### `src/api/`
Capa de composición y transporte HTTP/WS:
- `main.py` → instancia FastAPI, monta `/static`, registra middleware de identidad de asesor, incluye routers, define `GET /`.
- `dependencies.py` → **composition root**: fábricas `get_*` que arman cada caso de uso con sus adapters concretos, por request (excepto el gateway WS que es singleton de proceso porque mantiene conexiones vivas en memoria).
- `routers/*.py` → 9 routers (`asesor`, `cola`, `llamadas`, `notas`, `reportes`, `rutero`, `telefono`, **`dashboard` (nuevo)**, **`clientes` (nuevo)**), cada uno recibe casos de uso vía `Depends(get_*)`.
- `templates_config.py` → instancia `Jinja2Templates`, registra funciones Jinja globales: `telefono_valido`, `dia_visita_invalido`, `normalizar_telefono_whatsapp`, `link_whatsapp_no_contesto`.
- `templates/` y `templates/partials/` → vistas Jinja2 + HTMX. Nuevas desde el checkpoint anterior: `buscador_clientes.html`, `dashboard_novedades.html`, `partials/resultados_clientes.html`, `partials/historial_cliente_novedades.html`, `partials/ficha_cliente.html`.
- `static/` → CSS de Tailwind compilado localmente y `htmx.min.js`, servidos vía `StaticFiles`.

**Reconstrucción de `tailwind.css` — procedimiento no escrito hasta ahora en ningún documento, y necesario cada vez que se agregan clases Tailwind nuevas a una plantilla:**
El archivo `src/api/static/css/tailwind.css` es un build JIT **purgado**: solo contiene las clases que existían en las plantillas al momento del último build (confirmado repetidas veces durante este checkpoint: clases nuevas como `opacity-60`, `text-[11px]`, `bg-cian-suave` no aparecían en el CSS servido hasta reconstruirlo). No hay `package.json` en el repositorio — `tailwindcss` se instala **temporalmente** para el build y se borra después. Pasos:
1. `npm install --no-save --prefer-offline --no-audit --no-fund tailwindcss@3.4.19` (offline si el paquete ya está en la caché local de npm; si no, requiere red).
2. `npx --no-install tailwindcss -i ./src/api/static/css/input.css -o ./src/api/static/css/tailwind.css --minify`
3. `rm -rf node_modules package-lock.json package.json` — para no dejar artefactos de build en el repositorio (nunca se commitea `node_modules`/`package.json`).
Quien añada una clase Tailwind nueva a cualquier plantilla debe repetir este procedimiento antes de dar la tarea por terminada, o la clase simplemente no existirá en el CSS servido (fallo silencioso: la plantilla renderiza pero sin el estilo).

## Dependencias entre capas
```
api  →  application  →  domain
 │            │
 └─→ infrastructure ←──┘ (implementa los puertos que domain define)
```
`domain` no depende de nadie. `application` depende solo de `domain`. `infrastructure` depende de `domain` (implementa sus puertos) y de librerías externas (Supabase, pandas, WebSocket). `api` depende de todo: arma `application` + `infrastructure` en `dependencies.py` y expone vía HTTP/WS.

## Composition root
`src/api/dependencies.py`. Cada función `get_*` crea una instancia nueva del repo/caso de uso por request, salvo:
- `_telefono_gateway` (`dependencies.py:107`): singleton de proceso, porque mantiene el diccionario de conexiones WebSocket vivas.
- El hook `_on_llamada_finalizada` se cablea sobre el gateway al arrancar la app, conectando el evento `IDLE` del teléfono con `RegistrarFinLlamada`.

## Supabase
Backend de datos: PostgreSQL gestionado por Supabase, accedido vía su API REST (PostgREST) a través de `supabase-py`. No hay acceso a SQL crudo desde el código de la aplicación (no existe función RPC de tipo `exec_sql`). El esquema vive en `database/schema.sql` (idempotente) y `database/migration_llamada_telefono.sql` (migración específica de columnas de telefonía).

## WebSocket
Endpoint `WS /ws/telefono` (`src/api/routers/telefono.py`). Protocolo documentado en `docs/contrato_websocket.md` v1.0: mensajes JSON con campo `tipo` obligatorio. El teléfono Android es cliente WS; el servidor FastAPI es el servidor WS. `WebSocketTelefonoGateway` mantiene el estado de las conexiones en memoria de proceso (no persistido), con un watchdog que limpia sesiones sin heartbeat tras 90s.

## Android
La app Android **no está en este repositorio**. Se comunica con el backend únicamente a través del contrato WebSocket documentado en `docs/contrato_websocket.md`. Cualquier detalle de implementación de la app Android en sí es NO DETERMINADO DESDE EL CÓDIGO de este repositorio.

## Frontend
Jinja2 + HTMX + JS inline + Tailwind CSS compilado localmente (build v3 vía CLI, sin dependencia de CDN en tiempo de ejecución). HTMX se usa para partials específicos (filtros, notas, formularios); buena parte del flujo de la cola de llamadas usa `fetch` + swap manual de HTML (`htmx.process()` tras el swap), no atributos `hx-*` puros.

## Flujo de una llamada completo
1. Asesora en "vista enfocada" pulsa Llamar → `POST /cola/llamar`.
2. `cola.py` resuelve el `telefono_id` vinculado al asesor actual (tabla `asesores`).
3. `OrdenarLlamadaCliente` (caso de uso) obtiene teléfono/nombre del cliente desde el repo (no confía en el navegador), genera `llamada_id` (UUID), persiste esa asociación en `rutero_clientes.llamada_id` **antes** de enviar la orden, y delega en `TelefonoGateway.ordenar_llamada`.
4. `WebSocketTelefonoGateway` valida que la sesión del teléfono esté conectada y disponible, y envía `{"tipo":"llamar",...}` por WS.
5. El teléfono Android marca, y reporta de vuelta `estado_llamada: OFFHOOK` y luego `estado_llamada: IDLE` (con `duracion_seg`) cuando cuelga.
6. Al recibir `IDLE`, el gateway dispara el hook `on_llamada_finalizada`, que ejecuta `RegistrarFinLlamada` → persiste la duración en `rutero_clientes` (búsqueda por `llamada_id`).
7. La asesora, desde la vista enfocada, registra el resultado final (`contesto`/`no_contesto`), una novedad, o reagenda — estos pasos son independientes del ciclo WS y se hacen vía HTTP normal (`/llamadas/...`, `/cola/...`).

## Flujo de datos general
Excel subido → `ExcelRuteroParser` → `CargarRutero` reparte por día → Supabase (`clientes`, `rutero_dias`, `rutero_clientes`) → `ObtenerRuteroDia`/`ObtenerSiguienteCliente` leen de Supabase → HTML renderizado por Jinja2 → navegador. Las acciones de la asesora (llamar, registrar, reagendar, notas, novedades) escriben de vuelta a Supabase vía los repos de `infrastructure`.

**Carga por lotes (`perf: carga de rutero por lotes`, commit `e41a3a0`):** `CargarRutero` ya no hace un `upsert`/`crear_llamada` por cliente dentro de un bucle (patrón N+1). Por cada día de la semana hace UN `upsert_lote()` (merge por `cod_cliente`, sin `ignore_duplicates`, PostgREST devuelve todas las filas insertadas/actualizadas) seguido de UN `crear_llamadas_lote()` (`ignore_duplicates=True`, preserva BR-013). Para un rutero real de 620 clientes/6 días, esto bajó de ~1240 peticiones HTTP a Supabase a 18. Efecto colateral: los métodos individuales `upsert()`/`crear_llamada()` quedaron sin llamadores (ver "Deuda técnica" en `CURRENT_STATE.md`).

## Modos de despliegue existentes en el repositorio

### Render (nube) — **DESPLIEGUE ACTUAL DE PRODUCCIÓN**
- Configurado en `render.yaml`: servicio Python, `pip install -r requirements.txt`, `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`.
- Variables secretas `SUPABASE_URL`/`SUPABASE_KEY` configuradas manualmente en el dashboard de Render (`sync: false`).
- Según indicación directa del usuario (no verificable únicamente desde el código de este repo): producción corre en Render, accesible en `rutero-televenta.onrender.com`, y tanto el PC como el Android acceden por ese mismo dominio.

### Local / `.exe` — capacidad existente, NO es la producción actual
- `launcher.py` + `launcher.spec` (PyInstaller) generan un ejecutable que corre uvicorn localmente, detecta la IP WiFi local del PC y construye la URL WS (`ws://{ip}:8000/ws/telefono`) para que el Android (en la misma red WiFi) se conecte directamente.
- Este modo asume servidor y teléfono en la misma red local — es un modelo de despliegue distinto y no intercambiable automáticamente con el modo Render (en Render, el WS se sirve por el dominio público, no por una IP local).
- Documentado aquí como capacidad presente en el repositorio, no como el entorno de producción vigente.

## Nota sobre esta documentación
No se propone aquí ningún cambio de arquitectura. Este documento describe exclusivamente lo que existe hoy en el código.
