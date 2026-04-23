import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model: str = os.getenv("NOVA_MODEL", "claude-sonnet-4-6")

    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")
    news_api_key: str = os.getenv("NEWS_API_KEY", "")

    email_address: str = os.getenv("EMAIL_ADDRESS", "")
    email_password: str = os.getenv("EMAIL_PASSWORD", "")
    email_smtp_server: str = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    email_smtp_port: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))

    spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")

    wake_word: str = os.getenv("NOVA_WAKE_WORD", "nova")
    voice_rate: int = int(os.getenv("NOVA_VOICE_RATE", "175"))
    voice_volume: float = float(os.getenv("NOVA_VOICE_VOLUME", "1.0"))
    language: str = os.getenv("NOVA_LANGUAGE", "en-US")

    def validate(self) -> list[str]:
        errors = []
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required in .env file")
        return errors
