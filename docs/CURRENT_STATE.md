# CURRENT_STATE.md

> Estado del proyecto verificable ÚNICAMENTE desde el código actual del repositorio, a fecha de esta inspección. No confundir con suposiciones de conversación.
>
> Etiquetas usadas: **VERIFICADO EN CÓDIGO** / **NO DETERMINADO DESDE EL CÓDIGO** / **PENDIENTE DE VERIFICACIÓN EN PRODUCCIÓN**

## Repositorio
- Branch: `main` — VERIFICADO EN CÓDIGO
- Último commit de código: `f7e3b43` "feat: permitir llamar al telefono secundario del cliente" — VERIFICADO EN CÓDIGO
- Historial desde el checkpoint anterior (`c56ade3`), en orden: `e41a3a0` (carga por lotes) → `701b9fd` (asesor/fecha Colombia en novedades) → `75dc068` (dashboard + buscador/anulación + WhatsApp/navegación) → `1359306` (columnas Excel `Novedades`/`ASESOR`) → `c15bf55` (editar cliente + exportar rutero completo) → `0b304f5` (franja horaria) → `02934b3` (docs) → `21819b6` (registro de pedidos) → `5541b43` (formato nuevo de rutero + filtrado por código de asesora) → `d407eee` (campos nuevos del cliente editables) → `f7e3b43` (llamar al teléfono secundario) → *(esta tarea de documentación + los dos commits que consolida: registro automático de correcciones y hoja de correcciones en el reporte, ver `git log --stat` al final de la tarea)*. — VERIFICADO EN CÓDIGO (`git log c56ade3..HEAD --oneline`)
- Los commits hasta `f7e3b43` ya estaban en `origin/main`; los nuevos de esta tarea se crean localmente y **NO se empujan** (instrucción explícita de esta tarea) — VERIFICADO EN CÓDIGO.
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
- Registro de pedidos por cliente (texto libre, sin catálogo de productos): historial de los últimos 3 pedidos visible en la vista enfocada y en la ficha del buscador, señal de inactividad (`semanas_sin_ultima_compra`, umbral 4 semanas) que solo aparece si el cliente tiene al menos un pedido registrado, y sugerencias de texto ya usado (propias primero, luego las más frecuentes del asesor) vía `<datalist>`. Registro inline desde la vista enfocada sin avanzar la cola ni crear novedades ni cambiar el estado del cliente.
- Soporte del formato nuevo de rutero (`ACTUALIZACION_DATOS_TV_*.xlsx`, hoja `Informe`) además del formato antiguo: el parser acepta nombres de columna alternativos (`COD ASESOR`, `Codigo`, `Dias`, `Razon s.`, `NOVEDAD`, más `OBSERVACION`, `DATO A CORREGIR`, `Email.`, `Segmento`, `Telefono2`, nuevos), selecciona automáticamente la hoja correcta, y falla con un error claro si faltan columnas imprescindibles. La carga se filtra por `codigo_asesor` (código de PUESTO, configurable en "Mi código de asesora") para no mezclar los clientes de otra asesora: usa el código configurado, lo autoconfigura si el archivo trae uno solo, o rechaza la carga con mensaje claro en cualquier otro caso.
- Los cinco campos del formato nuevo (`email`, `telefono2`, `segmento`, `observacion_excel`, `dato_a_corregir`) son editables desde la ficha del buscador (con aviso de que el Excel los sobrescribe en la próxima carga) y se muestran en la vista enfocada los relevantes durante la llamada (`observacion_excel`, `novedad_excel`, `telefono2`).
- Llamada al teléfono secundario del cliente (`telefono2`): segundo botón en la vista enfocada, visible solo si el cliente lo tiene, que ordena marcar ese número. El navegador nunca envía un número, solo una etiqueta (`principal`/`secundario`) que el servidor resuelve contra la base de datos igual que el número principal. No cuenta como intento (BR-002 sin cambios), no crea novedades ni cambia el estado del cliente.
- Registro automático de correcciones de datos del cliente (`cambios_cliente`): cada vez que `EditarCliente` guarda cambios, compara campo por campo (normalizado) el valor anterior contra el nuevo y genera una fila por cada campo que realmente cambió (campo en texto legible, valor anterior, valor nuevo, asesor, fecha Colombia). Guardar sin cambios, o con solo espacios de más, no genera ninguna fila. La carga de Excel y `EditarFranjaHoraria` NO generan registros — no son correcciones de la asesora. El registro va en `try/except`: si falla, la edición del cliente se aplica igual (nunca bloquea, se registra solo en el log del servidor). Historial visible, colapsable y con carga diferida, en la ficha del cliente del buscador (`GET /clientes/{id}/cambios`).
- El Excel de `/reportes/exportar` ahora incluye una segunda hoja, "Correcciones solicitadas", con los cambios de la semana (lunes-sábado que contiene la fecha exportada) del asesor de la cookie (BR-012), `Cod Cliente` forzado a texto igual que el rutero completo, y un mensaje explícito si no hay correcciones en el rango en vez de una hoja vacía. La hoja de novedades (título, columnas, contenido) no cambió.

## Endpoints existentes (VERIFICADO EN CÓDIGO)
Ver lista completa y exacta (método, ruta, archivo:línea) en `ARCHITECTURE.md`, sección "Endpoints". Resumen por router:
- `main.py`: `GET /`
- `asesor.py` (`/asesor`): seleccionar (GET/POST), salir (POST), teléfono (GET/POST), código de asesora (GET/POST, nuevo — puesto, no persona)
- `cola.py` (`/cola`): vista-enfocada, saltar, llamar (ahora acepta `numero_a_usar: principal|secundario`), no-contesto, reagendar
- `llamadas.py` (`/llamadas`): estado (PATCH), novedad (POST), corregir-resultado (POST), corregir-form (GET), novedad-form (GET), historial (GET)
- `notas.py` (`/notas`): listar (GET), crear (POST), eliminar (DELETE)
- `reportes.py` (`/reportes`): exportar (GET) — reporte de excepciones (6 columnas, sin cambios) más una segunda hoja "Correcciones solicitadas" (7 columnas, semana lunes-sábado, filtrada por asesor)
- `rutero.py` (`/rutero`): cargar (POST, ahora filtra por `codigo_asesor` en el formato nuevo), hoy (GET), stats (GET), resumen (GET), exportar-completo (GET), eliminar (DELETE)
- `telefono.py`: `/ws/telefono` (WS), `/telefono/estado`, `/telefono/{id}/estado`, `/telefono/{id}/llamar`, `/telefono/{id}/colgar`
- `dashboard.py` (`/dashboard`): novedades (GET, `?periodo=dia|semana|mes&fecha=`)
- `clientes.py` (`/clientes`): buscador (GET, página), buscar (GET, parcial), `{id}/historial` (GET), `{id}/ficha` (GET), `{id}` (POST, editar datos — incluye ahora `email`/`telefono2`/`segmento`/`observacion_excel`/`dato_a_corregir`, y genera registro automático de cambios), `{id}/franja` (POST, franja horaria), `{id}/cambios` (GET, **nuevo** — historial de correcciones), `novedades/{id}/anular` (POST)
- `pedidos.py` (`/pedidos`, **nuevo**): crear (POST), sugerencias (GET, `?cliente_id=`), `{cliente_id}/historial` (GET)

## Estructura de BD conocida desde schema.sql (VERIFICADO EN CÓDIGO, contenido del archivo `database/schema.sql`)
Tablas: `clientes`, `rutero_dias` (`UNIQUE(fecha, asesor)`), `rutero_clientes` (`UNIQUE(rutero_dia_id, cliente_id)`, `estado` con CHECK, columnas `llamada_id`/`duracion_seg` agregadas en `database/migration_llamada_telefono.sql`), `novedades` (FK `rutero_cliente_id`: ver precisión abajo; FK `cliente_id` como `ON DELETE CASCADE`), `notas_cliente` (RLS deshabilitada, ligada solo a `cliente_id`), `pedidos` (`cliente_id` `ON DELETE CASCADE`, `rutero_cliente_id` `ON DELETE SET NULL`, mismo criterio que `novedades`), `cambios_cliente` (`cliente_id` `ON DELETE CASCADE`, sin FK a rutero — no depende de un rutero_cliente), `asesores` (`nombre` PK, `telefono_id`, `codigo_asesor`).

**Columnas/tablas nuevas desde el checkpoint anterior, con migración ejecutada y verificada por el usuario en Supabase de producción (según lo indicado explícitamente por el usuario al encargar esta tarea de documentación; no reproducido de forma independiente por Claude Code en esta sesión):**
- `novedades`: `asesor TEXT`, `anulada BOOLEAN NOT NULL DEFAULT false`, `anulada_motivo TEXT`, más índice `idx_novedades_asesor_fecha (asesor, fecha)` — `database/migration_novedades_dashboard.sql`.
- `clientes`: `novedad_excel TEXT`, `asesor_campo TEXT` — `database/migration_clientes_columnas_excel.sql`.
- `clientes`: `franja_desde TIME`, `franja_hasta TIME` — `database/migration_clientes_franja_horaria.sql`.
- `clientes`: `email TEXT`, `segmento TEXT`, `telefono2 TEXT`, `observacion_excel TEXT`, `dato_a_corregir TEXT`; `asesores`: `codigo_asesor TEXT` — `database/migration_formato_nuevo_rutero.sql`.
- Tabla `pedidos` completa (`id`, `cliente_id`, `rutero_cliente_id`, `asesor`, `fecha`, `detalle`, `created_at`) más índices `idx_pedidos_cliente_fecha`/`idx_pedidos_asesor_created` — `database/migration_pedidos.sql`.
- Tabla `cambios_cliente` completa (`id`, `cliente_id`, `asesor`, `campo`, `valor_anterior`, `valor_nuevo`, `fecha`, `created_at`) más índices `idx_cambios_cliente_fecha`/`idx_cambios_cliente_cliente_created` — `database/migration_cambios_cliente.sql`. **Esta migración ya fue ejecutada y verificada por el usuario en producción** (confirmado explícitamente al encargar esta tarea de documentación).
Todas las migraciones son aditivas (`ADD COLUMN IF NOT EXISTS` / `CREATE TABLE IF NOT EXISTS`), sin backfill donde el dato no existía previamente, y `schema.sql` quedó actualizado en la misma sección para que una instalación nueva incluya todo esto desde el principio.

- El archivo `schema.sql` declara inicialmente la FK `novedades.rutero_cliente_id` con `ON DELETE CASCADE` (`database/schema.sql:50`, dentro del `CREATE TABLE IF NOT EXISTS novedades`). Más adelante, en el mismo archivo (`database/schema.sql:144-146`), esa constraint se elimina (`DROP CONSTRAINT IF EXISTS novedades_rutero_cliente_id_fkey`) y se recrea con `ON DELETE SET NULL`. El estado final que define el script **ejecutado completo y en orden** es `ON DELETE SET NULL` — VERIFICADO EN CÓDIGO.
- **Que ese estado final (SET NULL) esté efectivamente aplicado en la instancia real de Supabase de producción ya NO es un pendiente: el usuario confirmó haberlo verificado directamente en producción** (verificación reportada por el usuario, no reproducida por Claude Code en esta sesión). BR-014 y DEC-011 se actualizan en consecuencia.

## Flujo de llamadas (VERIFICADO EN CÓDIGO)
1. `POST /cola/llamar` resuelve el `telefono_id` vinculado al asesor de la sesión (`cola.py:138`). Recibe también `numero_a_usar: "principal"|"secundario"` (default `"principal"`) — el navegador nunca manda un número, solo esa etiqueta.
2. `OrdenarLlamadaCliente` resuelve `telefono` o `telefono2` del cliente según la etiqueta (validado igual que el principal; si se pide el secundario y no es válido, error claro sin caer al principal en silencio), genera `llamada_id` (UUID), lo persiste en `rutero_clientes.llamada_id` antes de enviar la orden. Llamar al secundario no cuenta como intento (BR-002 sin cambios) ni crea novedades.
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
El parser (`excel_rutero_parser.py`) acepta **dos formatos** de archivo, vía un `COLUMN_MAP` con alias (varios nombres de columna de Excel pueden mapear al mismo campo interno), normalizado insensible a mayúsculas y espacios sobrantes:
- **Formato antiguo** (`RUTERO_*.xlsx`): `Usuario, ASESOR, Cod Cliente, Documento, Cliente, Razon social, Direccion, Barrio, Ciudad, Dias Visita, Telefono, Novedades` (12 columnas).
- **Formato nuevo** (`ACTUALIZACION_DATOS_TV_*.xlsx`, hoja `Informe`, 16 columnas): `COD ASESOR` (alias de `Usuario`), `Codigo` (alias de `Cod Cliente`), `Razon s.` (alias de `Razon social`), `Dias` (alias de `Dias Visita`), `NOVEDAD` (alias de `Novedades`), más columnas sin equivalente antiguo: `OBSERVACION` (→ `clientes.observacion_excel`), `DATO A CORREGIR` (→ `clientes.dato_a_corregir`), `Email.` (→ `clientes.email`), `Segmento` (→ `clientes.segmento`), `Telefono2` (→ `clientes.telefono2`). El resto de nombres (`Documento`, `Cliente`, `Direccion`, `Barrio`, `Ciudad`, `Telefono`) son iguales en ambos formatos.
- El parser elige automáticamente, de las hojas del libro, la primera que tenga las columnas imprescindibles (`cod_cliente`/`dias_visita`) y al menos una fila — ignora hojas vacías, sin asumir que la primera hoja es la buena. Si ninguna hoja cumple, falla con `ValueError` explícito indicando qué falta y qué nombres se aceptan (antes el archivo se cargaba en silencio sin insertar nada).
- `ASESOR`/`COD ASESOR` se leen por fila. `ASESOR` (→ `clientes.asesor_campo`, informativo, no determina el dueño del rutero, ver BR-016) es distinto de `COD ASESOR`/`Usuario` (→ código de PUESTO de la asesora de televenta, usado para filtrar la carga, ver BR-020). `Novedades`/`NOVEDAD` se persiste en `clientes.novedad_excel` (sin relación con la tabla `novedades` del sistema — homónimos).
- El archivo trae toda la semana; `parsear_dia_visita` (`src/domain/servicios/dia_visita.py`) determina el día desde los últimos 2 caracteres del código (tolerante a espacios y prefijos SS/Q/M). Clientes sin día válido se incluyen en todos los días de esa semana, marcados con badge "Sin día definido". Carga por lotes: `upsert_lote()` (merge por `cod_cliente`, un upsert por día) y `crear_llamadas_lote()` (`ignore_duplicates=True`, preserva progreso si se recarga el mismo rutero) — ver "Carga por lotes" en `ARCHITECTURE.md`.
- **Filtrado por código de asesora (formato nuevo, BR-020):** `CargarRutero` calcula el conjunto de códigos distintos en el archivo. Si la asesora tiene `codigo_asesor` configurado, se cargan solo las filas con ese código (error claro si no aparece en el archivo). Si no lo tiene configurado y el archivo trae uno solo, se usa y se guarda automáticamente en su perfil. Si no lo tiene y el archivo trae varios, no se carga nada y se pide configurar el código antes de reintentar. El resultado de la carga informa cuántas filas se cargaron y cuántas se descartaron por ser de otro código.
La política de conflicto en cada carga es "el Excel manda": el upsert de `clientes` sobrescribe con lo que traiga el archivo cualquier columna que `_to_row()` incluya — hoy eso incluye también `email`/`telefono2`/`segmento`/`observacion_excel`/`dato_a_corregir`, aunque sean editables desde la app (ver DEC-016). Los campos editables desde la app (nombre, dirección, etc.) están en `_to_row()` y por tanto se pierden si se recarga un Excel con el dato viejo; `franja_desde`/`franja_hasta` se dejaron deliberadamente FUERA de `_to_row()` para que sobrevivan a cualquier recarga (no vienen del Excel).

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
- **Clientes de prueba dentro del rutero real de producción**: `900000001`–`900000010` y los rangos `990000001`–`990000030`/`000990001`–`000990028` (nombres que empiezan por `PRUEBA`) — reportado por el usuario; no verificable desde este repositorio (son datos en Supabase, no código).
- **La columna `Usuario` puede quedar mezclada al exportar el rutero completo** si se cargaron ruteros de la misma semana con distinto `usuario_id`: `ExportarRuteroExcel` toma el primer `usuario_id` no vacío que encuentra entre los clientes deduplicados y lo usa para todas las filas y el nombre del archivo — no hay lógica que detecte o advierta sobre una mezcla.
- **`rutero_clientes.llamada_id` es una sola columna que se sobrescribe en cada orden** (`asociar_llamada_telefono`, `supabase_llamada_repository.py`): si la asesora ordena una segunda llamada (a cualquier número) antes de que llegue el `IDLE` de la primera, el `llamada_id` de la primera se pierde y su `IDLE` posterior no encuentra fila que actualizar — la duración de esa primera llamada se pierde en silencio. Preexistente, no introducido por la funcionalidad de teléfono secundario; aceptado explícitamente porque `duracion_seg` no se usa en ninguna pantalla ni reporte (verificado: cero referencias en `exportar_reporte.py`, `calcular_stats_rutero.py` o cualquier plantilla).
- **Las columnas `OBSERVACION`/`NOVEDAD`/`DATO A CORREGIR` del Excel se rellenan de forma inconsistente en el archivo real** (reportado por el usuario: a veces el valor nuevo está en una columna y el nombre del campo en otra). Hoy la aplicación solo las guarda y las muestra tal cual vienen; no las interpreta ni las valida.
- **Si el registro de un cambio en `cambios_cliente` falla, esa corrección queda sin rastro** salvo lo que quede en el log del servidor (`log.exception` en `EditarCliente._registrar_cambios`) — consecuencia aceptada deliberadamente de que la auditoría nunca debe bloquear la edición del cliente.
- **El orden de las filas de la hoja de correcciones se resuelve en Python**, no vía `.order()` de PostgREST, porque supabase-py no ordena con facilidad por una columna de una tabla enlazada (`clientes.nombre` desde `cambios_cliente`) — aceptable al volumen actual (correcciones semanales de un asesor).
- **Solo se registran los cambios hechos a partir de la implementación de `cambios_cliente`**: las correcciones que las asesoras hicieron antes de esta funcionalidad no quedaron registradas en ningún lado y no se pueden reconstruir retroactivamente.

## Trabajo pendiente (aplazado deliberadamente, no es deuda técnica)
- **Reporte de solicitudes de corrección para los jefes — IMPLEMENTADO.** Cada corrección de datos de cliente hecha desde la aplicación se registra automáticamente en `cambios_cliente` (campo, valor anterior, valor nuevo, asesor, fecha); el Excel de `/reportes/exportar` incluye una segunda hoja "Correcciones solicitadas" con los cambios de la semana del asesor de la sesión, lista para enviar al jefe. `observacion_excel`/`dato_a_corregir` (columnas del Excel) siguen sin alimentar ningún reporte — el reporte implementado se basa en `cambios_cliente`, no en esas columnas de texto libre.
- **Alerta de abandono por producto**: no se considera implementable de forma fiable porque el ERP/ecom no tiene un catálogo de productos actualizado (motivo verificado explícitamente antes de diseñar la señal de inactividad de pedidos, ver DEC-020). La señal de inactividad implementada es solo por fecha (semanas desde el último pedido), no por producto. Sigue abierto.
- **Reordenación real de la cola por franja horaria**: hoy la franja horaria solo genera un aviso visual (BR-018/DEC-017); no hay ninguna implementación, ni siquiera parcial, de que la cola priorice o filtre por franja. Sigue abierto.
