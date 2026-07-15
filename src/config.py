from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    groq_api_key: str = ""
    # Id del teléfono de este asesor (Opción A: un teléfono por PC).
    # Vacío = usar el único teléfono conectado; si hay varios, es obligatorio.
    telefono_id: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
