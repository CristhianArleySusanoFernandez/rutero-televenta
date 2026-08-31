# BUSINESS_RULES.md

> Reglas de negocio confirmadas por el comportamiento actual del sistema (código o documentación existente en el repositorio). Ninguna regla aquí es una suposición no verificada — las suposiciones van en la sección final "Reglas por confirmar".

### BR-001 — Orden de la cola de llamadas
**Regla:** La cola prioriza primero los clientes reagendados cuyo tiempo de espera ya venció (`reagendado_para <= ahora`), y luego los clientes pendientes/en reintento, ordenados por `posicion_cola` ascendente.
**Fuente:** `src/infrastructure/adapters/supabase_llamada_repository.py` (lógica de `get_siguiente_en_cola`).
**Estado:** CONFIRMADA

### BR-002 — Reintentos ante "no contesta"
**Regla:** El primer "no contesta" de un cliente lo pasa a `reintento_pendiente` y lo reinserta ~4 posiciones más adelante en la cola. El segundo "no contesta" lo marca `no_contesto` de forma definitiva (ya no vuelve a reintentar automáticamente).
**Fuente:** `src/infrastructure/adapters/supabase_llamada_repository.py` (lógica de `registrar_no_contesta_con_reintento`).
**Estado:** CONFIRMADA

### BR-003 — Reagendamiento
**Regla:** Un cliente puede marcarse como `reagendado` con una fecha/hora futura (`reagendado_para = ahora + minutos`, minutos definidos por la asesora). Vuelve a la cola automáticamente cuando ese tiempo vence.
**Fuente:** `src/application/use_cases/*` + `POST /cola/reagendar` (`src/api/routers/cola.py`).
**Estado:** CONFIRMADA

### BR-004 — Saltar cliente
**Regla:** Saltar un cliente lo marca directamente como `no_contesto` y registra una novedad automática con el motivo indicado, sin pasar por el ciclo de reintentos normal.
**Fuente:** `POST /cola/saltar` (`src/api/routers/cola.py`).
**Estado:** CONFIRMADA

### BR-005 — Finalización de la cola del día
**Regla:** La cola se considera "terminada" cuando no quedan clientes pendientes, ni en reintento, ni reagendados con el tiempo de espera vencido (puede seguir habiendo reagendados a futuro, en cuyo caso el sistema muestra "esperando" en lugar de "terminado").
**Fuente:** `src/application/use_cases/obtener_siguiente_cliente.py` + `supabase_llamada_repository.py`.
**Estado:** CONFIRMADA

### BR-006 — Corrección de resultado
**Regla:** Solo se puede corregir el resultado de un cliente que ya esté en estado final `contesto` o `no_contesto`, y solo alternando entre esos dos estados. La corrección requiere una observación obligatoria y queda registrada como una novedad adicional (no reemplaza el historial).
**Fuente:** `src/application/use_cases/corregir_resultado.py`, `POST /llamadas/{id}/corregir-resultado`.
**Estado:** CONFIRMADA

### BR-007 — Novedades
**Regla:** Una novedad tiene un tipo predefinido (`TipoNovedad`: 8 valores en español, ej. "Otro (ver observación)") y queda asociada al cliente. El historial de novedades de un cliente sobrevive aunque se elimine el rutero (ver BR-011).
**Fuente:** `src/domain/value_objects/tipo_novedad.py`, `database/schema.sql` (tabla `novedades`).
**Estado:** CONFIRMADA

### BR-008 — Notas permanentes
**Regla:** Las notas de un cliente están ligadas únicamente al `cliente_id`, no al rutero ni a un día específico. Son independientes de cualquier rutero cargado o eliminado.
**Fuente:** `database/schema.sql` (tabla `notas_cliente`, sin FK a `rutero_clientes`/`rutero_dias`).
**Estado:** CONFIRMADA

### BR-009 — El rutero es semanal, no diario
**Regla:** Un mismo archivo Excel trae los clientes de toda la semana. El sistema los reparte automáticamente en un `rutero_dia` distinto por cada día de la semana presente en el archivo, según la columna "Dias Visita" de cada cliente.
**Fuente:** `src/application/use_cases/cargar_rutero.py`, `src/domain/servicios/dia_visita.py`.
**Estado:** CONFIRMADA

### BR-010 — Parseo del código de día de visita
**Regla:** El día se determina a partir de los últimos 2 caracteres del código (mayúsculas, sin espacios): `LU, MA, MI, JU, VI, SA`. Prefijos de frecuencia (`SS`, `Q`, `M`, con o sin número) se ignoran para efectos de determinar el día.
**Fuente:** `src/domain/servicios/dia_visita.py` (`parsear_dia_visita`).
**Estado:** CONFIRMADA

### BR-011 — Clientes sin día de visita válido
**Regla:** Un cliente cuyo código no termina en un día reconocible (`LU..SA`) no se descarta: se incluye en TODOS los días de esa semana que tengan clientes, marcado visualmente con un badge "Sin día definido" para revisión manual de la asesora.
**Fuente:** `src/application/use_cases/cargar_rutero.py`, `src/api/templates_config.py` (`dia_visita_invalido`), `src/api/templates/partials/cliente_card.html`.
**Estado:** CONFIRMADA

### BR-012 — Multi-asesor y aislamiento de datos
**Regla:** Cada asesora tiene su propio rutero por fecha (`UNIQUE(fecha, asesor)` en `rutero_dias`). Toda consulta de cola/stats/reporte/eliminación se filtra siempre por `(fecha, asesor)` de la sesión actual — una asesora nunca ve ni puede borrar el rutero de otra.
**Fuente:** `database/schema.sql` (constraint `UNIQUE(fecha, asesor)`), `src/api/dependencies.py` (`get_asesor_actual` por cookie), `src/api/routers/rutero.py`.
**Estado:** CONFIRMADA

### BR-013 — Preservación de progreso al recargar el mismo rutero
**Regla:** Si se vuelve a subir un Excel para un rutero que ya existía (misma fecha/día/asesor/cliente), los registros `rutero_clientes` ya existentes NO se sobrescriben (no se pierde el estado ni la posición ya avanzada).
**Fuente:** `SupabaseClienteRepository`/`SupabaseLlamadaRepository` — upsert con `on_conflict=..., ignore_duplicates=True` (`crear_llamada`).
**Estado:** CONFIRMADA

### BR-014 — Eliminación de rutero preserva historial del cliente
**Regla:** Al eliminar el rutero de un día, las novedades de los clientes de ese rutero no se pierden — el FK `novedades.rutero_cliente_id` es `ON DELETE SET NULL` (la novedad sobrevive sin ese vínculo, pero conserva `cliente_id`). Las notas permanentes nunca están en riesgo porque no dependen del rutero (ver BR-008).
**Fuente:** `database/schema.sql`. El archivo declara la FK inicialmente con `ON DELETE CASCADE` (`schema.sql:50`), y más adelante (`schema.sql:144-146`) la elimina y la recrea con `ON DELETE SET NULL`.
**Estado:** CONFIRMADA — verificada por el usuario directamente en producción (ya no es un pendiente; ver `CURRENT_STATE.md`).

### BR-017 — Anulación de novedades (soft-delete)
**Regla:** Una novedad puede anularse pero nunca se borra físicamente. Anular marca `anulada = true` y guarda un `anulada_motivo` obligatorio; una novedad ya anulada no puede volver a anularse. Solo el asesor que la creó puede anularla (verificado en servidor contra la cookie de sesión, no contra lo que envíe el navegador). Una novedad anulada deja de contar en el dashboard de novedades y desaparece de la exportación del reporte de excepciones (`get_problematicos_del_dia`), pero sigue visible, marcada, en el historial del cliente.
**Fuente:** `src/application/use_cases/anular_novedad.py`, `POST /clientes/novedades/{id}/anular`, `database/migration_novedades_dashboard.sql` (columnas `anulada`/`anulada_motivo`).
**Estado:** CONFIRMADA

### BR-018 — Franja horaria preferida: preferencia blanda, nunca reordena
**Regla:** Un cliente puede tener una franja horaria preferida (`franja_desde`/`franja_hasta`), permanente y editable. Es puramente informativa: NO bloquea ninguna llamada, NO excluye al cliente de la cola, y NO cambia el orden en que `get_siguiente_en_cola` decide a quién llamar — solo agrega un aviso visual si la hora actual (Colombia) está fuera de esa franja.
**Fuente:** `src/domain/servicios/franja_horaria.py` (`esta_fuera_de_franja`), `src/infrastructure/adapters/supabase_llamada_repository.py` (`_enriquecer_fila`, con una consulta separada que no toca el `select()` de `get_siguiente_en_cola`), `partials/vista_enfocada.html`.
**Estado:** CONFIRMADA

### BR-019 — Exportación del rutero completo con `Cod Cliente` como texto
**Regla:** El rutero completo de la semana (12 columnas, formato original del Excel) se exporta filtrando por los `rutero_dias` del asesor de la sesión — nunca desde la tabla `clientes` completa, que es global y contiene clientes de otros ruteros. Un cliente que aparece en varios días de la semana (BR-011) sale una sola vez. La celda `Cod Cliente` se fuerza a formato de texto (`number_format="@"`, valor escrito como `str`) para conservar los ceros a la izquierda (ej. `000373587`) — sin esto, el archivo quedaría inservible para reimportar.
**Fuente:** `src/application/use_cases/exportar_rutero_excel.py`, `GET /rutero/exportar-completo`.
**Estado:** CONFIRMADA

### BR-015 — Confirmación obligatoria antes de eliminar un rutero
**Regla:** Antes de borrar el rutero de un día, el sistema muestra un resumen (total de clientes y cuántos ya fueron llamados) y requiere confirmación explícita de la asesora.
**Fuente:** `GET /rutero/resumen`, `DELETE /rutero/eliminar` (`src/api/routers/rutero.py`), JS en `src/api/templates/index.html`.
**Estado:** CONFIRMADA

### BR-016 — Asesor de campo (Excel) vs. dueño del rutero (sesión)
**Regla:** La columna "Asesor" del Excel identifica a quien visita en campo, pero NO determina el dueño del rutero en el sistema — el dueño real es la asesora de televenta identificada por la cookie de la sesión que hizo la carga.
**Fuente:** `src/application/use_cases/cargar_rutero.py` (comentario y lógica explícitos).
**Estado:** CONFIRMADA

### BR-020 — Código de asesora: es un PUESTO, no una persona
**Regla:** El `codigo_asesor` (ej. `10964`, `10991`) identifica un puesto de televenta, no a la persona que lo ocupa — las televendedoras rotan de puesto y deben poder cambiar su código configurado. Al cargar el formato nuevo de rutero, se filtran solo las filas cuyo código coincide con el configurado (o se autoconfigura si el archivo trae uno solo y la asesora no tiene ninguno); si hay varios códigos en el archivo y ninguno configurado, no se carga nada.
**Fuente:** `src/application/use_cases/cargar_rutero.py` (`_filtrar_por_codigo_asesor`), `src/api/routers/asesor.py` (`/asesor/codigo`), `database/migration_formato_nuevo_rutero.sql` (`asesores.codigo_asesor`).
**Estado:** CONFIRMADA

### BR-021 — Llamada al teléfono secundario no cuenta como intento
**Regla:** La asesora puede ordenar la marcación al `telefono2` del cliente además del principal, en cualquier orden y las veces que quiera. Marcar al secundario no registra novedades, no cambia el estado del `rutero_cliente`, y no participa en la lógica de reintentos — BR-002 no cambia: el intento fallido lo sigue declarando la asesora al pulsar "No contestó", sin importar a qué número llamó.
**Fuente:** `src/application/use_cases/ordenar_llamada_cliente.py` (parámetro `numero_a_usar`), `POST /cola/llamar` (`src/api/routers/cola.py`).
**Estado:** CONFIRMADA

### BR-022 — Señal de inactividad de pedidos solo con historial previo
**Regla:** La alerta de "lleva tiempo sin pedir" (`semanas_sin_ultima_compra >= 4`) solo puede aparecer si el cliente tiene al menos un pedido registrado. Un cliente sin ningún pedido registrado nunca se marca como inactivo — no haber comprado nunca no es lo mismo que haber dejado de comprar.
**Fuente:** `src/domain/servicios/antiguedad_pedido.py`, `src/infrastructure/adapters/supabase_llamada_repository.py` (`_datos_pedidos`).
**Estado:** CONFIRMADA

### BR-023 — Registro automático de correcciones de datos del cliente
**Regla:** Toda corrección de datos de cliente hecha por una asesora (vía `EditarCliente`) se registra automáticamente en `cambios_cliente`, una fila por cada campo de `CAMPOS_EDITABLES` que realmente cambió (comparado ya normalizado). La carga del Excel (`CargarRutero`/`upsert_lote`) y `EditarFranjaHoraria` NO generan ningún registro — no son correcciones hechas por la asesora sobre datos que existan en ecom.
**Fuente:** `src/application/use_cases/editar_cliente.py` (`_registrar_cambios`), `database/migration_cambios_cliente.sql`.
**Estado:** CONFIRMADA

### BR-024 — Reporte de correcciones: semana del día exportado, filtrado por asesora
**Regla:** La hoja "Correcciones solicitadas" del Excel de `/reportes/exportar` cubre la semana (lunes a sábado) que contiene la fecha exportada, y solo incluye los cambios del asesor de la sesión (BR-012) — nunca los de otra asesora.
**Fuente:** `src/application/use_cases/exportar_reporte.py` (`_agregar_hoja_correcciones`), `src/infrastructure/adapters/supabase_cambio_cliente_repository.py` (`get_por_asesor_rango`, filtro `.eq("asesor", asesor)`).
**Estado:** CONFIRMADA

### BR-025 — El registro de correcciones es de solo consulta
**Regla:** `cambios_cliente` y el reporte que lo exporta son de solo lectura para el flujo de negocio: nadie marca un cambio como "aplicado en ecom" desde la aplicación, porque el sistema no tiene forma de saber si el jefe efectivamente hizo el cambio en el ERP. El reporte es un insumo para que el jefe actúe fuera de la aplicación, no un flujo de aprobación.
**Fuente:** `src/application/use_cases/exportar_reporte.py`, `src/domain/ports/cambio_cliente_repository.py` (sin ningún método de actualización o marcado de estado).
**Estado:** CONFIRMADA

## Reglas por confirmar
Estas afirmaciones parecen reglas de negocio plausibles pero no están confirmadas únicamente por el código/documentación revisados:

- **Que producción corra actualmente en Render y que Android se conecte por el dominio `rutero-televenta.onrender.com`** — declarado por el usuario en conversación, no verificable desde el contenido del repositorio por sí solo. Ver `CURRENT_STATE.md`.
- **Propósito real (si alguno) de la variable `TELEFONO_ID`** declarada en `.env.example` — no se encontró uso en el código Python. NO DETERMINADA.
- **Límite máximo de reintentos distinto de 2**, o alguna política de reintentos configurable — el código observado implementa exactamente 2 intentos (1 original + 1 reintento); no se encontró configuración que lo haga variable. NO DETERMINADA si existe alguna intención de hacerlo configurable en el futuro.
