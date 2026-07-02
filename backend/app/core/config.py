from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "PDF Utility Platform"
    ENVIRONMENT: str = "development"

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    UPLOAD_DIR: str = "/app/storage/uploads"
    OUTPUT_DIR: str = "/app/storage/outputs"

    MAX_UPLOAD_SIZE_MB: int = 20
    FILE_RETENTION_MINUTES: int = 60

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    class Config:
        env_file = ".env"


settings = Settings()