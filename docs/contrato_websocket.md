# Contrato de mensajes WebSocket — Servidor Python ⇄ App Android

**Versión:** 1.0
**Fecha:** 2026-07-09
**Arquitectura:** Opción A — cada asesor corre su propio servidor Python en su PC; su teléfono se conecta por WebSocket a ESE mismo PC en la misma red WiFi local. Todos los servidores comparten una base de datos Supabase común.

Este documento define el **contrato de mensajes** entre ambos lados. Es la fuente de verdad: tanto el servidor Python como la app Android deben implementarse conforme a lo aquí descrito. Ningún lado debe inventar campos o tipos no documentados aquí sin actualizar este archivo primero.

---

## 1. Formato general de los mensajes

- **Transporte:** WebSocket sobre la red WiFi local (ej. `ws://192.168.x.x:PUERTO`).
- **Codificación:** todos los mensajes son **texto JSON** (un objeto por mensaje/frame de WebSocket).
- **Campo obligatorio `tipo`:** todo mensaje incluye un campo `"tipo"` (string) que identifica el tipo de mensaje. El receptor enruta según este campo.
- **Campos comunes recomendados en todo mensaje:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | string | Identificador del tipo de mensaje (ver secciones 4 y 5). **Obligatorio.** |
| `telefono_id` | string | Identificador del teléfono/asesor que origina o destinatario del mensaje. **Obligatorio.** |
| `ts` | string (ISO 8601) | Marca de tiempo UTC en que se generó el mensaje, ej. `"2026-07-09T14:30:05.123Z"`. Útil para depurar y ordenar eventos. **Obligatorio.** |

> **Por qué `ts` en todos los mensajes:** permite reconstruir la línea de tiempo de una llamada y detectar mensajes viejos/duplicados tras una reconexión. Se usa el reloj del emisor; no se asume sincronización perfecta entre PC y teléfono.

**Esqueleto de cualquier mensaje:**

```json
{
  "tipo": "<nombre_del_tipo>",
  "telefono_id": "asesor_ana_01",
  "ts": "2026-07-09T14:30:05.123Z",
  "...": "campos específicos del tipo"
}
```

### Convención de nombres
- Tipos y campos en `snake_case`, en español, minúsculas.
- Los estados de llamada en MAYÚSCULAS por corresponder a constantes de Android (`OFFHOOK`, `IDLE`, `RINGING`).

### Errores y mensajes desconocidos
- Si un lado recibe un `tipo` desconocido, lo **ignora** (no cierra la conexión) y opcionalmente lo registra en su log.
- No se define aún un mensaje de `error` formal en la v1.0; se puede añadir en una versión futura si hace falta.

---

## 2. Identificación del teléfono (`telefono_id`)

- Cada teléfono tiene un **`telefono_id` configurable dentro de la app Android** (una pantalla de ajustes o un valor guardado la primera vez). Es un string estable elegido por el equipo, ej. `"asesor_ana_01"`.
- Debe ser **único por asesor** dentro del sistema (aunque cada asesor tenga su propio servidor, el `telefono_id` viaja a Supabase, que es compartida; por eso debe ser globalmente único).
- **No se usa** un identificador de hardware (IMEI, Android ID) como `telefono_id`, porque en Android moderno esos identificadores están restringidos por privacidad y no son fiables. Se usa un id lógico configurado por el usuario.
- El `telefono_id` viaja en **todos** los mensajes (campo común) y también explícitamente en el `registro`.

---

## 3. Ciclo de vida de la conexión y reconexión

1. **Conexión:** la app Android abre el WebSocket contra el servidor Python de su PC.
2. **Primer mensaje siempre `registro`:** apenas se establece la conexión, el teléfono DEBE enviar un mensaje `registro`. El servidor no debe enviar órdenes `llamar` hasta haber recibido el `registro`.
3. **Disponibilidad:** tras el `registro`, el teléfono envía `disponible` cuando está libre para recibir órdenes.
4. **Heartbeat:** el teléfono envía `salud` periódicamente (recomendado cada **30 segundos**) para reportar batería/conexión.
5. **Detección de caída:**
   - Si el servidor **no recibe** un `salud` ni ningún otro mensaje del teléfono durante **90 segundos** (3 heartbeats perdidos), considera el teléfono **desconectado / no disponible** y así lo refleja (en memoria y/o Supabase). No debe enviarle órdenes `llamar`.
   - Se recomienda además usar el **ping/pong nativo de WebSocket** como señal de bajo nivel, complementaria al `salud` de nivel de aplicación.
6. **Reconexión (responsabilidad de la app Android):**
   - Si la conexión se cae, la app **reintenta conectarse automáticamente** con *backoff* exponencial (ej. 1s, 2s, 4s, 8s… hasta un máximo de 30s).
   - Al reconectar, la app **vuelve a enviar `registro`** como primer mensaje, y luego `disponible` si procede.
   - **Estado de una llamada en curso durante la caída:** si había una llamada activa cuando se perdió la conexión, al reconectar el teléfono debe reportar el estado actual de la llamada (`estado_llamada` con el `estado` vigente, o el `IDLE` final si ya terminó). El `llamada_id` se conserva del lado del teléfono mientras la llamada siga viva.
   - El servidor, al recibir un nuevo `registro` de un `telefono_id` que ya tenía sesión, **reemplaza** la sesión anterior por la nueva (la conexión vieja se descarta).

---

## 4. Mensajes del TELÉFONO → SERVIDOR

### 4.1 `registro`

- **Dirección:** teléfono → servidor
- **Cuándo se envía:** como **primer mensaje** inmediatamente después de abrir (o reabrir) la conexión WebSocket.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | string | Siempre `"registro"`. |
| `telefono_id` | string | Id lógico configurado en la app. |
| `ts` | string ISO 8601 | Marca de tiempo. |
| `modelo` | string | Modelo del dispositivo (ej. `"Samsung Galaxy A54"`). |
| `android_version` | string | Versión de Android legible (ej. `"14"`). |
| `sdk_int` | integer | Nivel de API de Android (ej. `34`). Útil para saber si usa `TelephonyCallback` (≥31) o `PhoneStateListener` (<31). |
| `bateria` | integer | Nivel de batería inicial, 0–100. |
| `app_version` | string | Versión de la app Android (ej. `"1.0.0"`). Ayuda a diagnosticar incompatibilidades de contrato. |

**Ejemplo:**

```json
{
  "tipo": "registro",
  "telefono_id": "asesor_ana_01",
  "ts": "2026-07-09T14:30:00.000Z",
  "modelo": "Samsung Galaxy A54",
  "android_version": "14",
  "sdk_int": 34,
  "bateria": 87,
  "app_version": "1.0.0"
}
```

---

### 4.2 `disponible`

- **Dirección:** teléfono → servidor
- **Cuándo se envía:** cuando el teléfono está libre y listo para recibir una orden `llamar`. Se envía después del `registro`, y de nuevo cada vez que una llamada termina (tras el `IDLE`) y el teléfono queda libre.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | string | Siempre `"disponible"`. |
| `telefono_id` | string | Id del teléfono. |
| `ts` | string ISO 8601 | Marca de tiempo. |

**Ejemplo:**

```json
{
  "tipo": "disponible",
  "telefono_id": "asesor_ana_01",
  "ts": "2026-07-09T14:30:02.000Z"
}
```

> **Nota de diseño:** se mantiene `disponible` como mensaje explícito (en vez de inferir disponibilidad del `IDLE`) porque hay casos donde el teléfono termina una llamada pero NO está listo para otra (batería baja, el asesor cerró la pantalla, etc.). Separar "terminó la llamada" de "estoy disponible" da control fino.

---

### 4.3 `estado_llamada`

- **Dirección:** teléfono → servidor
- **Cuándo se envía:** cada vez que Android reporta un cambio de estado de la línea durante una llamada que el servidor ordenó. Solo se reportan los estados que Android detecta de forma fiable.
- **IMPORTANTE:** **no existe** estado `"contestada"`. Android no puede saber si contestó un humano o un buzón de voz (validado previamente). El resultado humano (contestó / no contestó / buzón) lo marca el **asesor manualmente** en la interfaz; eso NO forma parte de este contrato teléfono⇄servidor, se maneja aparte (interfaz ⇄ Supabase).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | string | Siempre `"estado_llamada"`. |
| `telefono_id` | string | Id del teléfono. |
| `ts` | string ISO 8601 | Marca de tiempo del cambio de estado. |
| `llamada_id` | string (UUID) | Id de la llamada que el servidor asignó en la orden `llamar`. Permite correlacionar el evento con la llamada. |
| `estado` | string (enum) | Estado reportado. Valores permitidos: `"OFFHOOK"` (línea activa: empezó a marcar / en curso) e `"IDLE"` (llamada finalizada / colgada). Ver nota sobre `RINGING`. |
| `duracion_seg` | integer \| null | Solo presente y significativo cuando `estado = "IDLE"`. Duración aproximada de la llamada en segundos, medida desde OFFHOOK hasta IDLE. En estado `OFFHOOK` va `null` (o se omite). |

**Semántica de `estado`:**
- `OFFHOOK` → la línea pasó a activa. Marca el **inicio** de la llamada (marcando o ya conversando; Android no distingue). Se envía una vez, al comenzar.
- `IDLE` → la llamada **terminó** (colgó cualquiera de las dos partes). Incluye `duracion_seg`. La duración cuenta desde OFFHOOK, por lo que incluye el tiempo de tono de llamada; es aproximada.
- `RINGING` **no se usa** en este flujo: corresponde a llamadas *entrantes*, y aquí solo gestionamos salientes ordenadas por el servidor. Si la app lo detecta, no lo reporta como parte de una llamada saliente.

**Ejemplo — inicio (OFFHOOK):**

```json
{
  "tipo": "estado_llamada",
  "telefono_id": "asesor_ana_01",
  "ts": "2026-07-09T14:31:10.000Z",
  "llamada_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado": "OFFHOOK",
  "duracion_seg": null
}
```

**Ejemplo — fin (IDLE) con duración:**

```json
{
  "tipo": "estado_llamada",
  "telefono_id": "asesor_ana_01",
  "ts": "2026-07-09T14:32:05.000Z",
  "llamada_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado": "IDLE",
  "duracion_seg": 55
}
```

---

### 4.4 `salud` (heartbeat)

- **Dirección:** teléfono → servidor
- **Cuándo se envía:** periódicamente mientras la conexión esté viva. **Recomendado cada 30 segundos.**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | string | Siempre `"salud"`. |
| `telefono_id` | string | Id del teléfono. |
| `ts` | string ISO 8601 | Marca de tiempo. |
| `bateria` | integer | Nivel de batería actual, 0–100. |
| `cargando` | boolean | `true` si el teléfono está enchufado/cargando. Útil para no alarmar por batería baja si está cargando. |
| `en_llamada` | boolean | `true` si en este momento hay una llamada activa (línea en OFFHOOK). Da al servidor una verdad de fondo por si perdió algún `estado_llamada`. |

**Ejemplo:**

```json
{
  "tipo": "salud",
  "telefono_id": "asesor_ana_01",
  "ts": "2026-07-09T14:30:30.000Z",
  "bateria": 86,
  "cargando": true,
  "en_llamada": false
}
```

---

## 5. Mensajes del SERVIDOR → TELÉFONO

### 5.1 `llamar`

- **Dirección:** servidor → teléfono
- **Cuándo se envía:** cuando el asesor confirma que quiere llamar a un contacto (no hay marcado automático en cadena; siempre media una confirmación del asesor). El servidor solo la envía si el teléfono está registrado y disponible.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | string | Siempre `"llamar"`. |
| `telefono_id` | string | Id del teléfono destinatario. |
| `ts` | string ISO 8601 | Marca de tiempo. |
| `llamada_id` | string (UUID) | **Id único** de la llamada, generado por el servidor. El teléfono lo devuelve en cada `estado_llamada`. Permite rastrear la llamada de punta a punta y en Supabase. |
| `numero` | string | Número de teléfono a marcar, en formato marcable (idealmente E.164, ej. `"+50688887777"`). |
| `nombre_contacto` | string \| null | Opcional. Nombre del contacto, solo para mostrar en la app; no afecta el marcado. |

**Ejemplo:**

```json
{
  "tipo": "llamar",
  "telefono_id": "asesor_ana_01",
  "ts": "2026-07-09T14:31:08.000Z",
  "llamada_id": "550e8400-e29b-41d4-a716-446655440000",
  "numero": "+50688887777",
  "nombre_contacto": "Cliente Juan Pérez"
}
```

> **Sobre `llamada_id`:** lo genera el **servidor** (no el teléfono) porque el servidor es quien orquesta y quien escribe en Supabase; así el id existe antes de que el teléfono haga nada. Se recomienda UUID v4.

---

### 5.2 `colgar`

- **Dirección:** servidor → teléfono
- **Cuándo se envía:** cuando se necesita cancelar/terminar la llamada actual de forma remota (ej. el asesor pulsa "cancelar", o el sistema detecta que debe abortar).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | string | Siempre `"colgar"`. |
| `telefono_id` | string | Id del teléfono destinatario. |
| `ts` | string ISO 8601 | Marca de tiempo. |
| `llamada_id` | string (UUID) | Id de la llamada a colgar. El teléfono solo cuelga si coincide con la llamada activa; si ya no coincide, ignora la orden. |

**Ejemplo:**

```json
{
  "tipo": "colgar",
  "telefono_id": "asesor_ana_01",
  "ts": "2026-07-09T14:31:40.000Z",
  "llamada_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

> **Limitación técnica a validar en la implementación:** colgar una llamada mediante programación tiene restricciones en Android moderno. Requiere `ANSWER_PHONE_CALLS` (API 26+) vía `TelecomManager.endCall()` u otros mecanismos, y no siempre está permitido para apps normales sin ser la app de teléfono por defecto. Esto se abordará al implementar; el contrato lo prevé, pero puede que en la práctica `colgar` sea "mejor esfuerzo" (el asesor cuelga manualmente como respaldo).

---

## 6. Resumen de mensajes

| Tipo | Dirección | Propósito |
|------|-----------|-----------|
| `registro` | teléfono → servidor | Identificarse al conectar (primer mensaje). |
| `disponible` | teléfono → servidor | Señalar que está libre para recibir órdenes. |
| `estado_llamada` | teléfono → servidor | Reportar OFFHOOK (inicio) e IDLE (fin + duración). |
| `salud` | teléfono → servidor | Heartbeat: batería, carga, en_llamada. |
| `llamar` | servidor → teléfono | Ordenar marcar un número (con `llamada_id`). |
| `colgar` | servidor → teléfono | Ordenar colgar la llamada actual. |

---

## 7. Flujo típico de una llamada (línea de tiempo)

```
Teléfono                          Servidor
   |-- registro -------------------->|   (al conectar)
   |-- disponible ------------------>|
   |-- salud (cada 30s) ------------>|
   |                                 |
   |<-------------- llamar ----------|   (asesor confirma)
   |-- estado_llamada OFFHOOK ------>|   (empezó a marcar)
   |   ... conversación ...          |
   |-- estado_llamada IDLE (dur) --->|   (colgaron)
   |-- disponible ------------------>|   (listo para la siguiente)
```

El resultado humano (contestó / no contestó / buzón de voz) lo marca el **asesor en la interfaz**, y se guarda en Supabase por separado, correlacionado por `llamada_id`. No viaja por este contrato WebSocket.

---

## 8. Cambios de versión

Cualquier cambio en nombres de tipos, campos o semántica debe:
1. Incrementar la **Versión** al inicio de este documento.
2. Documentarse aquí antes de tocar el código de cualquiera de los dos lados.
