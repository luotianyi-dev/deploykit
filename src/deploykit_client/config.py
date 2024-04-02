from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str = ""
    api_url: str = "https://deployapi.webservice.luotianyi.dev"
    timezone: str = "UTC"
    project: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_endpoint: str = ""

settings = Settings()
