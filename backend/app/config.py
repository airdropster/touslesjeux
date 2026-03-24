from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://touslesjeux:changeme@localhost:5432/touslesjeux"
    openai_api_key: str = ""
    google_cse_api_key: str = ""
    google_cse_cx: str = ""
    app_api_key: str = "changeme"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
