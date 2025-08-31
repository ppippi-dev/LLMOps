"""pydantic 설정 파일"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정 클래스.

    .env 파일에서 환경 변수를 로드합니다.
    """

    model_config = SettingsConfigDict(env_file=".env")

    # API 설정
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5-nano"


# 설정 인스턴스 생성
settings = Settings()
