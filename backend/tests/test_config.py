from pathlib import Path

from app.core.config import Settings


def test_settings_default_env_file_is_backend_env():
    env_file = Path(Settings.model_config["env_file"])

    assert env_file.name == ".env"
    assert env_file.parent == Path(__file__).resolve().parents[1]


def test_settings_load_env_file_values(tmp_path):
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()
    env_file = backend_dir / ".env"
    env_file.write_text(
        "DATABASE_URL=sqlite+pysqlite:///backend-env.db\n"
        "SECRET_KEY=backend-env-secret\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.database_url == "sqlite+pysqlite:///backend-env.db"
    assert settings.secret_key == "backend-env-secret"


def test_backend_env_example_is_next_to_backend_project():
    assert (Path(__file__).resolve().parents[1] / ".env.example").is_file()


def test_default_cors_origins_include_windows_dev_port():
    settings = Settings(_env_file=None)

    origins = {origin.strip() for origin in settings.backend_cors_origins.split(",")}

    assert "http://127.0.0.1:3000" in origins
    assert "http://localhost:3000" in origins
