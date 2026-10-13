from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Item Bank API"
    app_env: str = "development"
    database_url: str = (
        "postgresql+psycopg://smart_item_bank:change-this-local-password"
        "@localhost:5432/smart_item_bank"
    )
    jwt_secret_key: str = "local-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
