"""
系統設定
System Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # 應用程式設定
    APP_NAME: str = "清發畜牧場管理系統"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "清發畜牧場進銷存、會計、薪資管理系統"
    
    # 安全設定
    SECRET_KEY: str = "your-super-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小時
    
    # 資料庫設定
    DATABASE_URL: Optional[str] = None
    
    # 備份設定
    BACKUP_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
    
    # 民國年轉換
    @staticmethod
    def to_roc_year(western_year: int) -> int:
        """西元年轉民國年"""
        return western_year - 1911
    
    @staticmethod
    def to_western_year(roc_year: int) -> int:
        """民國年轉西元年"""
        return roc_year + 1911

    class Config:
        env_file = ".env"

settings = Settings()
