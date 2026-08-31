# DECISIONS.md

> Decisiones técnicas y de producto recuperables del repositorio (código, comentarios, estructura, commits, documentación existente). Donde el motivo no puede determinarse, se indica explícitamente en vez de inventarlo.

### DEC-001 — Arquitectura hexagonal (domain / application / infrastructure / api)
**Decisión:** Separar el código en capas `domain` (puro), `application` (casos de uso), `infrastructure` (adapters concretos) y `api` (composición + transporte HTTP/WS).
**Motivo:** MOTIVO NO DETERMINADO DESDE EL REPOSITORIO (no hay comentarios ni commits que expliquen la elección explícitamente; se infiere como decisión deliberada por la consistencia estricta de la estructura de carpetas y el uso de puertos/ABC en `domain/ports`).
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO.
**Estado:** ACTIVA

### DEC-002 — Supabase como backend de datos
**Decisión:** Usar Supabase (PostgreSQL + API REST vía PostgREST) como base de datos y capa de acceso a datos, en vez de una conexión SQL directa.
**Motivo:** MOTIVO NO DETERMINADO DESDE EL REPOSITORIO.
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO.
**Estado:** ACTIVA
**Nota:** Esta elección implica que no hay ejecución de SQL arbitrario desde la aplicación (no existe una función RPC tipo `exec_sql`), lo cual limita la capacidad de introspección directa del esquema en producción desde fuera del dashboard de Supabase.

### DEC-003 — Render como plataforma de despliegue en la nube
**Decisión:** Desplegar el servicio FastAPI en Render (`render.yaml`), con `SUPABASE_URL`/`SUPABASE_KEY` como variables secretas configuradas manualmente en el dashboard.
**Motivo:** MOTIVO NO DETERMINADO DESDE EL REPOSITORIO.
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO.
**Estado:** ACTIVA — según indicación del usuario, es el despliegue de producción vigente actualmente (`rutero-televenta.onrender.com`).

### DEC-004 — Modo local/.exe vía PyInstaller como alternativa de despliegue
**Decisión:** Mantener en el repositorio un modo de ejecución local empaquetado (`launcher.py`, `launcher.spec`), que detecta la IP WiFi local y expone el WebSocket para que el Android se conecte directamente en la misma red.
**Motivo:** MOTIVO NO DETERMINADO DESDE EL REPOSITORIO (posiblemente el diseño original antes de adoptar Render, dado que este modelo asume servidor y teléfono en la misma red WiFi local).
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO.
**Estado:** NO DETERMINADA si sigue activa como plan de contingencia o es un remanente de un diseño anterior — existe y es funcional en el código, pero no es la producción actual (ver `CURRENT_STATE.md`, `ARCHITECTURE.md`).

### DEC-005 — WebSocket como canal de comunicación con el teléfono Android
**Decisión:** Usar WebSocket (no HTTP polling ni push notifications) para la comunicación bidireccional en tiempo real entre el servidor y la app Android, con un protocolo JSON versionado documentado (`docs/contrato_websocket.md` v1.0).
**Motivo:** MOTIVO NO DETERMINADO DESDE EL REPOSITORIO explícitamente, aunque el contrato sugiere necesidad de baja latencia y estado de conexión persistente (heartbeat, watchdog de 90s) para saber si el teléfono está disponible antes de ordenar una llamada.
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO.
**Estado:** ACTIVA

### DEC-006 — Asociar `llamada_id` en base de datos antes de enviar la orden WS
**Decisión:** `OrdenarLlamadaCliente` genera el `llamada_id` (UUID) en el servidor y lo persiste en `rutero_clientes.llamada_id` ANTES de enviar la orden de marcar al teléfono.
**Motivo:** Evitar una condición de carrera donde el mensaje `IDLE` (fin de llamada) del teléfono llegue antes de que exista la correlación en base de datos, lo que impediría guardar la duración correctamente. Inferido directamente de la secuencia del código en `src/application/use_cases/ordenar_llamada_cliente.py`.
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO.
**Estado:** ACTIVA

### DEC-007 — Cola con 2 intentos y reinserción ~4 posiciones adelante
**Decisión:** Ante un "no contesta", reintentar automáticamente una sola vez, reinsertando al cliente ~4 posiciones más adelante en la cola en vez de al final o inmediatamente después.
**Motivo:** MOTIVO NO DETERMINADO DESDE EL REPOSITORIO (posiblemente para dar tiempo a que el cliente esté disponible en un segundo intento sin perder demasiado tiempo de la sesión de llamadas).
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO.
**Estado:** ACTIVA

### DEC-008 — Reagendamiento con tiempo de espera configurable, no fecha fija
**Decisión:** El reagendamiento se expresa como "minutos desde ahora" (`reagendado_para = ahora + minutos`) en vez de una fecha/hora absoluta elegida manualmente.
**Motivo:** MOTIVO NO DETERMINADO DESDE EL REPOSITORIO.
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO.
**Estado:** ACTIVA

### DEC-009 — Excel semanal en vez de un archivo por día
**Decisión:** Rediseñar la carga de rutero para aceptar un único archivo semanal (~620 clientes) que se reparte automáticamente por día según la columna "Dias Visita", reemplazando un modelo previo de un archivo por día.
**Motivo:** El formato real de los archivos de la empresa es semanal, no diario — según lo indicado explícitamente por el usuario al solicitar este cambio (registrado en el historial de la conversación de desarrollo, no como comentario en el código, aunque el comentario en `cargar_rutero.py` sí documenta el diseño resultante).
**Alternativas consideradas:** Mantener un archivo por día (descartada porque no correspondía a la realidad operativa) — dropear clientes sin día válido (descartada, ver DEC-010) — crear una entidad nueva "rutero semanal" separada de `rutero_dias` (descartada a favor de reutilizar el modelo existente, ver nota abajo).
**Estado:** ACTIVA
**Nota de diseño:** Se optó por reutilizar el modelo existente `rutero_dias` por `(fecha, asesor)`, creando múltiples filas (una por día de la semana presente en el archivo) en vez de introducir una nueva entidad "rutero semanal". Esto permitió que la cola, las stats y el reporte —que ya filtraban por `(fecha, asesor)`— quedaran filtrados por día sin ningún cambio en esas capas.

### DEC-010 — Clientes sin día válido no se descartan
**Decisión:** En vez de eliminar silenciosamente los clientes cuyo código de día no se reconoce, se incluyen en todos los días de esa semana con un badge visual de advertencia.
**Motivo:** Evitar pérdida silenciosa de datos de clientes reales; permitir que la asesora los revise y decida manualmente. Indicado explícitamente como requisito por el usuario durante el desarrollo de esta funcionalidad.
**Alternativas consideradas:** Descartar esos clientes (rechazada: pérdida de datos); asignarlos arbitrariamente a un solo día (rechazada: no hay forma confiable de elegir cuál).
**Estado:** ACTIVA

### DEC-011 — Migración de `novedades.rutero_cliente_id` de CASCADE a SET NULL
**Decisión:** Cambiar el FK `novedades.rutero_cliente_id` de `ON DELETE CASCADE` a `ON DELETE SET NULL`.
**Motivo:** Al implementar la funcionalidad de "eliminar rutero cargado", se detectó que el comportamiento CASCADE original borraría también las novedades de los clientes de ese rutero al eliminarlo — contradiciendo el requisito explícito del usuario de que el historial de novedades es del cliente, no del rutero, y debe sobrevivir a la eliminación.
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO (no se documentan alternativas exploradas distintas de SET NULL).
**Estado:** ACTIVA. Verificada por el usuario directamente en producción — ya no es un pendiente (ver `CURRENT_STATE.md`).

### DEC-012 — Eliminación de rutero requiere confirmación con resumen previo
**Decisión:** Antes de borrar un rutero de un día, mostrar cuántos clientes tiene y cuántos ya fueron llamados, y exigir confirmación explícita.
**Motivo:** Requisito explícito del usuario para evitar borrados accidentales sin conciencia del impacto (cuántas llamadas ya hechas se perderían de la cola).
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO.
**Estado:** ACTIVA

### DEC-013 — Eliminar dependencia de CDNs externos (Tailwind y HTMX)
**Decisión:** Compilar Tailwind CSS localmente (build v3 vía CLI) y servir HTMX como archivo local, en vez de cargarlos desde CDN en tiempo real (`cdn.tailwindcss.com`, `unpkg.com`).
**Motivo:** El CDN de Tailwind fallaba por problemas de red, dejando la interfaz sin estilos; el usuario identificó esto como un punto de falla innecesario tanto en Render como en el `.exe` empaquetado, y solicitó explícitamente eliminar la dependencia de CDNs en tiempo real.
**Alternativas consideradas:** Mantener el CDN con algún mecanismo de fallback (no se adoptó); usar Tailwind v4 CLI (descartada porque `npx @tailwindcss/cli` falló al resolver el paquete `tailwindcss`, se usó Tailwind v3 en su lugar).
**Estado:** ACTIVA

### DEC-014 — Multi-asesor por cookie, sin autenticación con contraseña
**Decisión:** Identificar a cada asesora mediante una cookie simple (`asesor`, httponly, sin login/contraseña), en vez de un sistema de autenticación formal.
**Motivo:** MOTIVO NO DETERMINADO DESDE EL REPOSITORIO.
**Alternativas consideradas:** NO DETERMINADO DESDE EL REPOSITORIO.
**Estado:** ACTIVA — riesgo de seguridad documentado en `CURRENT_STATE.md`/histórico de inspección, no una decisión que este documento cuestione, solo registre.

### DEC-015 — Carga de rutero por lotes (upsert masivo en vez de fila por fila)
**Decisión:** Reemplazar el patrón N+1 de `cargar_rutero.py` (un `upsert`/`crear_llamada` por cliente en un bucle) por un `upsert_lote()`/`crear_llamadas_lote()` por día, cada uno en una sola petición a Supabase con una lista de filas.
**Motivo:** Rendimiento — la carga de un rutero real (620 clientes, 6 días) tardaba minutos por hacer hasta ~1240 peticiones HTTP secuenciales; con el cambio bajó a 18 peticiones. Diagnosticado y cuantificado explícitamente antes de implementar (tarea de diagnóstico previa a la de diseño).
**Alternativas consideradas:** Aumentar el timeout/paralelizar las peticiones individuales (descartada: no ataca la causa, solo la disimula); una única transacción SQL directa (descartada: no hay acceso a SQL crudo, ver DEC-002).
**Estado:** ACTIVA — commit `e41a3a0`.

### DEC-016 — El Excel manda: la carga sobrescribe cualquier corrección hecha en la app (opción A)
**Decisión:** Ante el conflicto "¿qué prevalece si la asesora corrige un dato de cliente en la app y luego se recarga un Excel con el dato viejo?", se optó por mantener el upsert como merge simple: el Excel siempre sobrescribe los campos que trae. No se implementó ningún mecanismo de protección de campos editados manualmente (por ejemplo, marcar un campo como "no pisar").
**Motivo:** Simplicidad y consistencia con el comportamiento ya existente del upsert; la alternativa (proteger campos editados) requeriría rediseñar el modelo de conflicto y no fue solicitada. Riesgo aceptado explícitamente: una corrección de nombre/dirección/teléfono/etc. hecha desde la app se pierde si se recarga un Excel con el dato antiguo.
**Alternativas consideradas:** Proteger campos editados manualmente con una marca de "no sobrescribir" (rechazada por complejidad, no descartada para el futuro); invertir la fuente de verdad hacia la app (rechazada, el Excel sigue siendo el flujo operativo real de la empresa).
**Estado:** ACTIVA. Consecuencia directa y deliberada: la franja horaria (`franja_desde`/`franja_hasta`, ver DEC-017) se dejó fuera de `_to_row()` precisamente para no heredar este riesgo, porque el Excel nunca trae ese dato.

### DEC-017 — Franja horaria como aviso, nunca como criterio de reordenación de la cola
**Decisión:** La franja horaria preferida de un cliente solo genera un aviso visual (`fuera_de_franja`); no participa en ningún `.order()` ni filtro de `get_siguiente_en_cola`, ni en la lógica de reintentos o reagendamiento.
**Motivo:** Evitar el riesgo de romper BR-001 (orden de cola), BR-002 (reintentos), BR-003 (reagendamiento) o BR-005 (cola terminada) sin tener una suite de tests que detecte una regresión — el proyecto no tiene tests automatizados (ver `CURRENT_STATE.md`), así que cualquier cambio a la lógica de orden es de alto riesgo y difícil de verificar exhaustivamente. Se prefirió la solución de menor riesgo: mostrar información, no actuar sobre ella.
**Alternativas consideradas:** Usar la franja para reordenar la cola dinámicamente (rechazada: alto riesgo de romper reglas confirmadas sin cobertura de tests); excluir temporalmente de la cola a un cliente fuera de franja (rechazada explícitamente: el requisito decía "la llamada se hace siempre").
**Estado:** ACTIVA — commit `0b304f5`.

### DEC-018 — Exclusión de correcciones de resultado del dashboard mediante un prefijo compartido
**Decisión:** Las correcciones de resultado (`CorregirResultado`) se identifican en el dashboard de novedades por un prefijo literal (`[Corrección`) en el campo `observacion`, extraído a una constante compartida (`PREFIJO_CORRECCION` en `corregir_resultado.py`) e importada por el caso de uso del dashboard, en vez de duplicar el literal.
**Motivo:** Una corrección de resultado es un registro de auditoría (qué cambió y cuándo), no una novedad comercial — contarla en el dashboard de novedades registradas inflaría el número real de novedades del asesor. Usar una constante compartida (no dos copias del mismo literal) evita que el filtro del dashboard se desincronice silenciosamente si el formato del texto de corrección cambia en el futuro.
**Alternativas consideradas:** Una columna booleana explícita `es_correccion` en `novedades` (más robusto, pero requiere migración; no se hizo porque el prefijo ya identificaba el caso sin cambios de esquema).
**Estado:** ACTIVA — commit `75dc068`.

### DEC-019 — Aviso al cliente por enlace `wa.me`, sin API de WhatsApp
**Decisión:** El aviso de "te llamamos y no contestaste" se implementa como un enlace `https://wa.me/<numero>?text=<mensaje>` que la asesora abre manualmente, en vez de integrar la API de WhatsApp Business (envío automático).
**Motivo:** Costo e infraestructura — la API de WhatsApp Business requiere cuenta de negocio verificada, aprobación de plantillas de mensaje y, en general, costo por conversación; un enlace `wa.me` no tiene ningún requisito de backend ni dependencia nueva y cumple el mismo objetivo (mensaje pre-escrito, un clic). Restricción explícita del usuario: "NO integres ninguna API de WhatsApp ni añadas dependencias nuevas".
**Alternativas consideradas:** API oficial de WhatsApp Business (rechazada por costo/infraestructura); SMS (no evaluado, fuera del alcance solicitado).
**Estado:** ACTIVA — commit `75dc068`.

### DEC-020 — Pedidos en texto libre, sin catálogo de productos
**Decisión:** El registro de pedidos por cliente (`pedidos.detalle`) es texto libre; no hay tabla de productos ni relación con un catálogo, y la señal de inactividad es solo por fecha (semanas desde el último pedido), nunca por producto específico.
**Motivo:** El ERP/ecom de la empresa no tiene una base de productos actualizada y confiable; una alerta "dejaste de pedir el producto X" requeriría ese catálogo para tener sentido, y construirlo no era parte del alcance. Verificado explícitamente antes de diseñar la funcionalidad, no una limitación descubierta después.
**Alternativas consideradas:** Relacionar pedidos con un catálogo de productos propio del sistema (rechazada: duplicaría datos que ya deberían vivir en el ERP y quedaría desincronizada); alerta de abandono por producto (rechazada por la misma razón, ver "Trabajo pendiente" en `CURRENT_STATE.md`).
**Estado:** ACTIVA — commit `21819b6`.

### DEC-021 — Dos formatos de Excel soportados mediante alias de columnas, no dos parsers
**Decisión:** `ExcelRuteroParser` acepta el formato antiguo (`RUTERO_*.xlsx`) y el nuevo (`ACTUALIZACION_DATOS_TV_*.xlsx`) con un único `COLUMN_MAP` donde varios nombres de columna de Excel pueden mapear al mismo campo interno, en vez de mantener dos parsers separados o dos rutas de carga distintas.
**Motivo:** Los dos formatos describen esencialmente los mismos datos con nombres de columna distintos (`Cod Cliente`/`Codigo`, `Dias Visita`/`Dias`, etc.); un único mapa de alias evita duplicar toda la lógica de reparto por día, upsert y validación que ya existía y estaba probada para el formato antiguo.
**Alternativas consideradas:** Un parser nuevo dedicado al formato nuevo (rechazada: duplicaría `CargarRutero` y el resto del flujo de carga sin necesidad); detectar el formato y convertir a un DataFrame intermedio antes de mapear (rechazada por complejidad innecesaria frente al alias directo).
**Estado:** ACTIVA — commit `5541b43`.

### DEC-022 — Teléfono secundario resuelto en el servidor mediante etiqueta, sin cambiar el contrato WebSocket
**Decisión:** Para llamar al `telefono2`, el navegador envía solo una etiqueta (`"principal"`/`"secundario"`), nunca un número; el servidor resuelve el número real contra la base de datos, igual que ya hacía con el principal. El contrato WebSocket v1.0 no se modificó.
**Motivo:** Mantener el mismo principio de confianza que ya regía `OrdenarLlamadaCliente` ("no confía en datos que vengan del navegador") en vez de crear una excepción para el segundo número; el mensaje `llamar` del contrato ya llevaba `numero` como valor resuelto, así que no había necesidad de tocar un contrato que también usa (o usaría) la app Android, que no está en este repositorio y cuyo cambio habría que coordinar aparte. Verificado explícitamente (inspección de solo lectura previa) antes de implementar.
**Alternativas consideradas:** Enviar el número desde el navegador (rechazada: rompe el principio de no confiar en el cliente, ya establecido); añadir un campo nuevo al contrato WS para indicar cuál número usar (rechazada: innecesaria, y habría requerido cambiar la app Android).
**Estado:** ACTIVA — commit `f7e3b43`.

### DEC-023 — Registrar correcciones automáticamente, no que la asesora marque qué pedir
**Decisión:** Cada corrección de datos de cliente hecha desde la aplicación se registra automáticamente (campo, valor anterior, valor nuevo, asesor, fecha), comparando el estado del cliente antes y después de `EditarCliente`, en vez de pedirle a la asesora que indique manualmente qué cambio se debe solicitar en ecom.
**Motivo:** El proceso manual existente (columnas `OBSERVACION`/`NOVEDAD`/`DATO A CORREGIR` del Excel real) se rellenaba de forma inconsistente — a veces el valor nuevo quedaba en una columna y el nombre del campo en otra, reportado explícitamente por el usuario. La aplicación ya sabe con exactitud qué campo cambió y a qué valor, porque es ella quien aplica el cambio: pedirle a la asesora que lo describa de nuevo reintroduciría el mismo riesgo de inconsistencia que se buscaba eliminar.
**Alternativas consideradas:** Un formulario aparte donde la asesora describa el cambio a mano (rechazada: mismo problema de inconsistencia que el proceso actual con el Excel); marcar manualmente "esto hay que corregirlo en ecom" al momento de editar (rechazada: carga extra sobre la asesora para un dato que el sistema ya puede derivar solo).
**Estado:** ACTIVA — commit consolidado en esta tarea de documentación/commits (ver `git log --stat` en el informe de la tarea).

### DEC-024 — Reporte de correcciones por rango de fechas, sin seguimiento de "aplicado en ecom"
**Decisión:** El reporte de correcciones (segunda hoja del Excel de `/reportes/exportar`) simplemente lista los cambios de la semana; no hay ningún mecanismo para que alguien marque una fila como "ya aplicada en ecom" ni para excluir de reportes futuros lo ya reportado.
**Motivo:** Un seguimiento de "aplicado" exigiría que el jefe (que trabaja fuera de esta aplicación, directamente en ecom) volviera a marcarlo en el sistema — un paso adicional que depende de un tercero ajeno al flujo de la asesora y que no ocurriría de forma fiable. Es más simple y más honesto que el reporte sea un corte de la realidad ("esto cambió esta semana") que un flujo de aprobación que la aplicación no puede verificar.
**Alternativas consideradas:** Estado `aplicado`/`pendiente` por fila en `cambios_cliente` con un endpoint para marcarlo (rechazada: dependencia de un actor externo al sistema, alto riesgo de quedar desactualizado); reporte acumulativo de todo el historial en vez de por semana (rechazada: el envío al jefe es semanal, un reporte acumulativo repetiría filas ya enviadas).
**Estado:** ACTIVA — commit consolidado en esta tarea de documentación/commits (ver `git log --stat` en el informe de la tarea).
