from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./tonight.db"

    tmdb_api_key: str = ""
    yelp_api_key: str = ""

    typesafe_api_key: str = ""
    groq_api_key: str = ""

    default_location: str = "New York, NY"


settings = Settings()
