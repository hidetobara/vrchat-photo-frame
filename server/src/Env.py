import json

import google.auth
from google.oauth2.service_account import Credentials
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


SCOPES = ['https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/photoslibrary']

class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    plan: str
    seed: str = Field(default="HOGE")
    frame_limit: int = Field(default=5)

    # GOOGLE_APPLICATION_CREDENTIALS_JSON
    google_application_credentials: str | None = Field(default=None)
    google_application_credentials_json: str | None = Field(default=None)

    def get_google_credentials(self):
        if self.google_application_credentials_json is None:
            credentials, project = google.auth.default()
        else:
            info = json.loads(self.google_application_credentials_json)
            credentials = Credentials.from_service_account_info(info,
                scopes=SCOPES)
        return credentials

    # Cloudflare
    cf_access_key_id: str
    cf_secret_access_key: str
    cf_endpoint: str
