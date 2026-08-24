# CURRENT_STATE.md

> Estado del proyecto verificable ÚNICAMENTE desde el código actual del repositorio, a fecha de esta inspección. No confundir con suposiciones de conversación.
>
> Etiquetas usadas: **VERIFICADO EN CÓDIGO** / **NO DETERMINADO DESDE EL CÓDIGO** / **PENDIENTE DE VERIFICACIÓN EN PRODUCCIÓN**

## Repositorio
- Branch: `main` — VERIFICADO EN CÓDIGO
- Último commit de código: `ee28eaf` "Rutero semanal por dia de visita + eliminar rutero cargado" — VERIFICADO EN CÓDIGO
- Working tree **al momento de la inspección inicial del código** (commit `ee28eaf`): limpio, sin cambios sin commitear, sincronizado con `origin/main` — VERIFICADO EN CÓDIGO
- Working tree **actual** (tras crear esta documentación): ya NO está limpio — `git status` reporta los seis archivos `docs/PROJECT_CONTEXT.md`, `docs/CURRENT_STATE.md`, `docs/ARCHITECTURE.md`, `docs/BUSINESS_RULES.md`, `docs/DECISIONS.md`, `docs/AI_WORKFLOW.md` como `??` (sin trackear, sin commitear). Ningún archivo de código fue modificado. — VERIFICADO EN CÓDIGO (vía `git status`)

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
- Exportación de reporte Excel del día.
- Empaquetado local vía PyInstaller (`.exe`) y configuración de despliegue en Render.

## Endpoints existentes (VERIFICADO EN CÓDIGO)
Ver lista completa y exacta (método, ruta, archivo:línea) en `ARCHITECTURE.md`, sección "Endpoints". Resumen por router:
- `main.py`: `GET /`
- `asesor.py` (`/asesor`): seleccionar (GET/POST), salir (POST), teléfono (GET/POST)
- `cola.py` (`/cola`): vista-enfocada, saltar, llamar, no-contesto, reagendar
- `llamadas.py` (`/llamadas`): estado (PATCH), novedad (POST), corregir-resultado (POST), corregir-form (GET), novedad-form (GET), historial (GET)
- `notas.py` (`/notas`): listar (GET), crear (POST), eliminar (DELETE)
- `reportes.py` (`/reportes`): exportar (GET)
- `rutero.py` (`/rutero`): cargar (POST), hoy (GET), stats (GET), resumen (GET), eliminar (DELETE)
- `telefono.py`: `/ws/telefono` (WS), `/telefono/estado`, `/telefono/{id}/estado`, `/telefono/{id}/llamar`, `/telefono/{id}/colgar`

## Estructura de BD conocida desde schema.sql (VERIFICADO EN CÓDIGO, contenido del archivo `database/schema.sql`)
Tablas: `clientes`, `rutero_dias` (`UNIQUE(fecha, asesor)`), `rutero_clientes` (`UNIQUE(rutero_dia_id, cliente_id)`, `estado` con CHECK, columnas `llamada_id`/`duracion_seg` agregadas en `database/migration_llamada_telefono.sql`), `novedades` (FK `rutero_cliente_id`: ver precisión abajo; FK `cliente_id` como `ON DELETE CASCADE`), `notas_cliente` (RLS deshabilitada, ligada solo a `cliente_id`), `asesores` (`nombre` PK, `telefono_id`).

- El archivo `schema.sql` declara inicialmente la FK `novedades.rutero_cliente_id` con `ON DELETE CASCADE` (`database/schema.sql:50`, dentro del `CREATE TABLE IF NOT EXISTS novedades`). Más adelante, en el mismo archivo (`database/schema.sql:144-146`), esa constraint se elimina (`DROP CONSTRAINT IF EXISTS novedades_rutero_cliente_id_fkey`) y se recrea con `ON DELETE SET NULL`. El estado final que define el script **ejecutado completo y en orden** es `ON DELETE SET NULL` — VERIFICADO EN CÓDIGO.
- Que ese estado final (SET NULL) esté efectivamente aplicado en la instancia real de Supabase de producción — **PENDIENTE DE VERIFICACIÓN EN PRODUCCIÓN**. El resultado depende de que el script se haya ejecutado completo y en orden: una ejecución parcial (por ejemplo, deteniéndose antes de las líneas 144-146) o una creación previa de la tabla `novedades` sin aplicar después ese `ALTER`, podría haber dejado la FK real en `CASCADE`. Se intentó verificar por consulta de solo lectura vía cliente Supabase/PostgREST y no fue posible: no existe función RPC para consultar `pg_catalog`; requiere que alguien lo confirme manualmente en el SQL Editor de Supabase con: `select confdeltype from pg_constraint where conname = 'novedades_rutero_cliente_id_fkey';`

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
Columnas esperadas: `Usuario, Asesor, Cod Cliente, Documento, Cliente, Razon social, Direccion, Barrio, Ciudad, Dias Visita, Telefono`. El archivo trae toda la semana; `parsear_dia_visita` (`src/domain/servicios/dia_visita.py`) determina el día desde los últimos 2 caracteres del código (tolerante a espacios y prefijos SS/Q/M). Clientes sin día válido se incluyen en todos los días de esa semana, marcados con badge "Sin día definido". Upsert de clientes por `cod_cliente`; upsert de `rutero_clientes` con `ignore_duplicates=True` (preserva progreso si se recarga el mismo rutero).

## Frontend (VERIFICADO EN CÓDIGO)
HTMX para filtros/notas/formularios parciales; JS inline maneja el modo cola, polling de estado del teléfono (10s), auto-refresco de la pantalla de espera de reagendados (30s), y swaps manuales con `htmx.process()`. Tailwind CSS compilado localmente (sin CDN), htmx.js servido localmente desde `/static`.

## Android / WebSocket (según documentación existente en el repositorio: `docs/contrato_websocket.md`)
Protocolo JSON v1.0 sobre WebSocket. Mensajes teléfono→servidor: `registro`, `disponible`, `estado_llamada` (OFFHOOK/IDLE), `salud` (heartbeat 30s). Mensajes servidor→teléfono: `llamar`, `colgar`. — VERIFICADO EN CÓDIGO (contrato documentado) / la implementación de la app Android en sí **NO ESTÁ EN ESTE REPOSITORIO** — NO DETERMINADO DESDE EL CÓDIGO.

## Configuración (VERIFICADO EN CÓDIGO)
Variables leídas realmente por `src/config.py`: `SUPABASE_URL`, `SUPABASE_KEY`, `APP_HOST`, `APP_PORT`. `.env.example` también declara `TELEFONO_ID`, pero no se encontró ningún uso de esa variable en el código Python — NO DETERMINADO DESDE EL CÓDIGO su propósito actual real (posible vestigio de un diseño anterior).

## Tests
No existe carpeta `tests/` ni archivos `test_*.py`/`*_test.py` propios del proyecto — VERIFICADO EN CÓDIGO (ausencia confirmada).

## Deployment
- **Producción actual: Render.** El servicio despliega `uvicorn src.api.main:app` según `render.yaml`. — Esto es una afirmación operativa proporcionada por el usuario en esta conversación, no verificable únicamente desde el contenido de `render.yaml` (el archivo confirma que Render *está configurado como opción de deploy*, pero no que sea el que está corriendo ahora mismo). Se registra explícitamente por instrucción directa del usuario:
  - **Producción actualmente utiliza Render.** — declarado por el usuario, no verificable desde el código por sí solo.
  - **El PC accede mediante `rutero-televenta.onrender.com`.** — declarado por el usuario, no verificable desde el código.
  - **Android utiliza el mismo dominio.** — declarado por el usuario, no verificable desde el código.
  - Esto implica que el modelo de telefonía por WiFi local descrito en `docs/contrato_websocket.md` (pensado para `launcher.py` + IP local) **no sería el que está en uso actualmente**, sino que Android se conectaría al WebSocket a través del dominio de Render. Esto es una inferencia razonable a partir de lo declarado por el usuario, pero **PENDIENTE DE VERIFICACIÓN EN PRODUCCIÓN** contra la configuración real de la app Android.
- **`launcher.spec`/`launcher.py` (modo local/.exe)**: existe en el repositorio y es funcional como capacidad, pero no es el despliegue de producción actual (ver `ARCHITECTURE.md`). — VERIFICADO EN CÓDIGO que el modo existe; NO es producción según indicación del usuario.
- **El estado final `ON DELETE SET NULL` que el script de `schema.sql` deja en `novedades.rutero_cliente_id` (ver sección de Base de Datos arriba) NO está verificado en producción.** — PENDIENTE DE VERIFICACIÓN EN PRODUCCIÓN (se intentó comprobar por consulta directa y no fue posible desde las herramientas disponibles en esta sesión).
