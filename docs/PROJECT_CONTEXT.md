# PROJECT_CONTEXT.md

> Documento de contexto general. Fuente de verdad para que cualquier conversación de IA nueva entienda el proyecto rápidamente, sin depender del historial de un chat anterior.

## Nombre del proyecto
Rutero Televenta (Distribuciones Santiago De Tunja S.A.S.)

## Objetivo
Dar a las asesoras de televenta una herramienta web para gestionar su rutero diario/semanal de clientes a llamar, ordenar la cola de llamadas, disparar la marcación desde un teléfono Android conectado por WebSocket, y registrar el resultado de cada llamada (contestó, no contestó, novedad, reagendamiento).

## Problema que resuelve
Antes, el proceso de televenta dependía de ruteros en Excel gestionados manualmente, sin cola de llamadas ordenada, sin registro centralizado de novedades/notas por cliente, y sin integración con el teléfono físico desde el que se marca. El sistema centraliza esto en una app web + un teléfono Android controlado remotamente.

## Qué proceso de televenta automatiza
- Carga del rutero semanal desde un archivo Excel (por lotes: 18 peticiones a Supabase en vez de ~1240 para 620 clientes).
- Distribución automática de los clientes por día de visita.
- Cola ordenada de llamadas pendientes, con reintentos y reagendamiento.
- Orden de marcación al teléfono Android vía WebSocket.
- Registro de resultado de la llamada (contestó / no contestó / novedad), con corrección posterior.
- Historial de novedades y notas permanentes por cliente; anulación (sin borrar) de novedades que ya no aplican.
- Dashboard de novedades por día/semana/mes.
- Búsqueda de clientes fuera de la cola, con edición de sus datos (incluidos los campos del formato nuevo de Excel: email, teléfono2, segmento, observación, dato a corregir) y de su franja horaria preferida (aviso, no bloqueo).
- Registro de pedidos por cliente (texto libre), con historial de los últimos 3, sugerencias de texto ya usado y señal de inactividad si lleva tiempo sin comprar.
- Aviso al cliente por WhatsApp cuando no se le pudo contactar.
- Llamada al teléfono secundario del cliente, cuando lo tiene, sin contar como intento adicional.
- Carga del rutero en dos formatos de Excel (antiguo y nuevo), filtrada por el código de asesora (puesto) para no mezclar los clientes de otra asesora.
- Registro automático de correcciones de datos de cliente, con reporte semanal ("Correcciones solicitadas") para que la asesora se lo envíe a su jefe y éste gestione el cambio en el ERP (ecom).
- Exportación de reporte de excepciones del día (con la hoja de correcciones incluida) y exportación del rutero completo de la semana (para volver a subirlo).
- Gestión de múltiples asesoras trabajando en paralelo, cada una con su propio teléfono.

## Usuarios del sistema
- **Asesoras de televenta**: usuarias principales, operan la cola de llamadas desde el navegador.
- No hay roles de administrador ni autenticación con contraseña identificados en el código (ver `CURRENT_STATE.md`).

## Flujo general
1. La asesora selecciona/crea su identidad (cookie, sin contraseña).
2. Sube el Excel del rutero semanal.
3. El sistema reparte los clientes por día de visita.
4. La asesora entra a la "vista enfocada" y avanza la cola: llama, registra resultado, reagenda, salta o anota novedades.
5. Las llamadas se disparan en el teléfono Android vinculado a esa asesora, vía WebSocket.
6. Al terminar, puede exportar un reporte del día.

## Componentes principales
- **Backend**: FastAPI (Python), arquitectura hexagonal (`domain` / `application` / `infrastructure` / `api`).
- **Frontend**: Jinja2 + HTMX + JS inline, Tailwind CSS (compilado localmente, sin CDN).
- **Base de datos**: Supabase (PostgreSQL + API REST vía PostgREST).
- **Teléfono**: app Android (fuera de este repositorio) conectada por WebSocket al backend.
- **Empaquetado**: PyInstaller para ejecución local tipo `.exe`; despliegue en Render para la nube.

## Tecnologías
FastAPI, Uvicorn, Jinja2Templates, HTMX, Tailwind CSS v3 (build local), pandas + openpyxl (parseo de Excel), Supabase (`supabase-py`), pydantic-settings, WebSockets nativos de FastAPI, PyInstaller.

## Estado general
Repositorio activo en `main`. Funcionalidad principal implementada y usada, incluyendo dashboard de novedades, buscador/edición de clientes, franja horaria preferida, registro de pedidos, soporte de dos formatos de Excel con filtrado por código de asesora, llamada al teléfono secundario, y registro automático de correcciones de datos con su reporte semanal para los jefes (fase 2, ya implementada). Todas las migraciones de este checkpoint, incluida `cambios_cliente`, fueron ejecutadas y verificadas por el usuario en la instancia real de Supabase, según lo indicado por el usuario al encargar la actualización de esta documentación. Sigue sin existir ningún test automatizado — toda la verificación se hizo manualmente. Queda trabajo pendiente aplazado deliberadamente (alerta de abandono por producto, reordenación de cola por franja horaria) y deuda técnica conocida sin resolver — ver ambas secciones en `CURRENT_STATE.md`.

## Documentos relacionados
- `CURRENT_STATE.md` — estado verificado desde el código.
- `ARCHITECTURE.md` — arquitectura técnica real.
- `BUSINESS_RULES.md` — reglas de negocio confirmadas.
- `DECISIONS.md` — decisiones técnicas/de producto registradas.
- `AI_WORKFLOW.md` — cómo trabajar con IA en este proyecto de aquí en adelante.
