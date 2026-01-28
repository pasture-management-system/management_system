"""
進貨管理路由
Purchase Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from app.database import get_db
from app.models.purchase import Purchase, PurchaseDetail, PurchaseMisc
from app.models.supplier import Supplier
from app.models.cattle import Cattle

router = APIRouter(prefix="/purchases", tags=["進貨管理"])
templates = Jinja2Templates(directory="templates")

def generate_purchase_no(db: Session, purchase_date: date) -> str:
    """
    產生進貨單號
    格式: PXXXXX(年月)XXX(流水號) 例: P11411001
    """
    roc_year = purchase_date.year - 1911
    prefix = f"P{roc_year}{purchase_date.month:02d}"
    
    last_purchase = db.query(Purchase).filter(
        Purchase.purchase_no.like(f"{prefix}%")
    ).order_by(Purchase.purchase_no.desc()).first()
    
    if last_purchase:
        try:
            last_seq = int(last_purchase.purchase_no[-3:])
            return f"{prefix}{str(last_seq + 1).zfill(3)}"
        except:
            pass
    
    return f"{prefix}001"

def generate_misc_no(db: Session, misc_date: date) -> str:
    """產生雜項單號"""
    roc_year = misc_date.year - 1911
    prefix = f"M{roc_year}{misc_date.month:02d}"
    
    last_misc = db.query(PurchaseMisc).filter(
        PurchaseMisc.misc_no.like(f"{prefix}%")
    ).order_by(PurchaseMisc.misc_no.desc()).first()
    
    if last_misc:
        try:
            last_seq = int(last_misc.misc_no[-3:])
            return f"{prefix}{str(last_seq + 1).zfill(3)}"
        except:
            pass
    
    return f"{prefix}001"

def parse_date(date_str: str) -> Optional[date]:
    """解析日期字串"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return None

def generate_cattle_serial(db: Session, category: str, entry_date: date) -> str:
    """產生牛隻身份編號"""
    roc_year = entry_date.year - 1911
    date_str = f"{roc_year}{entry_date.month:02d}{entry_date.day:02d}"
    prefix = f"{category}{date_str}"
    
    last_cattle = db.query(Cattle).filter(
        Cattle.serial_number.like(f"{prefix}%")
    ).order_by(Cattle.serial_number.desc()).first()
    
    if last_cattle:
        try:
            last_seq = int(last_cattle.serial_number[-2:])
            return f"{prefix}{str(last_seq + 1).zfill(2)}"
        except:
            pass
    
    return f"{prefix}01"

# ============== 頁面路由 ==============

@router.get("/", response_class=HTMLResponse)
async def purchase_list_page(request: Request, db: Session = Depends(get_db)):
    """進貨單列表頁面"""
    purchases = db.query(Purchase).order_by(Purchase.id.desc()).limit(100).all()
    return templates.TemplateResponse("purchases/list.html", {
        "request": request,
        "purchases": purchases,
        "active_menu": "purchases"
    })

@router.get("/create", response_class=HTMLResponse)
async def purchase_create_page(request: Request, db: Session = Depends(get_db)):
    """新增進貨單頁面"""
    purchase_no = generate_purchase_no(db, date.today())
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    return templates.TemplateResponse("purchases/form.html", {
        "request": request,
        "purchase_no": purchase_no,
        "suppliers": suppliers,
        "active_menu": "purchases"
    })

@router.get("/{purchase_id}", response_class=HTMLResponse)
async def purchase_detail_page(request: Request, purchase_id: int, db: Session = Depends(get_db)):
    """進貨單詳情頁面"""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="進貨單不存在")
    return templates.TemplateResponse("purchases/detail.html", {
        "request": request,
        "purchase": purchase,
        "active_menu": "purchases"
    })

@router.get("/{purchase_id}/edit", response_class=HTMLResponse)
async def purchase_edit_page(request: Request, purchase_id: int, db: Session = Depends(get_db)):
    """編輯進貨單頁面"""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="進貨單不存在")
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    return templates.TemplateResponse("purchases/form.html", {
        "request": request,
        "purchase": purchase,
        "suppliers": suppliers,
        "active_menu": "purchases"
    })

# 雜項進貨頁面
@router.get("/misc/list", response_class=HTMLResponse)
async def misc_list_page(request: Request, db: Session = Depends(get_db)):
    """雜項進貨列表頁面"""
    misc_list = db.query(PurchaseMisc).order_by(PurchaseMisc.id.desc()).limit(100).all()
    return templates.TemplateResponse("purchases/misc_list.html", {
        "request": request,
        "misc_list": misc_list,
        "active_menu": "purchases"
    })

@router.get("/misc/create", response_class=HTMLResponse)
async def misc_create_page(request: Request, db: Session = Depends(get_db)):
    """新增雜項進貨頁面"""
    misc_no = generate_misc_no(db, date.today())
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    return templates.TemplateResponse("purchases/misc_form.html", {
        "request": request,
        "misc_no": misc_no,
        "suppliers": suppliers,
        "active_menu": "purchases"
    })

# ============== API 路由 ==============

@router.get("/api/list")
async def get_purchases(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得進貨單列表 API"""
    query = db.query(Purchase)
    
    if start_date:
        query = query.filter(Purchase.purchase_date >= parse_date(start_date))
    if end_date:
        query = query.filter(Purchase.purchase_date <= parse_date(end_date))
    if supplier_id:
        query = query.filter(Purchase.supplier_id == supplier_id)
    
    total = query.count()
    purchases = query.order_by(Purchase.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": p.id,
            "purchase_no": p.purchase_no,
            "purchase_date": str(p.purchase_date) if p.purchase_date else None,
            "supplier_name": p.supplier.name if p.supplier else None,
            "total_amount": float(p.total_amount) if p.total_amount else 0,
            "total_quantity": p.total_quantity,
            "payment_status": p.payment_status
        } for p in purchases],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/api/statistics")
async def get_purchase_statistics(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """取得進貨統計"""
    query = db.query(Purchase)
    
    if start_date:
        query = query.filter(Purchase.purchase_date >= parse_date(start_date))
    if end_date:
        query = query.filter(Purchase.purchase_date <= parse_date(end_date))
    
    # 總金額
    total_amount = query.with_entities(func.sum(Purchase.total_amount)).scalar() or 0
    
    # 總數量
    total_quantity = query.with_entities(func.sum(Purchase.total_quantity)).scalar() or 0
    
    # 各廠商進貨統計
    by_supplier = db.query(
        Supplier.name,
        func.sum(Purchase.total_amount),
        func.sum(Purchase.total_quantity)
    ).join(Purchase).group_by(Supplier.id).all()
    
    # 各類別統計
    cattle_stats = db.query(
        Cattle.category,
        func.count(Cattle.id),
        func.sum(Cattle.entry_weight)
    ).filter(Cattle.is_archived == False).group_by(Cattle.category).all()
    
    return {
        "success": True,
        "data": {
            "total_amount": float(total_amount),
            "total_quantity": total_quantity,
            "by_supplier": [{
                "name": s[0],
                "amount": float(s[1]) if s[1] else 0,
                "quantity": s[2] or 0
            } for s in by_supplier],
            "by_category": [{
                "category": c[0],
                "count": c[1],
                "total_weight": float(c[2]) if c[2] else 0
            } for c in cattle_stats]
        }
    }

@router.post("/api/create")
async def create_purchase(request: Request, db: Session = Depends(get_db)):
    """新增進貨單 API"""
    form_data = await request.form()
    
    purchase_date = parse_date(form_data.get("purchase_date")) or date.today()
    purchase_no = form_data.get("purchase_no") or generate_purchase_no(db, purchase_date)
    
    purchase = Purchase(
        purchase_no=purchase_no,
        purchase_date=purchase_date,
        supplier_id=int(form_data.get("supplier_id")),
        notes=form_data.get("notes")
    )
    
    db.add(purchase)
    db.flush()
    
    # 處理明細
    detail_count = int(form_data.get("detail_count", 0))
    total_amount = Decimal(0)
    total_quantity = 0
    
    for i in range(detail_count):
        category = form_data.get(f"details[{i}][category]", "S")
        weight = Decimal(form_data.get(f"details[{i}][weight]", 0) or 0)
        unit_price = Decimal(form_data.get(f"details[{i}][unit_price]", 0) or 0)
        amount = weight * unit_price
        
        # 產生牛隻身份編號
        cattle_serial = generate_cattle_serial(db, category, purchase_date)
        
        # 建立進貨明細
        detail = PurchaseDetail(
            purchase_id=purchase.id,
            cattle_serial=cattle_serial,
            category=category,
            weight=weight,
            unit_price=unit_price,
            amount=amount,
            notes=form_data.get(f"details[{i}][notes]")
        )
        db.add(detail)
        db.flush()
        
        # 建立牛隻記錄
        cattle = Cattle(
            serial_number=cattle_serial,
            category=category,
            purchase_id=purchase.id,
            purchase_detail_id=detail.id,
            supplier_id=purchase.supplier_id,
            entry_date=purchase_date,
            entry_weight=weight,
            current_weight=weight,
            unit_price=unit_price,
            total_price=amount,
            status="在養"
        )
        db.add(cattle)
        
        total_amount += amount
        total_quantity += 1
    
    purchase.total_amount = total_amount
    purchase.total_quantity = total_quantity
    
    db.commit()
    
    return {"success": True, "message": "進貨單建立成功", "data": {"id": purchase.id, "purchase_no": purchase.purchase_no}}

@router.post("/api/misc/create")
async def create_misc_purchase(request: Request, db: Session = Depends(get_db)):
    """新增雜項進貨 API"""
    form_data = await request.form()
    
    misc_date = parse_date(form_data.get("misc_date")) or date.today()
    misc_no = form_data.get("misc_no") or generate_misc_no(db, misc_date)
    
    quantity = Decimal(form_data.get("quantity", 1) or 1)
    unit_price = Decimal(form_data.get("unit_price", 0) or 0)
    
    misc = PurchaseMisc(
        misc_no=misc_no,
        misc_date=misc_date,
        category=form_data.get("category"),
        supplier_id=int(form_data.get("supplier_id")) if form_data.get("supplier_id") else None,
        item_name=form_data.get("item_name"),
        quantity=quantity,
        unit=form_data.get("unit"),
        unit_price=unit_price,
        amount=quantity * unit_price,
        notes=form_data.get("notes")
    )
    
    db.add(misc)
    db.commit()
    
    return {"success": True, "message": "雜項進貨建立成功", "data": {"id": misc.id}}

@router.get("/api/misc/list")
async def get_misc_purchases(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得雜項進貨列表 API"""
    query = db.query(PurchaseMisc)
    
    if start_date:
        query = query.filter(PurchaseMisc.misc_date >= parse_date(start_date))
    if end_date:
        query = query.filter(PurchaseMisc.misc_date <= parse_date(end_date))
    if category:
        query = query.filter(PurchaseMisc.category == category)
    
    total = query.count()
    misc_list = query.order_by(PurchaseMisc.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": m.id,
            "misc_no": m.misc_no,
            "misc_date": str(m.misc_date) if m.misc_date else None,
            "category": m.category,
            "item_name": m.item_name,
            "quantity": float(m.quantity) if m.quantity else 0,
            "unit": m.unit,
            "amount": float(m.amount) if m.amount else 0,
            "payment_status": m.payment_status
        } for m in misc_list],
        "total": total,
        "page": page,
        "page_size": page_size
    }
