"""
會計管理路由
Accounting Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from app.database import get_db
from app.models.accounting import AccountTitle, PayableAccount, ReceivableAccount, TransferVoucher
from app.models.supplier import Supplier
from app.models.customer import Customer
from app.models.purchase import Purchase, PurchaseMisc
from app.models.sales import Sales

router = APIRouter(prefix="/accounting", tags=["會計管理"])
templates = Jinja2Templates(directory="templates")

def parse_date(date_str: str) -> Optional[date]:
    """解析日期字串"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return None

def generate_payable_no(db: Session, payable_date: date) -> str:
    """產生應付帳款編號"""
    roc_year = payable_date.year - 1911
    prefix = f"AP{roc_year}{payable_date.month:02d}"
    
    last = db.query(PayableAccount).filter(
        PayableAccount.payable_no.like(f"{prefix}%")
    ).order_by(PayableAccount.payable_no.desc()).first()
    
    if last:
        try:
            last_seq = int(last.payable_no[-3:])
            return f"{prefix}{str(last_seq + 1).zfill(3)}"
        except:
            pass
    
    return f"{prefix}001"

def generate_receivable_no(db: Session, receivable_date: date) -> str:
    """產生應收帳款編號"""
    roc_year = receivable_date.year - 1911
    prefix = f"AR{roc_year}{receivable_date.month:02d}"
    
    last = db.query(ReceivableAccount).filter(
        ReceivableAccount.receivable_no.like(f"{prefix}%")
    ).order_by(ReceivableAccount.receivable_no.desc()).first()
    
    if last:
        try:
            last_seq = int(last.receivable_no[-3:])
            return f"{prefix}{str(last_seq + 1).zfill(3)}"
        except:
            pass
    
    return f"{prefix}001"

def generate_voucher_no(db: Session, voucher_date: date) -> str:
    """產生傳票編號"""
    roc_year = voucher_date.year - 1911
    prefix = f"TV{roc_year}{voucher_date.month:02d}"
    
    last = db.query(TransferVoucher).filter(
        TransferVoucher.voucher_no.like(f"{prefix}%")
    ).order_by(TransferVoucher.voucher_no.desc()).first()
    
    if last:
        try:
            last_seq = int(last.voucher_no[-3:])
            return f"{prefix}{str(last_seq + 1).zfill(3)}"
        except:
            pass
    
    return f"{prefix}001"

# ============== 頁面路由 ==============

# 應付帳款
@router.get("/payables", response_class=HTMLResponse)
async def payable_list_page(request: Request, db: Session = Depends(get_db)):
    """應付帳款列表頁面"""
    payables = db.query(PayableAccount).order_by(PayableAccount.id.desc()).limit(100).all()
    
    # 計算統計數據
    unpaid = db.query(func.sum(PayableAccount.balance)).filter(PayableAccount.status != "已付款").scalar() or 0
    paid = db.query(func.sum(PayableAccount.paid_amount)).filter(PayableAccount.status == "已付款").scalar() or 0
    total = db.query(func.sum(PayableAccount.amount)).scalar() or 0
    
    return templates.TemplateResponse("accounting/payables.html", {
        "request": request,
        "payables": payables,
        "summary": {
            "unpaid": unpaid,
            "paid": paid,
            "total": total
        },
        "active_menu": "accounting"
    })

@router.get("/payables/create", response_class=HTMLResponse)
async def payable_create_page(request: Request, db: Session = Depends(get_db)):
    """新增應付帳款頁面"""
    payable_no = generate_payable_no(db, date.today())
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    purchases = db.query(Purchase).filter(Purchase.payment_status != "已付款").all()
    return templates.TemplateResponse("accounting/payable_form.html", {
        "request": request,
        "payable_no": payable_no,
        "suppliers": suppliers,
        "purchases": purchases,
        "active_menu": "accounting"
    })

# 應收帳款
@router.get("/receivables", response_class=HTMLResponse)
async def receivable_list_page(request: Request, db: Session = Depends(get_db)):
    """應收帳款列表頁面"""
    receivables = db.query(ReceivableAccount).order_by(ReceivableAccount.id.desc()).limit(100).all()
    
    # 計算統計數據
    uncollected = db.query(func.sum(ReceivableAccount.balance)).filter(ReceivableAccount.status != "已收款").scalar() or 0
    collected = db.query(func.sum(ReceivableAccount.received_amount)).filter(ReceivableAccount.status == "已收款").scalar() or 0
    total = db.query(func.sum(ReceivableAccount.amount)).scalar() or 0
    
    return templates.TemplateResponse("accounting/receivables.html", {
        "request": request,
        "receivables": receivables,
        "summary": {
            "uncollected": uncollected,
            "collected": collected,
            "total": total
        },
        "active_menu": "accounting"
    })

@router.get("/receivables/create", response_class=HTMLResponse)
async def receivable_create_page(request: Request, db: Session = Depends(get_db)):
    """新增應收帳款頁面"""
    receivable_no = generate_receivable_no(db, date.today())
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    sales_list = db.query(Sales).filter(Sales.payment_status != "已收款").all()
    return templates.TemplateResponse("accounting/receivable_form.html", {
        "request": request,
        "receivable_no": receivable_no,
        "customers": customers,
        "sales_list": sales_list,
        "active_menu": "accounting"
    })

# 轉帳傳票
@router.get("/vouchers", response_class=HTMLResponse)
async def voucher_list_page(request: Request, db: Session = Depends(get_db)):
    """轉帳傳票列表頁面"""
    vouchers = db.query(TransferVoucher).order_by(TransferVoucher.id.desc()).limit(100).all()
    
    # 計算統計數據
    total_count = db.query(func.count(TransferVoucher.id)).scalar() or 0
    total_debit = db.query(func.sum(TransferVoucher.debit_amount)).scalar() or 0
    total_credit = db.query(func.sum(TransferVoucher.credit_amount)).scalar() or 0
    
    return templates.TemplateResponse("accounting/vouchers.html", {
        "request": request,
        "vouchers": vouchers,
        "summary": {
            "count": total_count,
            "debit": total_debit,
            "credit": total_credit
        },
        "active_menu": "accounting"
    })

@router.get("/vouchers/create", response_class=HTMLResponse)
async def voucher_create_page(request: Request, db: Session = Depends(get_db)):
    """新增轉帳傳票頁面"""
    voucher_no = generate_voucher_no(db, date.today())
    account_titles = db.query(AccountTitle).filter(AccountTitle.is_active == True).all()
    return templates.TemplateResponse("accounting/voucher_form.html", {
        "request": request,
        "voucher_no": voucher_no,
        "account_titles": account_titles,
        "active_menu": "accounting"
    })

# 會計科目
@router.get("/accounts", response_class=HTMLResponse)
async def account_list_page(request: Request, db: Session = Depends(get_db)):
    """會計科目列表頁面"""
    accounts = db.query(AccountTitle).order_by(AccountTitle.code).all()
    return templates.TemplateResponse("accounting/account_list.html", {
        "request": request,
        "accounts": accounts,
        "active_menu": "accounting"
    })

# ============== API 路由 ==============

# 應付帳款 API
@router.get("/api/payables/list")
async def get_payables(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得應付帳款列表 API"""
    query = db.query(PayableAccount)
    
    if status:
        query = query.filter(PayableAccount.status == status)
    if supplier_id:
        query = query.filter(PayableAccount.supplier_id == supplier_id)
    
    total = query.count()
    payables = query.order_by(PayableAccount.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": p.id,
            "payable_no": p.payable_no,
            "supplier_name": p.supplier.name if p.supplier else None,
            "payable_date": str(p.payable_date) if p.payable_date else None,
            "amount": float(p.amount) if p.amount else 0,
            "paid_amount": float(p.paid_amount) if p.paid_amount else 0,
            "balance": float(p.balance) if p.balance else float(p.amount - p.paid_amount) if p.amount else 0,
            "status": p.status
        } for p in payables],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/api/payables/unpaid")
async def get_unpaid_payables(db: Session = Depends(get_db)):
    """取得未付帳款清單"""
    payables = db.query(PayableAccount).filter(
        PayableAccount.status != "已付款"
    ).order_by(PayableAccount.due_date).all()
    
    total_unpaid = sum(float(p.amount - p.paid_amount) for p in payables)
    
    return {
        "success": True,
        "data": [{
            "id": p.id,
            "payable_no": p.payable_no,
            "supplier_name": p.supplier.name if p.supplier else None,
            "due_date": str(p.due_date) if p.due_date else None,
            "amount": float(p.amount) if p.amount else 0,
            "paid_amount": float(p.paid_amount) if p.paid_amount else 0,
            "balance": float(p.amount - p.paid_amount) if p.amount else 0
        } for p in payables],
        "total_unpaid": total_unpaid
    }

@router.post("/api/payables/create")
async def create_payable(request: Request, db: Session = Depends(get_db)):
    """新增應付帳款 API"""
    form_data = await request.form()
    
    payable_date = parse_date(form_data.get("payable_date")) or date.today()
    
    payable = PayableAccount(
        payable_no=form_data.get("payable_no") or generate_payable_no(db, payable_date),
        supplier_id=int(form_data.get("supplier_id")),
        purchase_id=int(form_data.get("purchase_id")) if form_data.get("purchase_id") else None,
        payable_date=payable_date,
        due_date=parse_date(form_data.get("due_date")),
        amount=Decimal(form_data.get("amount") or 0),
        payment_method=form_data.get("payment_method"),
        notes=form_data.get("notes")
    )
    payable.balance = payable.amount
    
    db.add(payable)
    db.commit()
    
    return {"success": True, "message": "應付帳款建立成功", "data": {"id": payable.id}}

@router.post("/api/payables/{payable_id}/pay")
async def pay_payable(payable_id: int, request: Request, db: Session = Depends(get_db)):
    """沖帳應付帳款 API"""
    payable = db.query(PayableAccount).filter(PayableAccount.id == payable_id).first()
    if not payable:
        raise HTTPException(status_code=404, detail="應付帳款不存在")
    
    form_data = await request.form()
    
    pay_amount = Decimal(form_data.get("pay_amount") or 0)
    payment_method = form_data.get("payment_method")
    payment_date = parse_date(form_data.get("payment_date")) or date.today()
    
    payable.paid_amount = (payable.paid_amount or 0) + pay_amount
    payable.balance = payable.amount - payable.paid_amount
    payable.payment_method = payment_method
    payable.payment_date = payment_date
    payable.bank_name = form_data.get("bank_name")
    payable.bank_account = form_data.get("bank_account")
    
    if payable.balance <= 0:
        payable.status = "已付款"
    elif payable.paid_amount > 0:
        payable.status = "部分付款"
    
    db.commit()
    
    return {"success": True, "message": "沖帳成功"}

# 應收帳款 API
@router.get("/api/receivables/list")
async def get_receivables(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得應收帳款列表 API"""
    query = db.query(ReceivableAccount)
    
    if status:
        query = query.filter(ReceivableAccount.status == status)
    if customer_id:
        query = query.filter(ReceivableAccount.customer_id == customer_id)
    
    total = query.count()
    receivables = query.order_by(ReceivableAccount.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": r.id,
            "receivable_no": r.receivable_no,
            "customer_name": r.customer.name if r.customer else None,
            "receivable_date": str(r.receivable_date) if r.receivable_date else None,
            "amount": float(r.amount) if r.amount else 0,
            "received_amount": float(r.received_amount) if r.received_amount else 0,
            "balance": float(r.balance) if r.balance else float(r.amount - r.received_amount) if r.amount else 0,
            "status": r.status
        } for r in receivables],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/api/receivables/unreceived")
async def get_unreceived_receivables(db: Session = Depends(get_db)):
    """取得未收帳款清單"""
    receivables = db.query(ReceivableAccount).filter(
        ReceivableAccount.status != "已收款"
    ).order_by(ReceivableAccount.due_date).all()
    
    total_unreceived = sum(float(r.amount - r.received_amount) for r in receivables)
    
    return {
        "success": True,
        "data": [{
            "id": r.id,
            "receivable_no": r.receivable_no,
            "customer_name": r.customer.name if r.customer else None,
            "due_date": str(r.due_date) if r.due_date else None,
            "amount": float(r.amount) if r.amount else 0,
            "received_amount": float(r.received_amount) if r.received_amount else 0,
            "balance": float(r.amount - r.received_amount) if r.amount else 0
        } for r in receivables],
        "total_unreceived": total_unreceived
    }

@router.post("/api/receivables/create")
async def create_receivable(request: Request, db: Session = Depends(get_db)):
    """新增應收帳款 API"""
    form_data = await request.form()
    
    receivable_date = parse_date(form_data.get("receivable_date")) or date.today()
    
    receivable = ReceivableAccount(
        receivable_no=form_data.get("receivable_no") or generate_receivable_no(db, receivable_date),
        customer_id=int(form_data.get("customer_id")),
        sales_id=int(form_data.get("sales_id")) if form_data.get("sales_id") else None,
        receivable_date=receivable_date,
        due_date=parse_date(form_data.get("due_date")),
        amount=Decimal(form_data.get("amount") or 0),
        payment_method=form_data.get("payment_method"),
        notes=form_data.get("notes")
    )
    receivable.balance = receivable.amount
    
    db.add(receivable)
    db.commit()
    
    return {"success": True, "message": "應收帳款建立成功", "data": {"id": receivable.id}}

@router.post("/api/receivables/{receivable_id}/receive")
async def receive_receivable(receivable_id: int, request: Request, db: Session = Depends(get_db)):
    """沖帳應收帳款 API"""
    receivable = db.query(ReceivableAccount).filter(ReceivableAccount.id == receivable_id).first()
    if not receivable:
        raise HTTPException(status_code=404, detail="應收帳款不存在")
    
    form_data = await request.form()
    
    receive_amount = Decimal(form_data.get("receive_amount") or 0)
    payment_method = form_data.get("payment_method")
    payment_date = parse_date(form_data.get("payment_date")) or date.today()
    
    receivable.received_amount = (receivable.received_amount or 0) + receive_amount
    receivable.balance = receivable.amount - receivable.received_amount
    receivable.payment_method = payment_method
    receivable.payment_date = payment_date
    receivable.bank_name = form_data.get("bank_name")
    receivable.bank_account = form_data.get("bank_account")
    
    if receivable.balance <= 0:
        receivable.status = "已收款"
    elif receivable.received_amount > 0:
        receivable.status = "部分收款"
    
    db.commit()
    
    return {"success": True, "message": "沖帳成功"}

# 轉帳傳票 API
@router.post("/api/vouchers/create")
async def create_voucher(request: Request, db: Session = Depends(get_db)):
    """新增轉帳傳票 API"""
    form_data = await request.form()
    
    voucher_date = parse_date(form_data.get("voucher_date")) or date.today()
    
    voucher = TransferVoucher(
        voucher_no=form_data.get("voucher_no") or generate_voucher_no(db, voucher_date),
        voucher_date=voucher_date,
        voucher_type=form_data.get("voucher_type"),
        debit_account=form_data.get("debit_account"),
        debit_amount=Decimal(form_data.get("debit_amount") or 0),
        credit_account=form_data.get("credit_account"),
        credit_amount=Decimal(form_data.get("credit_amount") or 0),
        bank_name=form_data.get("bank_name"),
        bank_account=form_data.get("bank_account"),
        reference_no=form_data.get("reference_no"),
        description=form_data.get("description"),
        notes=form_data.get("notes")
    )
    
    db.add(voucher)
    db.commit()
    
    return {"success": True, "message": "轉帳傳票建立成功", "data": {"id": voucher.id}}

# 會計科目 API
@router.post("/api/accounts/create")
async def create_account_title(request: Request, db: Session = Depends(get_db)):
    """新增會計科目 API"""
    form_data = await request.form()
    
    account = AccountTitle(
        code=form_data.get("code"),
        name=form_data.get("name"),
        category=form_data.get("category"),
        parent_code=form_data.get("parent_code"),
        level=int(form_data.get("level", 1)),
        notes=form_data.get("notes")
    )
    
    db.add(account)
    db.commit()
    
    return {"success": True, "message": "會計科目建立成功", "data": {"id": account.id}}

@router.post("/api/accounts/init")
async def init_account_titles(db: Session = Depends(get_db)):
    """初始化基本會計科目"""
    default_accounts = [
        {"code": "1100", "name": "現金", "category": "資產", "level": 1},
        {"code": "1110", "name": "銀行存款", "category": "資產", "level": 1},
        {"code": "1200", "name": "應收帳款", "category": "資產", "level": 1},
        {"code": "1300", "name": "存貨", "category": "資產", "level": 1},
        {"code": "2100", "name": "應付帳款", "category": "負債", "level": 1},
        {"code": "2200", "name": "應付薪資", "category": "負債", "level": 1},
        {"code": "3100", "name": "資本", "category": "權益", "level": 1},
        {"code": "4100", "name": "銷貨收入", "category": "收入", "level": 1},
        {"code": "5100", "name": "進貨成本", "category": "費用", "level": 1},
        {"code": "5200", "name": "薪資費用", "category": "費用", "level": 1},
        {"code": "5300", "name": "飼料費用", "category": "費用", "level": 1},
        {"code": "5400", "name": "維修費用", "category": "費用", "level": 1},
        {"code": "5500", "name": "辦公費用", "category": "費用", "level": 1},
        {"code": "5600", "name": "其他費用", "category": "費用", "level": 1},
    ]
    
    for acc in default_accounts:
        existing = db.query(AccountTitle).filter(AccountTitle.code == acc["code"]).first()
        if not existing:
            db.add(AccountTitle(**acc))
    
    db.commit()
    
    return {"success": True, "message": "會計科目初始化成功"}
