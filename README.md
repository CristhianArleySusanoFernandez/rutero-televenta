# Rutero Televenta Nutresa

Aplicación web para gestión del rutero diario de televenta. Permite cargar el Excel con clientes del día, registrar el resultado de cada llamada y exportar el reporte de novedades.

## Stack

- **Backend:** FastAPI + arquitectura hexagonal (ports & adapters)
- **Frontend:** HTMX + Jinja2 + TailwindCSS (CDN)
- **Base de datos:** Supabase (PostgreSQL)
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
2. Seleccionar el archivo `.xlsx` del día (columnas requeridas: `Usuario`, `Asesor`, `Cod Cliente`, `Documento`, `Cliente`, `Razon social`, `Direccion`, `Barrio`, `Ciudad`, `Dias Visita`, `Telefono`, `NOVEDADS`)
3. La lista se actualiza automáticamente sin recargar la página

### Registrar resultado de una llamada
- **✓ Contestó** → marca la llamada como exitosa (verde)
- **✗ No contestó** → marca sin respuesta (rojo)
- **⚠ Novedad** → abre formulario inline para seleccionar tipo y agregar observación

### Ver historial
- Click en **📋 Historial** en cualquier tarjeta para ver novedades de semanas anteriores

### Exportar reporte
- Click en **📊 Exportar reporte Excel** para descargar el Excel con todas las novedades del día

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
```

## Notas importantes

- El archivo `.env` **no se sube a git** (está en `.gitignore`)
- Los casos de uso solo conocen el dominio: nunca importan de `infrastructure` ni de `api`
- El upsert de clientes se hace por `cod_cliente`, evitando duplicados al recargar el rutero
- HTMX reemplaza únicamente la tarjeta del cliente al actualizar su estado (sin recarga completa)
