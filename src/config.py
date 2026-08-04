from pydantic_settings import BaseSettings, SettingsConfigDict

from src.paths import exe_dir


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Ruta absoluta: el .env vive junto al .exe, no dentro del bundle de
    # PyInstaller, y no debe depender del directorio de trabajo del proceso.
    model_config = SettingsConfigDict(
        env_file=str(exe_dir() / ".env"), env_file_encoding="utf-8"
    )


settings = Settings()
