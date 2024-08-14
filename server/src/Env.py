from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    plan: str
    seed: str = Field(default="HOGE")
    frame_limit: int = Field(default=5)

    # Cloudflare
    cf_access_key_id: str
    cf_secret_access_key: str
    cf_endpoint: str
