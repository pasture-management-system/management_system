"""
使用者資料模型
User Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    """使用者資料表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="使用者帳號")
    password_hash = Column(String(255), nullable=False, comment="密碼雜湊")
    name = Column(String(50), comment="姓名")
    email = Column(String(100), comment="電子郵件")
    role = Column(String(20), default="user", comment="角色: admin/manager/user")
    is_active = Column(Boolean, default=True, comment="是否啟用")
    last_login = Column(DateTime, comment="最後登入時間")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
