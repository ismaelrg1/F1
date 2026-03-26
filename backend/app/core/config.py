from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "FutureF1 API"
    app_env: str = "development"
    debug: bool = False
    backend_port: int = 8000
    
    db_host: str = "db"
    db_port: int = 5432
    db_user: str = ""
    db_password: str = ""
    db_name: str = "futuref1"

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    jwt_access_cookie_name: str = "access_token_cookie"
    jwt_refresh_cookie_name: str = "refresh_token_cookie"
    jwt_cookie_samesite: str = "lax"
    jwt_cookie_domain: str | None = None
    jwt_cookie_secure: bool | None = None

    default_group_id: int = 1
    google_client_id: str = ""

    password_reset_token_expire_minutes: int = 5
    password_reset_request_cooldown_seconds: int = 60

    frontend_base_url: str = "http://localhost:3000"
    backend_base_url: str = "http://localhost:8000"
    cors_allowed_origins: str = "http://localhost:3000" 

    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"
    resend_from_name: str = "FutureF1"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore",
    )

    @property
    def db_url(self):
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
