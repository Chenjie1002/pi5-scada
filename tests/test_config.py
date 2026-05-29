from pi5_scada.config import Settings


def test_settings_have_safe_defaults(monkeypatch) -> None:
    for key in (
        "PI5_SCADA_APP_NAME",
        "PI5_SCADA_POLL_INTERVAL_MS",
        "PI5_SCADA_DATABASE_URL",
        "PI5_SCADA_RAW_DATA_DIR",
    ):
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_name == "Pi5 SCADA"
    assert settings.poll_interval_ms == 200
    assert settings.database_url == "sqlite:///./data/pi5_scada.sqlite3"
    assert settings.raw_data_dir == "./data/raw"
