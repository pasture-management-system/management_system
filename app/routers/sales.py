"""
銷貨管理路由
Sales Router
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
from app.models.sales import Sales, SalesDetail, CattleDeath
from app.models.customer import Customer
from app.models.cattle import Cattle

router = APIRouter(prefix="/sales", tags=["銷貨管理"])
templates = Jinja2Templates(directory="templates")

def generate_sales_no(db: Session, sales_date: date) -> str:
    """
    產生銷貨單號
    格式: SXXXXX(年月)XXX(流水號) 例: S11411001
    """
    roc_year = sales_date.year - 1911
    prefix = f"S{roc_year}{sales_date.month:02d}"
    
    last_sales = db.query(Sales).filter(
        Sales.sales_no.like(f"{prefix}%")
    ).order_by(Sales.sales_no.desc()).first()
    
    if last_sales:
        try:
            last_seq = int(last_sales.sales_no[-3:])
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

# ============== 頁面路由 ==============

@router.get("/", response_class=HTMLResponse)
async def sales_list_page(request: Request, db: Session = Depends(get_db)):
    """銷貨單列表頁面"""
    sales_list = db.query(Sales).order_by(Sales.id.desc()).limit(100).all()
    return templates.TemplateResponse("sales/list.html", {
        "request": request,
        "sales_list": sales_list,
        "active_menu": "sales"
    })

@router.get("/create", response_class=HTMLResponse)
async def sales_create_page(request: Request, db: Session = Depends(get_db)):
    """新增銷貨單頁面"""
    sales_no = generate_sales_no(db, date.today())
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    available_cattle = db.query(Cattle).filter(
        Cattle.status == "在養",
        Cattle.is_archived == False
    ).order_by(Cattle.entry_date.desc()).all()
    
    return templates.TemplateResponse("sales/form.html", {
        "request": request,
        "sales_no": sales_no,
        "customers": customers,
        "available_cattle": available_cattle,
        "active_menu": "sales"
    })

@router.get("/{sales_id}", response_class=HTMLResponse)
async def sales_detail_page(request: Request, sales_id: int, db: Session = Depends(get_db)):
    """銷貨單詳情頁面"""
    sale = db.query(Sales).filter(Sales.id == sales_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="銷貨單不存在")
    return templates.TemplateResponse("sales/detail.html", {
        "request": request,
        "sale": sale,
        "active_menu": "sales"
    })

@router.get("/{sales_id}/edit", response_class=HTMLResponse)
async def sales_edit_page(request: Request, sales_id: int, db: Session = Depends(get_db)):
    """編輯銷貨單頁面"""
    sale = db.query(Sales).filter(Sales.id == sales_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="銷貨單不存在")
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    available_cattle = db.query(Cattle).filter(
        Cattle.status == "在養",
        Cattle.is_archived == False
    ).order_by(Cattle.entry_date.desc()).all()
    
    return templates.TemplateResponse("sales/form.html", {
        "request": request,
        "sale": sale,
        "customers": customers,
        "available_cattle": available_cattle,
        "active_menu": "sales"
    })

# 死亡記錄頁面
@router.get("/deaths/list", response_class=HTMLResponse)
async def death_list_page(request: Request, db: Session = Depends(get_db)):
    """牛隻死亡記錄列表"""
    deaths = db.query(CattleDeath).order_by(CattleDeath.id.desc()).limit(100).all()
    return templates.TemplateResponse("sales/death_list.html", {
        "request": request,
        "deaths": deaths,
        "active_menu": "sales"
    })

# ============== API 路由 ==============

@router.get("/api/list")
async def get_sales(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得銷貨單列表 API"""
    query = db.query(Sales)
    
    if start_date:
        query = query.filter(Sales.sales_date >= parse_date(start_date))
    if end_date:
        query = query.filter(Sales.sales_date <= parse_date(end_date))
    if customer_id:
        query = query.filter(Sales.customer_id == customer_id)
    
    total = query.count()
    sales_list = query.order_by(Sales.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": s.id,
            "sales_no": s.sales_no,
            "sales_date": str(s.sales_date) if s.sales_date else None,
            "customer_name": s.customer.name if s.customer else None,
            "total_amount": float(s.total_amount) if s.total_amount else 0,
            "total_quantity": s.total_quantity,
            "payment_status": s.payment_status
        } for s in sales_list],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/api/statistics")
async def get_sales_statistics(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """取得銷貨統計"""
    query = db.query(Sales)
    
    if start_date:
        query = query.filter(Sales.sales_date >= parse_date(start_date))
    if end_date:
        query = query.filter(Sales.sales_date <= parse_date(end_date))
    
    # 總金額
    total_amount = query.with_entities(func.sum(Sales.total_amount)).scalar() or 0
    
    # 總數量
    total_quantity = query.with_entities(func.sum(Sales.total_quantity)).scalar() or 0
    
    # 各客戶銷貨統計
    by_customer = db.query(
        Customer.name,
        func.sum(Sales.total_amount),
        func.sum(Sales.total_quantity)
    ).join(Sales).group_by(Customer.id).all()
    
    # 各類別統計
    category_stats = db.query(
        SalesDetail.category,
        func.count(SalesDetail.id),
        func.sum(SalesDetail.weight),
        func.sum(SalesDetail.amount)
    ).group_by(SalesDetail.category).all()
    
    # 死亡損失統計
    death_count = db.query(func.count(CattleDeath.id)).scalar() or 0
    death_loss = db.query(func.sum(CattleDeath.estimated_loss)).scalar() or 0
    
    return {
        "success": True,
        "data": {
            "total_amount": float(total_amount),
            "total_quantity": total_quantity,
            "by_customer": [{
                "name": c[0],
                "amount": float(c[1]) if c[1] else 0,
                "quantity": c[2] or 0
            } for c in by_customer],
            "by_category": [{
                "category": c[0],
                "count": c[1],
                "total_weight": float(c[2]) if c[2] else 0,
                "total_amount": float(c[3]) if c[3] else 0
            } for c in category_stats],
            "death_count": death_count,
            "death_loss": float(death_loss)
        }
    }

@router.post("/api/create")
async def create_sales(request: Request, db: Session = Depends(get_db)):
    """新增銷貨單 API"""
    form_data = await request.form()
    
    sales_date = parse_date(form_data.get("sales_date")) or date.today()
    sales_no = form_data.get("sales_no") or generate_sales_no(db, sales_date)
    
    sale = Sales(
        sales_no=sales_no,
        sales_date=sales_date,
        customer_id=int(form_data.get("customer_id")),
        notes=form_data.get("notes")
    )
    
    db.add(sale)
    db.flush()
    
    # 處理明細
    detail_count = int(form_data.get("detail_count", 0))
    total_amount = Decimal(0)
    total_quantity = 0
    
    for i in range(detail_count):
        cattle_id = int(form_data.get(f"details[{i}][cattle_id]"))
        cattle = db.query(Cattle).filter(Cattle.id == cattle_id).first()
        
        if not cattle:
            continue
        
        weight = Decimal(form_data.get(f"details[{i}][weight]", 0) or cattle.current_weight or 0)
        unit_price = Decimal(form_data.get(f"details[{i}][unit_price]", 0) or 0)
        amount = weight * unit_price
        
        # 計算畜牧天數
        feeding_days = (sales_date - cattle.entry_date).days if cattle.entry_date else 0
        
        # 建立銷貨明細
        detail = SalesDetail(
            sales_id=sale.id,
            cattle_id=cattle.id,
            cattle_serial=cattle.serial_number,
            category=cattle.category,
            weight=weight,
            unit_price=unit_price,
            amount=amount,
            feeding_days=feeding_days,
            notes=form_data.get(f"details[{i}][notes]")
        )
        db.add(detail)
        
        # 更新牛隻狀態
        cattle.status = "已售出"
        cattle.exit_date = sales_date
        cattle.exit_weight = weight
        cattle.feeding_days = feeding_days
        cattle.is_archived = True
        
        total_amount += amount
        total_quantity += 1
    
    sale.total_amount = total_amount
    sale.total_quantity = total_quantity
    
    db.commit()
    
    return {"success": True, "message": "銷貨單建立成功", "data": {"id": sale.id, "sales_no": sale.sales_no}}

@router.post("/api/death/create")
async def create_death_record(request: Request, db: Session = Depends(get_db)):
    """新增牛隻死亡記錄 API"""
    form_data = await request.form()
    
    cattle_id = int(form_data.get("cattle_id"))
    cattle = db.query(Cattle).filter(Cattle.id == cattle_id).first()
    
    if not cattle:
        raise HTTPException(status_code=404, detail="牛隻不存在")
    
    death_date = parse_date(form_data.get("death_date")) or date.today()
    
    # 建立死亡記錄
    death = CattleDeath(
        cattle_id=cattle.id,
        cattle_serial=cattle.serial_number,
        death_date=death_date,
        death_reason=form_data.get("death_reason"),
        estimated_loss=Decimal(form_data.get("estimated_loss", 0) or cattle.total_price or 0),
        notes=form_data.get("notes")
    )
    db.add(death)
    
    # 更新牛隻狀態
    cattle.status = "死亡"
    cattle.death_date = death_date
    cattle.death_reason = form_data.get("death_reason")
    cattle.is_archived = True
    
    if cattle.entry_date:
        cattle.feeding_days = (death_date - cattle.entry_date).days
    
    db.commit()
    
    return {"success": True, "message": "死亡記錄建立成功", "data": {"id": death.id}}

@router.get("/api/deaths/list")
async def get_death_records(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得死亡記錄列表 API"""
    query = db.query(CattleDeath)
    
    if start_date:
        query = query.filter(CattleDeath.death_date >= parse_date(start_date))
    if end_date:
        query = query.filter(CattleDeath.death_date <= parse_date(end_date))
    
    total = query.count()
    deaths = query.order_by(CattleDeath.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": d.id,
            "cattle_serial": d.cattle_serial,
            "death_date": str(d.death_date) if d.death_date else None,
            "death_reason": d.death_reason,
            "estimated_loss": float(d.estimated_loss) if d.estimated_loss else 0
        } for d in deaths],
        "total": total,
        "page": page,
        "page_size": page_size
    }
