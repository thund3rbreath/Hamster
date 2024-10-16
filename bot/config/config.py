from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str


    REF_LINK: str = "https://t.me/hamster_kOmbat_bot/start?startapp=kentId6624523270"

    AUTO_TASK:bool = True
    AUTO_UPGRADE: bool = True
    UPGRADE_COEFFICIENT: int = 200
    AUTO_PLAYGROUND: bool = True

    DELAY_EACH_ACCOUNT: list[int] = [15,25]
    SLEEP_TIME_BETWEEN_EACH_ROUND: list[int] = [1000, 1500]


    USE_PROXY_FROM_FILE: bool = False


settings = Settings()

