"""
銷貨資料模型
Sales Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Sales(Base):
    """銷貨單主表"""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sales_no = Column(String(20), unique=True, index=True, nullable=False, comment="銷貨單號 SXXXXX(年月)XXX(流水號)")
    sales_date = Column(Date, nullable=False, comment="銷貨日期")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客戶ID")
    total_amount = Column(Numeric(12, 2), default=0, comment="總金額")
    total_quantity = Column(Integer, default=0, comment="總數量")
    payment_status = Column(String(20), default="未收款", comment="收款狀態: 未收款/部分收款/已收款")
    received_amount = Column(Numeric(12, 2), default=0, comment="已收金額")
    notes = Column(Text, comment="備註")
    created_by = Column(Integer, comment="建立人員ID")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    # 關聯
    customer = relationship("Customer", backref="sales")
    details = relationship("SalesDetail", back_populates="sale", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Sales(id={self.id}, sales_no={self.sales_no})>"


class SalesDetail(Base):
    """銷貨單明細表"""
    __tablename__ = "sales_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sales_id = Column(Integer, ForeignKey("sales.id"), nullable=False, comment="銷貨單ID")
    cattle_id = Column(Integer, ForeignKey("cattle.id"), comment="牛隻ID")
    cattle_serial = Column(String(20), index=True, comment="牛隻身份編號")
    category = Column(String(10), comment="類別: S=小牛, K=整隻牛")
    weight = Column(Numeric(10, 2), comment="重量(公斤)")
    unit_price = Column(Numeric(10, 2), comment="單價")
    amount = Column(Numeric(12, 2), comment="金額")
    feeding_days = Column(Integer, comment="畜牧天數")
    notes = Column(Text, comment="備註")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")

    # 關聯
    sale = relationship("Sales", back_populates="details")
    cattle = relationship("Cattle", backref="sales_details")

    def __repr__(self):
        return f"<SalesDetail(id={self.id}, cattle_serial={self.cattle_serial})>"


class CattleDeath(Base):
    """牛隻死亡記錄表"""
    __tablename__ = "cattle_deaths"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cattle_id = Column(Integer, ForeignKey("cattle.id"), nullable=False, comment="牛隻ID")
    cattle_serial = Column(String(20), index=True, comment="牛隻身份編號")
    death_date = Column(Date, nullable=False, comment="死亡日期")
    death_reason = Column(Text, comment="死亡原因")
    estimated_loss = Column(Numeric(12, 2), comment="估計損失金額")
    notes = Column(Text, comment="備註")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")

    # 關聯
    cattle = relationship("Cattle", backref="death_record")

    def __repr__(self):
        return f"<CattleDeath(id={self.id}, cattle_serial={self.cattle_serial})>"
