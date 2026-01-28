"""
廠商資料模型
Supplier Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base

class Supplier(Base):
    """廠商資料表"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_code = Column(String(20), unique=True, index=True, comment="廠商編號")
    name = Column(String(100), nullable=False, index=True, comment="廠商名稱")
    contact_person = Column(String(50), comment="負責人")
    address = Column(String(200), comment="地址")
    phone = Column(String(20), comment="電話")
    fax = Column(String(20), comment="傳真")
    mobile = Column(String(20), comment="手機")
    tax_id = Column(String(20), comment="統一編號")
    email = Column(String(100), comment="電子郵件")
    bank_name = Column(String(50), comment="銀行名稱")
    bank_account = Column(String(30), comment="銀行帳號")
    notes = Column(Text, comment="備註")
    is_active = Column(Boolean, default=True, comment="是否啟用")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    def __repr__(self):
        return f"<Supplier(id={self.id}, name={self.name})>"
