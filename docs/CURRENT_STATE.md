# CURRENT_STATE.md

> Estado del proyecto verificable ÚNICAMENTE desde el código actual del repositorio, a fecha de esta inspección. No confundir con suposiciones de conversación.
>
> Etiquetas usadas: **VERIFICADO EN CÓDIGO** / **NO DETERMINADO DESDE EL CÓDIGO** / **PENDIENTE DE VERIFICACIÓN EN PRODUCCIÓN**

## Repositorio
- Branch: `main` — VERIFICADO EN CÓDIGO
- Último commit de código: `0b304f5` "feat: franja horaria preferida por cliente" — VERIFICADO EN CÓDIGO
- Historial desde el checkpoint anterior (`c56ade3`), en orden: `e41a3a0` (carga por lotes) → `701b9fd` (asesor/fecha Colombia en novedades) → `75dc068` (dashboard + buscador/anulación + WhatsApp/navegación) → `1359306` (columnas Excel `Novedades`/`ASESOR`) → `c15bf55` (editar cliente + exportar rutero completo) → `0b304f5` (franja horaria). — VERIFICADO EN CÓDIGO (`git log c56ade3..HEAD --stat`)
- Estos 6 commits ya están en `origin/main` al momento de esta inspección (`git log origin/main..main` vacío) — VERIFICADO EN CÓDIGO.
- `launcher.py` tiene una única línea en blanco sin commitear desde hace varias tareas (cambio trivial, no funcional) — VERIFICADO EN CÓDIGO (`git status`). Ningún otro archivo de código está pendiente; solo `docs/` se está actualizando en esta tarea.

## Arquitectura actual
Hexagonal: `domain` (entidades, puertos, value objects, servicios puros) ← `application/use_cases` (orquestación) ← `infrastructure/adapters` (Supabase, Excel, WebSocket) ← `api` (routers, composition root en `src/api/dependencies.py`). Detalle completo en `ARCHITECTURE.md`. — VERIFICADO EN CÓDIGO

## Funcionalidades implementadas (VERIFICADO EN CÓDIGO)
- Selección/creación de asesor por cookie, sin contraseña.
- Configuración de teléfono vinculado al asesor.
- Carga de rutero semanal desde Excel, con reparto automático por día de visita.
- Cola de llamadas con priorización de reagendados vencidos y pendientes por posición.
- Reintentos automáticos ante "no contesta" (hasta 2 intentos).
- Reagendamiento con minutos de espera configurables.
- Saltar cliente (marca `no_contesto` + novedad automática).
- Registro de estado final (`contesto` / `no_contesto`) y corrección posterior de ese resultado.
- Registro de novedades con tipo e historial por cliente.
- Notas permanentes por cliente (independientes del rutero).
- Eliminación de rutero de un día específico (con resumen previo de cuántos clientes ya fueron llamados).
- Exportación de reporte Excel del día (excepciones: novedad/saltado/no contestó, 6 columnas).
- Empaquetado local vía PyInstaller (`.exe`) y configuración de despliegue en Render.
- Carga de rutero por lotes (`upsert`/upsert masivo por día en vez de fila por fila): pasó de ~1240 peticiones a Supabase a 18 para un rutero de 620 clientes/6 días. Los métodos `upsert()` (individual) y `crear_llamada()` (individual) siguen existiendo en los adapters pero ya no tienen ningún llamador (ver "Deuda técnica" abajo).
- Dashboard de novedades por asesor con selector de período (día/semana/mes): total, conteo por tipo, excluye anuladas y correcciones de resultado (prefijo `[Corrección`), aviso de novedades históricas sin asesor asignado.
- Buscador de clientes por nombre/razón social/teléfono, fuera de la cola, con historial de novedades del cliente filtrado por el asesor de la sesión (BR-012) y anulación (soft-delete) de novedades propias con motivo obligatorio.
- Aviso por WhatsApp (`wa.me`, sin API ni backend) para avisar al cliente que se le llamó y no se pudo contactar, con mensaje pre-escrito; se muestra solo si el teléfono normaliza a un móvil colombiano válido.
- Enlace de "Inicio" en la barra de navegación, visible en todas las pantallas.
- Captura de las columnas `Novedades` (→ `clientes.novedad_excel`) y `ASESOR` (→ `clientes.asesor_campo`, por fila) del Excel, antes descartadas; normalización de encabezados insensible a mayúsculas/espacios en el parser.
- Edición de cliente (nombre, razón social, dirección, barrio, ciudad, teléfono, documento) desde el buscador y desde la vista enfocada (deep link); `cod_cliente` y `dias_visita` quedan de solo lectura.
- Exportación del rutero completo de la semana (12 columnas originales del Excel, deduplicado por cliente, `Cod Cliente` forzado a formato texto para conservar ceros a la izquierda), distinta del reporte de excepciones existente.
- Franja horaria preferida por cliente (`clientes.franja_desde`/`franja_hasta`, permanente, editable/borrable desde la vista enfocada sin avanzar la cola y desde la ficha del buscador): preferencia blanda que solo muestra un aviso si la hora actual (Colombia) está fuera de ella — no reordena ni bloquea ninguna llamada.

## Endpoints existentes (VERIFICADO EN CÓDIGO)
Ver lista completa y exacta (método, ruta, archivo:línea) en `ARCHITECTURE.md`, sección "Endpoints". Resumen por router:
- `main.py`: `GET /`
- `asesor.py` (`/asesor`): seleccionar (GET/POST), salir (POST), teléfono (GET/POST)
- `cola.py` (`/cola`): vista-enfocada, saltar, llamar, no-contesto, reagendar
- `llamadas.py` (`/llamadas`): estado (PATCH), novedad (POST), corregir-resultado (POST), corregir-form (GET), novedad-form (GET), historial (GET)
- `notas.py` (`/notas`): listar (GET), crear (POST), eliminar (DELETE)
- `reportes.py` (`/reportes`): exportar (GET) — reporte de excepciones, 6 columnas
- `rutero.py` (`/rutero`): cargar (POST), hoy (GET), stats (GET), resumen (GET), **exportar-completo (GET, nuevo)**, eliminar (DELETE)
- `telefono.py`: `/ws/telefono` (WS), `/telefono/estado`, `/telefono/{id}/estado`, `/telefono/{id}/llamar`, `/telefono/{id}/colgar`
- `dashboard.py` (`/dashboard`, **nuevo**): novedades (GET, `?periodo=dia|semana|mes&fecha=`)
- `clientes.py` (`/clientes`, **nuevo**): buscador (GET, página), buscar (GET, parcial), `{id}/historial` (GET), `{id}/ficha` (GET), `{id}` (POST, editar datos), `{id}/franja` (POST, franja horaria), `novedades/{id}/anular` (POST)

## Estructura de BD conocida desde schema.sql (VERIFICADO EN CÓDIGO, contenido del archivo `database/schema.sql`)
Tablas: `clientes`, `rutero_dias` (`UNIQUE(fecha, asesor)`), `rutero_clientes` (`UNIQUE(rutero_dia_id, cliente_id)`, `estado` con CHECK, columnas `llamada_id`/`duracion_seg` agregadas en `database/migration_llamada_telefono.sql`), `novedades` (FK `rutero_cliente_id`: ver precisión abajo; FK `cliente_id` como `ON DELETE CASCADE`), `notas_cliente` (RLS deshabilitada, ligada solo a `cliente_id`), `asesores` (`nombre` PK, `telefono_id`).

**Columnas nuevas desde el checkpoint anterior, con migración ejecutada y verificada por el usuario en Supabase de producción:**
- `novedades`: `asesor TEXT`, `anulada BOOLEAN NOT NULL DEFAULT false`, `anulada_motivo TEXT`, más índice `idx_novedades_asesor_fecha (asesor, fecha)` — `database/migration_novedades_dashboard.sql`.
- `clientes`: `novedad_excel TEXT`, `asesor_campo TEXT` — `database/migration_clientes_columnas_excel.sql`.
- `clientes`: `franja_desde TIME`, `franja_hasta TIME` — `database/migration_clientes_franja_horaria.sql`.
Las tres migraciones son aditivas (`ADD COLUMN IF NOT EXISTS`), sin backfill donde el dato no existía previamente, y `schema.sql` quedó actualizado en la misma sección para que una instalación nueva incluya estas columnas desde el principio.

- El archivo `schema.sql` declara inicialmente la FK `novedades.rutero_cliente_id` con `ON DELETE CASCADE` (`database/schema.sql:50`, dentro del `CREATE TABLE IF NOT EXISTS novedades`). Más adelante, en el mismo archivo (`database/schema.sql:144-146`), esa constraint se elimina (`DROP CONSTRAINT IF EXISTS novedades_rutero_cliente_id_fkey`) y se recrea con `ON DELETE SET NULL`. El estado final que define el script **ejecutado completo y en orden** es `ON DELETE SET NULL` — VERIFICADO EN CÓDIGO.
- **Que ese estado final (SET NULL) esté efectivamente aplicado en la instancia real de Supabase de producción ya NO es un pendiente: el usuario confirmó haberlo verificado directamente en producción** (verificación reportada por el usuario, no reproducida por Claude Code en esta sesión). BR-014 y DEC-011 se actualizan en consecuencia.

## Flujo de llamadas (VERIFICADO EN CÓDIGO)
1. `POST /cola/llamar` resuelve el `telefono_id` vinculado al asesor de la sesión (`cola.py:138`).
2. `OrdenarLlamadaCliente` genera `llamada_id` (UUID), lo persiste en `rutero_clientes.llamada_id` antes de enviar la orden.
3. `WebSocketTelefonoGateway.ordenar_llamada` envía `{"tipo":"llamar",...}` por WS al teléfono conectado.
4. El teléfono reporta `OFFHOOK` y luego `IDLE` (con `duracion_seg`); en `IDLE`, `RegistrarFinLlamada` guarda la duración.

## Cola (VERIFICADO EN CÓDIGO)
Prioriza reagendados vencidos (`reagendado_para <= ahora`) y luego pendientes/reintentos por `posicion_cola` ascendente. "Cola terminada" quiere decir: no hay pendientes, no hay reintentos pendientes, y no hay reagendados sin vencer.

## Reintentos (VERIFICADO EN CÓDIGO)
1er "no contesta" → `reintento_pendiente`, se reinserta ~4 posiciones adelante en la cola. 2do "no contesta" → `no_contesto` definitivo (ya no reintenta).

## Reagendamiento (VERIFICADO EN CÓDIGO)
`POST /cola/reagendar` marca `estado=reagendado` y `reagendado_para = ahora + minutos` (minutos definidos por la asesora).

## Novedades (VERIFICADO EN CÓDIGO)
Tipos definidos en `TipoNovedad` (8 valores en español, ej. `"Otro (ver observación)"`). Se registran vía `POST /llamadas/{id}/novedad` y también automáticamente al saltar un cliente. Se consultan por cliente vía `GET /llamadas/{cliente_id}/historial`.

## Notas (VERIFICADO EN CÓDIGO)
`notas_cliente` está ligada solo a `cliente_id` (no a `rutero_cliente_id` ni `rutero_dia_id`), por lo tanto no se ve afectada al eliminar un rutero. CRUD vía `/notas`.

## Multi-asesor (VERIFICADO EN CÓDIGO)
Identidad por cookie `asesor` (httponly, sin contraseña). Middleware global exige la cookie salvo en rutas `/asesor*`, `/ws*`, `/static*`. Teléfono vinculado al asesor vía tabla `asesores.telefono_id`. Todo el rutero/cola/stats se filtra por `(fecha, asesor)`.

## Excel (VERIFICADO EN CÓDIGO)
Columnas esperadas (12, todas ya capturadas): `Usuario, ASESOR, Cod Cliente, Documento, Cliente, Razon social, Direccion, Barrio, Ciudad, Dias Visita, Telefono, Novedades`. El parser (`excel_rutero_parser.py`) normaliza encabezados (insensible a mayúsculas y espacios sobrantes) antes de mapear, así `ASESOR`/`Asesor`/`asesor` calzan igual. `ASESOR` se lee por fila (→ `clientes.asesor_campo`, informativo, no determina el dueño del rutero, ver BR-016); `Novedades` se persiste en `clientes.novedad_excel` (sin relación con la tabla `novedades` del sistema — homónimos). El archivo trae toda la semana; `parsear_dia_visita` (`src/domain/servicios/dia_visita.py`) determina el día desde los últimos 2 caracteres del código (tolerante a espacios y prefijos SS/Q/M). Clientes sin día válido se incluyen en todos los días de esa semana, marcados con badge "Sin día definido". Carga por lotes: `upsert_lote()` (merge por `cod_cliente`, un upsert por día) y `crear_llamadas_lote()` (`ignore_duplicates=True`, preserva progreso si se recarga el mismo rutero) — ver "Carga por lotes" en `ARCHITECTURE.md`.
La política de conflicto en cada carga es "el Excel manda": el upsert de `clientes` sobrescribe con lo que traiga el archivo cualquier columna que `_to_row()` incluya. Los campos editables desde la app (nombre, dirección, etc.) están en `_to_row()` y por tanto se pierden si se recarga un Excel con el dato viejo; `franja_desde`/`franja_hasta` se dejaron deliberadamente FUERA de `_to_row()` para que sobrevivan a cualquier recarga (no vienen del Excel).

## Frontend (VERIFICADO EN CÓDIGO)
HTMX para filtros/notas/formularios parciales; JS inline maneja el modo cola, polling de estado del teléfono (10s), auto-refresco de la pantalla de espera de reagendados (30s), y swaps manuales con `htmx.process()`. Tailwind CSS compilado localmente (sin CDN), htmx.js servido localmente desde `/static`.

## Android / WebSocket (según documentación existente en el repositorio: `docs/contrato_websocket.md`)
Protocolo JSON v1.0 sobre WebSocket. Mensajes teléfono→servidor: `registro`, `disponible`, `estado_llamada` (OFFHOOK/IDLE), `salud` (heartbeat 30s). Mensajes servidor→teléfono: `llamar`, `colgar`. — VERIFICADO EN CÓDIGO (contrato documentado) / la implementación de la app Android en sí **NO ESTÁ EN ESTE REPOSITORIO** — NO DETERMINADO DESDE EL CÓDIGO.

## Configuración (VERIFICADO EN CÓDIGO)
Variables leídas realmente por `src/config.py`: `SUPABASE_URL`, `SUPABASE_KEY`, `APP_HOST`, `APP_PORT`. `.env.example` también declara `TELEFONO_ID`, pero no se encontró ningún uso de esa variable en el código Python — NO DETERMINADO DESDE EL CÓDIGO su propósito actual real (posible vestigio de un diseño anterior).

## Tests
**Sigue sin existir ningún test automatizado.** No hay carpeta `tests/` ni archivos `test_*.py`/`*_test.py` propios del proyecto — VERIFICADO EN CÓDIGO (ausencia confirmada, reconfirmado tras todo el trabajo de este checkpoint). Toda la verificación de las funcionalidades nuevas descritas en este documento se hizo manualmente (ejecución de scripts puntuales durante el desarrollo y pruebas del usuario contra la aplicación real), no mediante una suite de tests que perdure en el repositorio.

## Deployment
- **Producción actual: Render.** El servicio despliega `uvicorn src.api.main:app` según `render.yaml`. — Esto es una afirmación operativa proporcionada por el usuario en esta conversación, no verificable únicamente desde el contenido de `render.yaml` (el archivo confirma que Render *está configurado como opción de deploy*, pero no que sea el que está corriendo ahora mismo). Se registra explícitamente por instrucción directa del usuario:
  - **Producción actualmente utiliza Render.** — declarado por el usuario, no verificable desde el código por sí solo.
  - **El PC accede mediante `rutero-televenta.onrender.com`.** — declarado por el usuario, no verificable desde el código.
  - **Android utiliza el mismo dominio.** — declarado por el usuario, no verificable desde el código.
  - Esto implica que el modelo de telefonía por WiFi local descrito en `docs/contrato_websocket.md` (pensado para `launcher.py` + IP local) **no sería el que está en uso actualmente**, sino que Android se conectaría al WebSocket a través del dominio de Render. Esto es una inferencia razonable a partir de lo declarado por el usuario, pero **PENDIENTE DE VERIFICACIÓN EN PRODUCCIÓN** contra la configuración real de la app Android.
- **`launcher.spec`/`launcher.py` (modo local/.exe)**: existe en el repositorio y es funcional como capacidad, pero no es el despliegue de producción actual (ver `ARCHITECTURE.md`). — VERIFICADO EN CÓDIGO que el modo existe; NO es producción según indicación del usuario.
- **El estado final `ON DELETE SET NULL` que el script de `schema.sql` deja en `novedades.rutero_cliente_id` (ver sección de Base de Datos arriba) fue verificado por el usuario directamente en producción.** Ya no es un pendiente (ver detalle arriba).

## Deuda técnica detectada (NO resuelta)
Registrada aquí a partir de este checkpoint; ninguno de estos puntos se ha corregido todavía.

- **Código muerto tras la carga por lotes**: `ClienteRepository.upsert()` (individual) y `LlamadaRepository.crear_llamada()` (individual) siguen declarados en puertos y adapters, pero `cargar_rutero.py` usa exclusivamente `upsert_lote()`/`crear_llamadas_lote()` desde el cambio a carga por lotes. Grep en `src/application` y `src/api` confirma cero llamadores de las versiones individuales — VERIFICADO EN CÓDIGO.
- **`posicion_cola` sin constraint `UNIQUE`**: solo existe un índice compuesto no-único `idx_rutero_clientes_cola (rutero_dia_id, posicion_cola)` (`database/schema.sql:113`). La reinserción de BR-002 (`registrar_no_contesta_con_reintento`) calcula la nueva posición como `posicion_cola + 1` del cliente encontrado más adelante, sin desplazar el resto de filas — puede producir empates de `posicion_cola` entre dos `rutero_clientes` del mismo día. No se ha observado que esto rompa el orden de la cola (que solo pide "el de menor posición"), pero el dato no es único por diseño.
- **Columnas de búsqueda de `clientes` sin índice**: `buscar()` (`SupabaseClienteRepository`) hace `.ilike()` sobre `nombre`, `razon_social` y `telefono`, ninguna de las tres indexada. Aceptable con el volumen actual (cientos de clientes); un crecimiento a miles de registros lo volvería lento.
- **Motivo de anulación de novedad pedido con `prompt()` del navegador** (`buscador_clientes.html:126`), no con un modal propio de la interfaz — funcional pero visualmente inconsistente con el resto de la app.
- **`get_llamadas_del_dia` trae novedades de todas las asesoras y descarta en Python**: la consulta de novedades (`supabase_llamada_repository.py`, dentro de `get_llamadas_del_dia`) filtra solo por `fecha`, no por `asesor`; el filtrado real ocurre después, en Python, al indexar por `rutero_cliente_id` (que sí pertenece exclusivamente al rutero del asesor actual). Es una ineficiencia (trae más filas de las necesarias), **no una fuga de datos**: ninguna novedad ajena llega a mostrarse, porque el cruce final por `rc_id` propio la descarta.
- **10 clientes de prueba (`900000001`–`900000010`) dentro del rutero real de producción** — reportado por el usuario; no verificable desde este repositorio (son datos en Supabase, no código).
- **La columna `Usuario` puede quedar mezclada al exportar el rutero completo** si se cargaron ruteros de la misma semana con distinto `usuario_id`: `ExportarRuteroExcel` toma el primer `usuario_id` no vacío que encuentra entre los clientes deduplicados y lo usa para todas las filas y el nombre del archivo — no hay lógica que detecte o advierta sobre una mezcla.
