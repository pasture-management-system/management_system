"""
牛隻資料模型
Cattle Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Cattle(Base):
    """牛隻資料表"""
    __tablename__ = "cattle"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    serial_number = Column(String(20), unique=True, index=True, nullable=False, comment="牛隻身份編號 S/N")
    category = Column(String(10), nullable=False, comment="類別: S=小牛, K=整隻牛")
    purchase_id = Column(Integer, ForeignKey("purchases.id"), comment="進貨單ID")
    purchase_detail_id = Column(Integer, ForeignKey("purchase_details.id"), comment="進貨明細ID")
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), comment="供應商ID")
    entry_date = Column(Date, nullable=False, comment="進場日期")
    entry_weight = Column(Numeric(10, 2), comment="進場重量(公斤)")
    current_weight = Column(Numeric(10, 2), comment="目前重量(公斤)")
    exit_date = Column(Date, comment="出場日期")
    exit_weight = Column(Numeric(10, 2), comment="出場重量(公斤)")
    unit_price = Column(Numeric(10, 2), comment="進貨單價")
    total_price = Column(Numeric(12, 2), comment="進貨總價")
    status = Column(String(20), default="在養", comment="狀態: 在養/已售出/死亡")
    death_date = Column(Date, comment="死亡日期")
    death_reason = Column(Text, comment="死亡原因")
    feeding_days = Column(Integer, default=0, comment="畜牧天數")
    notes = Column(Text, comment="備註")
    is_archived = Column(Boolean, default=False, comment="是否已歸檔")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    # 關聯
    supplier = relationship("Supplier", backref="cattle")

    def __repr__(self):
        return f"<Cattle(id={self.id}, serial_number={self.serial_number})>"
