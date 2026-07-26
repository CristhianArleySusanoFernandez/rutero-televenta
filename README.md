# Rutero Televenta — Distribuciones Santiago De Tunja S.A.S.

Aplicación web para gestión del rutero diario de televenta. Permite cargar el Excel con los clientes del día, marcar teléfonos desde el celular del asesor por WebSocket, registrar el resultado de cada llamada y las novedades, y exportar el reporte de casos que requieren seguimiento.

## Funcionalidades principales

- **Carga de rutero:** sube el Excel del día y genera la cola de clientes a llamar.
- **Modo cola (vista enfocada):** presenta un cliente a la vez en el orden correcto (reagendados vencidos primero, luego pendientes/reintentos por posición) y ordena la llamada al teléfono del asesor por WebSocket.
- **Resultado de la llamada:** Contestó / No contestó (con reintento automático tras el primer fallo) / Reagendar.
- **Novedades:** un cliente puede tener una novedad (número equivocado, cambió de dueño, no quiere ser llamado, etc.) de forma independiente de si contestó o no — ambos hechos conviven y se muestran juntos en su tarjeta.
- **Notas permanentes:** observaciones que persisten entre semanas, asociadas al cliente (no al rutero del día).
- **Reporte Excel:** exporta únicamente los casos que requieren una decisión (novedades, saltados, no-contestó definitivo), no los contactos exitosos.
- **Manual de la asesora:** ver `docs/MANUAL_ASESORA.md`.

## Stack

- **Backend:** FastAPI + arquitectura hexagonal (ports & adapters)
- **Frontend:** HTMX + Jinja2 + TailwindCSS (CDN)
- **Base de datos:** Supabase (PostgreSQL)
- **Telefonía:** WebSocket contra la app Android del asesor (ver `docs/contrato_websocket.md`)
- **Lectura Excel:** pandas + openpyxl
- **Exportación:** openpyxl

## Requisitos

- Python 3.11+
- Cuenta en [Supabase](https://supabase.com) (gratuita)

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd Televenta
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar Supabase

1. Ir a [supabase.com](https://supabase.com) y crear un proyecto.
2. En el panel de Supabase ir a **SQL Editor** y ejecutar el archivo `database/schema.sql`.
3. Copiar la **URL** y la **API Key (anon/public)** desde **Project Settings → API**.

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:

```env
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
APP_HOST=0.0.0.0
APP_PORT=8000
```

### 5. Ejecutar la aplicación

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Abrir el navegador en: [http://localhost:8000](http://localhost:8000)

## Uso

### Cargar rutero diario
1. Click en **📂 Cargar Rutero**
2. Seleccionar el archivo `.xlsx` del día (columnas requeridas: `Usuario`, `Asesor`, `Cod Cliente`, `Documento`, `Cliente`, `Razon social`, `Direccion`, `Barrio`, `Ciudad`, `Dias Visita`, `Telefono`)
3. La lista se actualiza automáticamente sin recargar la página

### Conectar el teléfono
La app Android del asesor debe estar abierta y conectada por WebSocket al servidor (misma red WiFi). El estado de conexión se ve en el panel de teléfono; sin conexión no se puede ordenar marcar.

### Modo cola
Entra a la vista enfocada para que el sistema presente los clientes en orden, uno a la vez, y ordene la llamada al teléfono conectado.

### Registrar resultado de una llamada
- **✓ Contestó** → marca la llamada como exitosa (verde)
- **✗ No contestó** → primer fallo reintenta más adelante en la cola; segundo fallo queda definitivo (rojo)
- **⚠ Novedad** → abre formulario inline para seleccionar tipo y agregar observación. Es independiente del resultado: un cliente puede haber contestado y además tener una novedad.

### Ver historial
- Click en **📋 Historial** en cualquier tarjeta para ver novedades de semanas anteriores

### Exportar reporte
- Click en **📊 Exportar reporte Excel** para descargar el Excel con los casos que requieren seguimiento: novedades, saltados y no-contestó definitivo. Los contactos exitosos sin novedad no aparecen.

## Estructura del proyecto

```
src/
├── domain/               # Entidades, value objects e interfaces (ports)
│   ├── entities/
│   ├── value_objects/
│   └── ports/
├── application/          # Casos de uso (lógica de negocio)
│   └── use_cases/
├── infrastructure/       # Implementaciones concretas (adapters)
│   ├── adapters/
│   └── supabase_client.py
├── api/                  # FastAPI: routers, templates, dependencias
│   ├── routers/
│   ├── templates/
│   ├── dependencies.py
│   └── main.py
└── config.py             # Configuración con pydantic-settings
database/
└── schema.sql            # DDL para ejecutar en Supabase
docs/
├── contrato_websocket.md # Contrato de mensajes servidor ⇄ app Android
└── MANUAL_ASESORA.md     # Manual de uso para la asesora de televenta
```

## Notas importantes

- El archivo `.env` **no se sube a git** (está en `.gitignore`)
- Los casos de uso solo conocen el dominio: nunca importan de `infrastructure` ni de `api`
- El upsert de clientes se hace por `cod_cliente`, evitando duplicados al recargar el rutero
- HTMX reemplaza únicamente la tarjeta del cliente al actualizar su estado (sin recarga completa)
- `estado` en `rutero_clientes` es solo el resultado de la llamada; una novedad se guarda aparte en la tabla `novedades` y no lo sobrescribe — un cliente puede haber contestado y tener una novedad al mismo tiempo
