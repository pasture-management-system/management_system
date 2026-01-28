"""
薪資資料模型
Payroll Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Payroll(Base):
    """薪資單主表"""
    __tablename__ = "payrolls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payroll_no = Column(String(20), unique=True, index=True, nullable=False, comment="薪資單號")
    payroll_year = Column(Integer, nullable=False, comment="年度")
    payroll_month = Column(Integer, nullable=False, comment="月份")
    pay_date = Column(Date, comment="發薪日期")
    total_employees = Column(Integer, default=0, comment="員工人數")
    total_amount = Column(Numeric(12, 2), default=0, comment="薪資總額")
    status = Column(String(20), default="草稿", comment="狀態: 草稿/已確認/已發放")
    notes = Column(Text, comment="備註")
    created_by = Column(Integer, comment="建立人員ID")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    # 關聯
    details = relationship("PayrollDetail", back_populates="payroll", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Payroll(id={self.id}, payroll_no={self.payroll_no})>"


class PayrollDetail(Base):
    """薪資單明細表"""
    __tablename__ = "payroll_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payroll_id = Column(Integer, ForeignKey("payrolls.id"), nullable=False, comment="薪資單ID")
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, comment="員工ID")
    
    # 基本薪資
    base_salary = Column(Numeric(10, 2), default=0, comment="底薪")
    daily_wage = Column(Numeric(10, 2), default=0, comment="日薪")
    work_days = Column(Integer, default=0, comment="工作天數")
    
    # 加項
    bonus = Column(Numeric(10, 2), default=0, comment="獎金")
    full_attendance = Column(Numeric(10, 2), default=0, comment="全勤獎金")
    overtime_pay = Column(Numeric(10, 2), default=0, comment="加班費")
    other_allowance = Column(Numeric(10, 2), default=0, comment="其他津貼")
    
    # 扣項
    labor_insurance = Column(Numeric(10, 2), default=0, comment="勞保自付額")
    health_insurance = Column(Numeric(10, 2), default=0, comment="健保自付額")
    absence_deduction = Column(Numeric(10, 2), default=0, comment="請假扣款")
    sick_leave_deduction = Column(Numeric(10, 2), default=0, comment="病假扣款")
    other_deduction = Column(Numeric(10, 2), default=0, comment="其他扣款")
    
    # 統計
    gross_salary = Column(Numeric(10, 2), default=0, comment="應發薪資")
    total_deduction = Column(Numeric(10, 2), default=0, comment="扣款總計")
    net_salary = Column(Numeric(10, 2), default=0, comment="實發薪資")
    
    # 發放
    payment_method = Column(String(20), default="轉帳", comment="發放方式: 現金/轉帳")
    bank_name = Column(String(50), comment="銀行名稱")
    bank_account = Column(String(30), comment="銀行帳號")
    is_paid = Column(Boolean, default=False, comment="是否已發放")
    paid_date = Column(Date, comment="發放日期")
    
    notes = Column(Text, comment="備註")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    # 關聯
    payroll = relationship("Payroll", back_populates="details")
    employee = relationship("Employee", backref="payroll_details")

    def __repr__(self):
        return f"<PayrollDetail(id={self.id}, employee_id={self.employee_id})>"
