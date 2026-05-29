from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pi5 SCADA"
    poll_interval_ms: int = 200
    database_url: str = "sqlite:///./data/pi5_scada.sqlite3"
    raw_data_dir: str = "./data/raw"

    model_config = SettingsConfigDict(env_prefix="PI5_SCADA_", env_file=".env")
