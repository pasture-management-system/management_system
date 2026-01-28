"""
員工資料模型
Employee Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Numeric
from sqlalchemy.sql import func
from app.database import Base

class Employee(Base):
    """員工資料表"""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_code = Column(String(20), unique=True, index=True, comment="員工編號")
    name = Column(String(50), nullable=False, index=True, comment="員工姓名")
    id_number = Column(String(20), comment="身分證字號")
    birth_date = Column(Date, comment="出生年月日")
    gender = Column(String(10), comment="性別")
    hire_date = Column(Date, comment="到職日")
    resign_date = Column(Date, comment="離職日")
    address = Column(String(200), comment="地址")
    phone = Column(String(20), comment="電話")
    mobile = Column(String(20), comment="手機")
    email = Column(String(100), comment="電子郵件")
    emergency_contact = Column(String(50), comment="緊急聯絡人")
    emergency_phone = Column(String(20), comment="緊急聯絡電話")
    department = Column(String(50), comment="部門")
    position = Column(String(50), comment="職位")
    salary_type = Column(String(20), default="月薪", comment="薪資類型(月薪/日薪)")
    base_salary = Column(Numeric(10, 2), default=0, comment="底薪")
    bank_name = Column(String(50), comment="銀行名稱")
    bank_account = Column(String(30), comment="銀行帳號")
    labor_insurance = Column(Boolean, default=True, comment="勞保")
    health_insurance = Column(Boolean, default=True, comment="健保")
    notes = Column(Text, comment="備註")
    is_active = Column(Boolean, default=True, comment="是否在職")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.name})>"
