"""
廠商管理路由
Supplier Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.supplier import Supplier

router = APIRouter(prefix="/suppliers", tags=["廠商管理"])
templates = Jinja2Templates(directory="templates")

def generate_supplier_code(db: Session) -> str:
    """產生廠商編號"""
    last_supplier = db.query(Supplier).order_by(Supplier.id.desc()).first()
    if last_supplier and last_supplier.supplier_code:
        try:
            last_num = int(last_supplier.supplier_code[1:])
            return f"V{str(last_num + 1).zfill(5)}"
        except:
            pass
    return "V00001"

# ============== 頁面路由 ==============

@router.get("/", response_class=HTMLResponse)
async def supplier_list_page(request: Request, db: Session = Depends(get_db)):
    """廠商列表頁面"""
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.id.desc()).all()
    return templates.TemplateResponse("suppliers/list.html", {
        "request": request,
        "suppliers": suppliers,
        "active_menu": "suppliers"
    })

@router.get("/create", response_class=HTMLResponse)
async def supplier_create_page(request: Request, db: Session = Depends(get_db)):
    """新增廠商頁面"""
    supplier_code = generate_supplier_code(db)
    return templates.TemplateResponse("suppliers/form.html", {
        "request": request,
        "supplier_code": supplier_code,
        "active_menu": "suppliers"
    })

@router.get("/{supplier_id}/edit", response_class=HTMLResponse)
async def supplier_edit_page(request: Request, supplier_id: int, db: Session = Depends(get_db)):
    """編輯廠商頁面"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="廠商不存在")
    return templates.TemplateResponse("suppliers/form.html", {
        "request": request,
        "supplier": supplier,
        "active_menu": "suppliers"
    })

# ============== API 路由 ==============

@router.get("/api/list")
async def get_suppliers(
    db: Session = Depends(get_db),
    keyword: Optional[str] = Query(None, description="關鍵字搜尋"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得廠商列表 API"""
    query = db.query(Supplier).filter(Supplier.is_active == True)
    
    if keyword:
        query = query.filter(or_(
            Supplier.name.contains(keyword),
            Supplier.contact_person.contains(keyword),
            Supplier.phone.contains(keyword),
            Supplier.mobile.contains(keyword),
            Supplier.tax_id.contains(keyword),
            Supplier.supplier_code.contains(keyword)
        ))
    
    total = query.count()
    suppliers = query.order_by(Supplier.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": s.id,
            "supplier_code": s.supplier_code,
            "name": s.name,
            "contact_person": s.contact_person,
            "phone": s.phone,
            "mobile": s.mobile,
            "address": s.address,
            "tax_id": s.tax_id
        } for s in suppliers],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/api/{supplier_id}")
async def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """取得單一廠商資料"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="廠商不存在")
    return {"success": True, "data": supplier}

@router.post("/api/create")
async def create_supplier(request: Request, db: Session = Depends(get_db)):
    """新增廠商 API"""
    form_data = await request.form()
    
    supplier = Supplier(
        supplier_code=form_data.get("supplier_code") or generate_supplier_code(db),
        name=form_data.get("name"),
        contact_person=form_data.get("contact_person"),
        address=form_data.get("address"),
        phone=form_data.get("phone"),
        fax=form_data.get("fax"),
        mobile=form_data.get("mobile"),
        tax_id=form_data.get("tax_id"),
        email=form_data.get("email"),
        bank_name=form_data.get("bank_name"),
        bank_account=form_data.get("bank_account"),
        notes=form_data.get("notes")
    )
    
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    
    return {"success": True, "message": "廠商建立成功", "data": {"id": supplier.id}}

@router.post("/api/{supplier_id}/update")
async def update_supplier(supplier_id: int, request: Request, db: Session = Depends(get_db)):
    """更新廠商 API"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="廠商不存在")
    
    form_data = await request.form()
    
    supplier.name = form_data.get("name") or supplier.name
    supplier.contact_person = form_data.get("contact_person")
    supplier.address = form_data.get("address")
    supplier.phone = form_data.get("phone")
    supplier.fax = form_data.get("fax")
    supplier.mobile = form_data.get("mobile")
    supplier.tax_id = form_data.get("tax_id")
    supplier.email = form_data.get("email")
    supplier.bank_name = form_data.get("bank_name")
    supplier.bank_account = form_data.get("bank_account")
    supplier.notes = form_data.get("notes")
    
    db.commit()
    
    return {"success": True, "message": "廠商更新成功"}

@router.post("/api/{supplier_id}/delete")
async def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """刪除廠商 API (軟刪除)"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="廠商不存在")
    
    supplier.is_active = False
    db.commit()
    
    return {"success": True, "message": "廠商已刪除"}
