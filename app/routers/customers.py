"""
客戶管理路由
Customer Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models.customer import Customer

router = APIRouter(prefix="/customers", tags=["客戶管理"])
templates = Jinja2Templates(directory="templates")

def generate_customer_code(db: Session) -> str:
    """產生客戶編號"""
    last_customer = db.query(Customer).order_by(Customer.id.desc()).first()
    if last_customer and last_customer.customer_code:
        try:
            last_num = int(last_customer.customer_code[1:])
            return f"C{str(last_num + 1).zfill(5)}"
        except:
            pass
    return "C00001"

# ============== 頁面路由 ==============

@router.get("/", response_class=HTMLResponse)
async def customer_list_page(request: Request, db: Session = Depends(get_db)):
    """客戶列表頁面"""
    customers = db.query(Customer).filter(Customer.is_active == True).order_by(Customer.id.desc()).all()
    return templates.TemplateResponse("customers/list.html", {
        "request": request,
        "customers": customers,
        "active_menu": "customers"
    })

@router.get("/create", response_class=HTMLResponse)
async def customer_create_page(request: Request, db: Session = Depends(get_db)):
    """新增客戶頁面"""
    customer_code = generate_customer_code(db)
    return templates.TemplateResponse("customers/form.html", {
        "request": request,
        "customer_code": customer_code,
        "active_menu": "customers"
    })

@router.get("/{customer_id}/edit", response_class=HTMLResponse)
async def customer_edit_page(request: Request, customer_id: int, db: Session = Depends(get_db)):
    """編輯客戶頁面"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客戶不存在")
    return templates.TemplateResponse("customers/form.html", {
        "request": request,
        "customer": customer,
        "active_menu": "customers"
    })

# ============== API 路由 ==============

@router.get("/api/list")
async def get_customers(
    db: Session = Depends(get_db),
    keyword: Optional[str] = Query(None, description="關鍵字搜尋"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得客戶列表 API"""
    query = db.query(Customer).filter(Customer.is_active == True)
    
    if keyword:
        query = query.filter(or_(
            Customer.name.contains(keyword),
            Customer.contact_person.contains(keyword),
            Customer.phone.contains(keyword),
            Customer.mobile.contains(keyword),
            Customer.tax_id.contains(keyword),
            Customer.customer_code.contains(keyword)
        ))
    
    total = query.count()
    customers = query.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": c.id,
            "customer_code": c.customer_code,
            "name": c.name,
            "contact_person": c.contact_person,
            "phone": c.phone,
            "mobile": c.mobile,
            "address": c.address,
            "tax_id": c.tax_id
        } for c in customers],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/api/{customer_id}")
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """取得單一客戶資料"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客戶不存在")
    return {"success": True, "data": customer}

@router.post("/api/create")
async def create_customer(request: Request, db: Session = Depends(get_db)):
    """新增客戶 API"""
    form_data = await request.form()
    
    customer = Customer(
        customer_code=form_data.get("customer_code") or generate_customer_code(db),
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
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return {"success": True, "message": "客戶建立成功", "data": {"id": customer.id}}

@router.post("/api/{customer_id}/update")
async def update_customer(customer_id: int, request: Request, db: Session = Depends(get_db)):
    """更新客戶 API"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客戶不存在")
    
    form_data = await request.form()
    
    customer.name = form_data.get("name") or customer.name
    customer.contact_person = form_data.get("contact_person")
    customer.address = form_data.get("address")
    customer.phone = form_data.get("phone")
    customer.fax = form_data.get("fax")
    customer.mobile = form_data.get("mobile")
    customer.tax_id = form_data.get("tax_id")
    customer.email = form_data.get("email")
    customer.bank_name = form_data.get("bank_name")
    customer.bank_account = form_data.get("bank_account")
    customer.notes = form_data.get("notes")
    
    db.commit()
    
    return {"success": True, "message": "客戶更新成功"}

@router.post("/api/{customer_id}/delete")
async def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """刪除客戶 API (軟刪除)"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客戶不存在")
    
    customer.is_active = False
    db.commit()
    
    return {"success": True, "message": "客戶已刪除"}
