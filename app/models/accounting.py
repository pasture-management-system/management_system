"""
會計資料模型
Accounting Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class AccountTitle(Base):
    """會計科目表"""
    __tablename__ = "account_titles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(20), unique=True, index=True, nullable=False, comment="科目代碼")
    name = Column(String(100), nullable=False, comment="科目名稱")
    category = Column(String(50), comment="類別: 資產/負債/權益/收入/費用")
    parent_code = Column(String(20), comment="上層科目代碼")
    level = Column(Integer, default=1, comment="層級")
    is_active = Column(Boolean, default=True, comment="是否啟用")
    notes = Column(Text, comment="備註")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    def __repr__(self):
        return f"<AccountTitle(code={self.code}, name={self.name})>"


class PayableAccount(Base):
    """應付帳款表 (付款帳款作業)"""
    __tablename__ = "payable_accounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payable_no = Column(String(20), unique=True, index=True, comment="應付帳款編號")
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, comment="廠商ID")
    purchase_id = Column(Integer, ForeignKey("purchases.id"), comment="進貨單ID")
    misc_id = Column(Integer, ForeignKey("purchase_misc.id"), comment="雜項單ID")
    payable_date = Column(Date, nullable=False, comment="應付日期")
    due_date = Column(Date, comment="到期日")
    amount = Column(Numeric(12, 2), nullable=False, comment="應付金額")
    paid_amount = Column(Numeric(12, 2), default=0, comment="已付金額")
    balance = Column(Numeric(12, 2), comment="餘額")
    payment_method = Column(String(20), comment="付款方式: 現金/匯款/支票")
    payment_date = Column(Date, comment="付款日期")
    status = Column(String(20), default="未付款", comment="狀態: 未付款/部分付款/已付款")
    bank_name = Column(String(50), comment="付款銀行")
    bank_account = Column(String(30), comment="付款帳號")
    check_no = Column(String(30), comment="支票號碼")
    notes = Column(Text, comment="備註")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    # 關聯
    supplier = relationship("Supplier", backref="payables")

    def __repr__(self):
        return f"<PayableAccount(id={self.id}, amount={self.amount})>"


class ReceivableAccount(Base):
    """應收帳款表 (收款帳款作業)"""
    __tablename__ = "receivable_accounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    receivable_no = Column(String(20), unique=True, index=True, comment="應收帳款編號")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客戶ID")
    sales_id = Column(Integer, ForeignKey("sales.id"), comment="銷貨單ID")
    receivable_date = Column(Date, nullable=False, comment="應收日期")
    due_date = Column(Date, comment="到期日")
    amount = Column(Numeric(12, 2), nullable=False, comment="應收金額")
    received_amount = Column(Numeric(12, 2), default=0, comment="已收金額")
    balance = Column(Numeric(12, 2), comment="餘額")
    payment_method = Column(String(20), comment="收款方式: 現金/匯款/支票")
    payment_date = Column(Date, comment="收款日期")
    status = Column(String(20), default="未收款", comment="狀態: 未收款/部分收款/已收款")
    bank_name = Column(String(50), comment="收款銀行")
    bank_account = Column(String(30), comment="收款帳號")
    check_no = Column(String(30), comment="支票號碼")
    notes = Column(Text, comment="備註")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    # 關聯
    customer = relationship("Customer", backref="receivables")

    def __repr__(self):
        return f"<ReceivableAccount(id={self.id}, amount={self.amount})>"


class TransferVoucher(Base):
    """轉帳傳票表"""
    __tablename__ = "transfer_vouchers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    voucher_no = Column(String(20), unique=True, index=True, nullable=False, comment="傳票編號")
    voucher_date = Column(Date, nullable=False, comment="傳票日期")
    voucher_type = Column(String(20), nullable=False, comment="傳票類型: 銀行借/銀行貸/現金支出/匯款支出/現金收入/匯款收入")
    debit_account = Column(String(20), comment="借方科目代碼")
    debit_amount = Column(Numeric(12, 2), default=0, comment="借方金額")
    credit_account = Column(String(20), comment="貸方科目代碼")
    credit_amount = Column(Numeric(12, 2), default=0, comment="貸方金額")
    bank_name = Column(String(50), comment="銀行名稱")
    bank_account = Column(String(30), comment="銀行帳號")
    reference_no = Column(String(50), comment="參考單號")
    description = Column(Text, comment="說明")
    notes = Column(Text, comment="備註")
    created_by = Column(Integer, comment="建立人員ID")
    created_at = Column(DateTime, server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    def __repr__(self):
        return f"<TransferVoucher(voucher_no={self.voucher_no})>"
