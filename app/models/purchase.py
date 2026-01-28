"""
進貨資料模型
Purchase Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Purchase(Base):
    """進貨單主表"""
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    purchase_no = Column(String(20), unique=True, index=True, nullable=False, comment="進貨單號 PXXXXX(年月)XXX(流水號)")
    purchase_date = Column(Date, nullable=False, comment="進貨日期")
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, comment="廠商ID")
    total_amount = Column(Numeric(12, 2), default=0, comment="總金額")
    total_quantity = Column(Integer, default=0, comment="總數量")
    payment_status = Column(String(20), default="未付款", comment="付款狀態: 未付款/部分付款/已付款")
    paid_amount = Column(Numeric(12, 2), default=0, comment="已付金額")
    notes = Column(Text, comment="備註")
    created_by = Column(Integer, comment="建立人員ID")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    # 關聯
    supplier = relationship("Supplier", backref="purchases")
    details = relationship("PurchaseDetail", back_populates="purchase", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Purchase(id={self.id}, purchase_no={self.purchase_no})>"


class PurchaseDetail(Base):
    """進貨單明細表"""
    __tablename__ = "purchase_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False, comment="進貨單ID")
    cattle_serial = Column(String(20), index=True, comment="牛隻身份編號")
    category = Column(String(10), comment="類別: S=小牛, K=整隻牛")
    weight = Column(Numeric(10, 2), comment="重量(公斤)")
    unit_price = Column(Numeric(10, 2), comment="單價")
    amount = Column(Numeric(12, 2), comment="金額")
    notes = Column(Text, comment="備註")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")

    # 關聯
    purchase = relationship("Purchase", back_populates="details")

    def __repr__(self):
        return f"<PurchaseDetail(id={self.id}, cattle_serial={self.cattle_serial})>"


class PurchaseMisc(Base):
    """進貨雜項表 (設備維修、辦公文具、飼料、耗損等)"""
    __tablename__ = "purchase_misc"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    misc_no = Column(String(20), unique=True, index=True, comment="雜項單號")
    misc_date = Column(Date, nullable=False, comment="日期")
    category = Column(String(50), nullable=False, comment="類別: 設備維修/辦公文具/飼料/耗損/其他")
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), comment="廠商ID")
    item_name = Column(String(100), nullable=False, comment="品項名稱")
    quantity = Column(Numeric(10, 2), default=1, comment="數量")
    unit = Column(String(20), comment="單位")
    unit_price = Column(Numeric(10, 2), comment="單價")
    amount = Column(Numeric(12, 2), comment="金額")
    payment_status = Column(String(20), default="未付款", comment="付款狀態")
    paid_amount = Column(Numeric(12, 2), default=0, comment="已付金額")
    notes = Column(Text, comment="備註")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    # 關聯
    supplier = relationship("Supplier", backref="misc_purchases")

    def __repr__(self):
        return f"<PurchaseMisc(id={self.id}, item_name={self.item_name})>"
