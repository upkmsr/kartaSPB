from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")

    host: str = "localhost"
    port: int = 5432
    name: str = "kartaspb"
    user: str = "kartaspb"
    password: SecretStr = SecretStr("kartaspb_local")
    geocoder_url: str = Field(
        default="https://nominatim.openstreetmap.org/search", validation_alias="GEOCODER_URL"
    )
    geocoder_user_agent: str = Field(
        default="KARTASPB-development/0.4 (local GIS project)",
        validation_alias="GEOCODER_USER_AGENT",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
