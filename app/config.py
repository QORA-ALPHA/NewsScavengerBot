from pydantic import BaseModel, Field, ValidationError
from typing import List
import os

class Settings(BaseModel):
    telegram_bot_token: str = Field(validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_targets: List[str] = Field(validation_alias="TELEGRAM_TARGETS")
    provider: str = Field(default="rss", validation_alias="PROVIDER")
    rss_urls: List[str] = Field(default_factory=list, validation_alias="RSS_URLS")
    refresh_minutes: int = Field(default=10, validation_alias="REFRESH_MINUTES")
    tz: str = Field(default=os.getenv("TZ") or "America/New_York", validation_alias="TZ")
    db_path: str = Field(default="/data/state.db", validation_alias="DB_PATH")
    market_provider: str = Field(default="yfinance", validation_alias="MARKET_PROVIDER")
    us30_symbol: str = Field(default="YM=F", validation_alias="US30_SYMBOL")
    us30_interval: str = Field(default="5m", validation_alias="US30_INTERVAL")
    us30_lookback: str = Field(default="2d", validation_alias="US30_LOOKBACK")
    us30_refresh_minutes: int = Field(default=5, validation_alias="US30_REFRESH_MINUTES")
    us30_enable: bool = Field(default=True, validation_alias="US30_ENABLE")
    us30_session_start: str = Field(default="09:30", validation_alias="US30_SESSION_START")
    us30_session_end: str = Field(default="16:00", validation_alias="US30_SESSION_END")

def _split_list(env_val: str) -> list:
    return [x.strip() for x in env_val.split(",") if x.strip()] if env_val else []

def load_settings() -> Settings:
    env = os.environ.copy()
    if "TELEGRAM_TARGETS" in env:
        env["TELEGRAM_TARGETS"] = _split_list(env["TELEGRAM_TARGETS"])
    if "RSS_URLS" in env:
        env["RSS_URLS"] = _split_list(env["RSS_URLS"])
    if "US30_ENABLE" in env:
        env["US30_ENABLE"] = str(env["US30_ENABLE"]).lower() in ("1","true","yes","on")
    try:
        return Settings.model_validate(env)
    except ValidationError as e:
        raise SystemExit(f"[Config] Error en variables de entorno:\n{e}\n") from e
