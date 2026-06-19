from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgres://macro:macro@postgres:5432/macro"
    jwt_secret: str = "dev-secret-change-me"
    settings_encryption_key: str = "dev-encryption-key-change-me-32b"
    environment: str = "development"
    server_port: int = 8080
    app_url: str = "https://economicdb.com"
    redis_url: str = "redis://redis:6379/0"
    log_level: str = "info"

    admin_initial_email: str = "erman.ai@yandex.ru"
    admin_initial_password: str = ""

    etl_sync_hour: int = 4
    etl_sync_minute: int = 0
    etl_sync_timezone: str = "Europe/Moscow"


settings = Settings()
