from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "GestionEventosParqueConsota"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str
    jwt_secret_key: str
    jwt_expire_minutes: int = 30
    cors_origins: str = "http://localhost:5173"
    external_api_base_url: str = ""
    external_api_auth_url: str = ""
    external_api_username: str = ""
    external_api_password: str = ""
    external_api_timeout: int = 15

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
