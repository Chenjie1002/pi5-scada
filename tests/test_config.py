from pi5_scada.config import Settings


def test_settings_have_safe_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "Pi5 SCADA"
    assert settings.poll_interval_ms == 200
    assert settings.database_url == "sqlite:///./data/pi5_scada.sqlite3"
    assert settings.raw_data_dir == "./data/raw"
