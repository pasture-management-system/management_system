"""
牛隻管理路由
Cattle Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
from datetime import datetime, date

from app.database import get_db
from app.models.cattle import Cattle
from app.models.supplier import Supplier

router = APIRouter(prefix="/cattle", tags=["牛隻管理"])
templates = Jinja2Templates(directory="templates")

def generate_cattle_serial(db: Session, category: str, entry_date: date) -> str:
    """
    產生牛隻身份編號
    格式: X(類別)XXXXXXX(年月日)XX(流水號)
    例: S114112101, K114112101
    """
    # 計算民國年
    roc_year = entry_date.year - 1911
    date_str = f"{roc_year}{entry_date.month:02d}{entry_date.day:02d}"
    
    # 查詢當日同類別最後一筆
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
async def cattle_list_page(request: Request, db: Session = Depends(get_db)):
    """牛隻列表頁面"""
    cattle_list = db.query(Cattle).filter(Cattle.is_archived == False).order_by(Cattle.id.desc()).all()
    return templates.TemplateResponse("cattle/list.html", {
        "request": request,
        "cattle_list": cattle_list,
        "active_menu": "cattle"
    })

@router.get("/create", response_class=HTMLResponse)
async def cattle_create_page(request: Request, db: Session = Depends(get_db)):
    """新增牛隻頁面"""
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    return templates.TemplateResponse("cattle/form.html", {
        "request": request,
        "suppliers": suppliers,
        "active_menu": "cattle"
    })

@router.get("/{cattle_id}", response_class=HTMLResponse)
async def cattle_detail_page(request: Request, cattle_id: int, db: Session = Depends(get_db)):
    """牛隻詳情頁面"""
    cattle = db.query(Cattle).filter(Cattle.id == cattle_id).first()
    if not cattle:
        raise HTTPException(status_code=404, detail="牛隻不存在")
    
    # 計算畜牧天數
    if cattle.exit_date:
        feeding_days = (cattle.exit_date - cattle.entry_date).days
    else:
        feeding_days = (date.today() - cattle.entry_date).days
    
    return templates.TemplateResponse("cattle/detail.html", {
        "request": request,
        "cattle": cattle,
        "feeding_days": feeding_days,
        "active_menu": "cattle"
    })

@router.get("/{cattle_id}/edit", response_class=HTMLResponse)
async def cattle_edit_page(request: Request, cattle_id: int, db: Session = Depends(get_db)):
    """編輯牛隻頁面"""
    cattle = db.query(Cattle).filter(Cattle.id == cattle_id).first()
    if not cattle:
        raise HTTPException(status_code=404, detail="牛隻不存在")
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    return templates.TemplateResponse("cattle/form.html", {
        "request": request,
        "cattle": cattle,
        "suppliers": suppliers,
        "active_menu": "cattle"
    })

# ============== API 路由 ==============

@router.get("/api/list")
async def get_cattle_list(
    db: Session = Depends(get_db),
    keyword: Optional[str] = Query(None, description="關鍵字搜尋"),
    category: Optional[str] = Query(None, description="類別: S=小牛, K=整隻牛"),
    status: Optional[str] = Query(None, description="狀態"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得牛隻列表 API"""
    query = db.query(Cattle).filter(Cattle.is_archived == False)
    
    if keyword:
        query = query.filter(or_(
            Cattle.serial_number.contains(keyword),
            Cattle.notes.contains(keyword)
        ))
    
    if category:
        query = query.filter(Cattle.category == category)
    
    if status:
        query = query.filter(Cattle.status == status)
    
    total = query.count()
    cattle_list = query.order_by(Cattle.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": c.id,
            "serial_number": c.serial_number,
            "category": c.category,
            "entry_date": str(c.entry_date) if c.entry_date else None,
            "entry_weight": float(c.entry_weight) if c.entry_weight else None,
            "current_weight": float(c.current_weight) if c.current_weight else None,
            "status": c.status,
            "feeding_days": (date.today() - c.entry_date).days if c.entry_date else 0
        } for c in cattle_list],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/api/available")
async def get_available_cattle(db: Session = Depends(get_db)):
    """取得可售牛隻列表"""
    cattle_list = db.query(Cattle).filter(
        Cattle.status == "在養",
        Cattle.is_archived == False
    ).order_by(Cattle.entry_date.desc()).all()
    
    return {
        "success": True,
        "data": [{
            "id": c.id,
            "serial_number": c.serial_number,
            "category": c.category,
            "entry_date": str(c.entry_date) if c.entry_date else None,
            "entry_weight": float(c.entry_weight) if c.entry_weight else None,
            "current_weight": float(c.current_weight) if c.current_weight else None,
            "feeding_days": (date.today() - c.entry_date).days if c.entry_date else 0
        } for c in cattle_list]
    }

@router.get("/api/statistics")
async def get_cattle_statistics(db: Session = Depends(get_db)):
    """取得牛隻統計"""
    # 在養數量
    in_farm = db.query(func.count(Cattle.id)).filter(
        Cattle.status == "在養",
        Cattle.is_archived == False
    ).scalar()
    
    # 已售出數量
    sold = db.query(func.count(Cattle.id)).filter(
        Cattle.status == "已售出"
    ).scalar()
    
    # 死亡數量
    dead = db.query(func.count(Cattle.id)).filter(
        Cattle.status == "死亡"
    ).scalar()
    
    # 按類別統計
    by_category = db.query(
        Cattle.category,
        func.count(Cattle.id)
    ).filter(
        Cattle.status == "在養",
        Cattle.is_archived == False
    ).group_by(Cattle.category).all()
    
    return {
        "success": True,
        "data": {
            "in_farm": in_farm,
            "sold": sold,
            "dead": dead,
            "by_category": {c[0]: c[1] for c in by_category}
        }
    }

@router.post("/api/create")
async def create_cattle(request: Request, db: Session = Depends(get_db)):
    """新增牛隻 API"""
    form_data = await request.form()
    
    category = form_data.get("category", "S")
    entry_date = parse_date(form_data.get("entry_date")) or date.today()
    serial_number = form_data.get("serial_number") or generate_cattle_serial(db, category, entry_date)
    
    cattle = Cattle(
        serial_number=serial_number,
        category=category,
        supplier_id=int(form_data.get("supplier_id")) if form_data.get("supplier_id") else None,
        entry_date=entry_date,
        entry_weight=float(form_data.get("entry_weight") or 0),
        current_weight=float(form_data.get("current_weight") or form_data.get("entry_weight") or 0),
        unit_price=float(form_data.get("unit_price") or 0),
        status="在養",
        notes=form_data.get("notes")
    )
    
    # 計算總價
    cattle.total_price = cattle.entry_weight * cattle.unit_price if cattle.entry_weight and cattle.unit_price else 0
    
    db.add(cattle)
    db.commit()
    db.refresh(cattle)
    
    return {"success": True, "message": "牛隻建立成功", "data": {"id": cattle.id, "serial_number": cattle.serial_number}}

@router.post("/api/{cattle_id}/update")
async def update_cattle(cattle_id: int, request: Request, db: Session = Depends(get_db)):
    """更新牛隻 API"""
    cattle = db.query(Cattle).filter(Cattle.id == cattle_id).first()
    if not cattle:
        raise HTTPException(status_code=404, detail="牛隻不存在")
    
    form_data = await request.form()
    
    cattle.current_weight = float(form_data.get("current_weight") or cattle.current_weight or 0)
    cattle.status = form_data.get("status") or cattle.status
    cattle.notes = form_data.get("notes")
    
    # 更新畜牧天數
    if cattle.entry_date:
        cattle.feeding_days = (date.today() - cattle.entry_date).days
    
    db.commit()
    
    return {"success": True, "message": "牛隻更新成功"}

@router.post("/api/{cattle_id}/death")
async def record_cattle_death(cattle_id: int, request: Request, db: Session = Depends(get_db)):
    """記錄牛隻死亡"""
    cattle = db.query(Cattle).filter(Cattle.id == cattle_id).first()
    if not cattle:
        raise HTTPException(status_code=404, detail="牛隻不存在")
    
    form_data = await request.form()
    
    cattle.status = "死亡"
    cattle.death_date = parse_date(form_data.get("death_date")) or date.today()
    cattle.death_reason = form_data.get("death_reason")
    cattle.is_archived = True
    
    # 計算畜牧天數
    if cattle.entry_date:
        cattle.feeding_days = (cattle.death_date - cattle.entry_date).days
    
    db.commit()
    
    return {"success": True, "message": "牛隻死亡記錄已建立"}
