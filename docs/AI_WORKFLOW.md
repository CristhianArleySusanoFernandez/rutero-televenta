# AI_WORKFLOW.md

> Este documento NO describe el código del proyecto. Describe cómo se quiere trabajar con IA en este proyecto de aquí en adelante, para poder continuar el desarrollo entre distintas conversaciones sin depender de la memoria de un único chat.

## Roles

### Claude normal
Responsable de:
- Arquitectura y diseño de soluciones.
- Análisis y planificación de tareas.
- Revisión de resultados entregados por Claude Code.
- Generación de prompts estructurados para Claude Code.

**Claude normal es la autoridad de planificación y razonamiento del proceso, pero NO debe asumir que recuerda el estado actual del código.** Antes de planificar sobre una parte del sistema, debe apoyarse en los documentos de `docs/` (`CURRENT_STATE.md`, `ARCHITECTURE.md`, `BUSINESS_RULES.md`, `DECISIONS.md`) y, si algo es incierto o crítico, pedir a Claude Code que lo verifique en el código real antes de decidir.

### Claude Code
Responsable de:
- Inspección directa del código.
- Implementación de cambios.
- Ejecución de pruebas/verificaciones.
- Revisión técnica de lo implementado.
- Modificación de archivos.
- Commits, cuando corresponda y sea solicitado explícitamente.

**Claude Code es la autoridad sobre el estado REAL del código.** Ante cualquier discrepancia entre lo que dice `docs/` y lo que existe en el código, el código (verificado por Claude Code) tiene siempre prioridad, y la documentación debe actualizarse para reflejarlo.

## Flujo de trabajo obligatorio

1. Claude normal propone una tarea.
2. Claude normal genera un prompt estructurado para Claude Code.
3. Claude Code inspecciona primero el código relevante (no asume, no recuerda de conversaciones anteriores).
4. Claude Code implementa.
5. Claude Code verifica los cambios (tests si existen, ejecución manual, revisión de que no rompió nada).
6. Claude Code devuelve un resumen estructurado (ver formato obligatorio abajo).
7. Claude normal revisa ese resultado.
8. Solo después de la revisión se continúa con la siguiente tarea.

## Principio de alcance
**Claude Code nunca debe modificar archivos fuera del alcance de una tarea sin indicarlo explícitamente.** Si durante la implementación detecta que un cambio adicional es necesario o conveniente fuera del alcance original, debe reportarlo y pedir confirmación en vez de aplicarlo silenciosamente.

## Antes de cambios importantes, Claude Code debe:
- Inspeccionar el código existente relevante a la tarea.
- Identificar dependencias entre los archivos que va a tocar y el resto del sistema.
- Identificar riesgos (pérdida de datos, romper otra funcionalidad, cambios de comportamiento visibles para la asesora).
- Verificar contra `BUSINESS_RULES.md` que el cambio no contradiga una regla de negocio confirmada (o, si la contradice intencionalmente, decirlo explícitamente).
- Explicar qué archivos va a modificar antes de modificarlos, cuando el cambio sea no trivial.

## Formato obligatorio de respuesta de Claude Code

```
## TASK RESULT

### Objetivo
...

### Análisis realizado
...

### Cambios realizados
...

### Archivos modificados
...

### Tests/verificaciones
...

### Resultado
PASS / PARTIAL / FAIL

### Decisiones tomadas
...

### Riesgos
...

### Pendientes
...

### Próximo paso recomendado
...
```

## Mantenimiento de esta documentación
Cuando una tarea implementada por Claude Code cambie algo descrito en `CURRENT_STATE.md`, `ARCHITECTURE.md`, `BUSINESS_RULES.md` o `DECISIONS.md`, ese documento debe actualizarse como parte de la misma tarea (o como tarea de seguimiento explícita), no quedar desactualizado. Nunca sobrescribir estos documentos sin antes revisar su contenido existente para no perder conocimiento ya registrado.
