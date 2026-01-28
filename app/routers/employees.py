"""
員工管理路由
Employee Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, date

from app.database import get_db
from app.models.employee import Employee

router = APIRouter(prefix="/employees", tags=["員工管理"])
templates = Jinja2Templates(directory="templates")

def generate_employee_code(db: Session) -> str:
    """產生員工編號"""
    last_employee = db.query(Employee).order_by(Employee.id.desc()).first()
    if last_employee and last_employee.employee_code:
        try:
            last_num = int(last_employee.employee_code[1:])
            return f"E{str(last_num + 1).zfill(5)}"
        except:
            pass
    return "E00001"

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
async def employee_list_page(request: Request, db: Session = Depends(get_db)):
    """員工列表頁面"""
    employees = db.query(Employee).filter(Employee.is_active == True).order_by(Employee.id.desc()).all()
    return templates.TemplateResponse("employees/list.html", {
        "request": request,
        "employees": employees,
        "active_menu": "employees"
    })

@router.get("/create", response_class=HTMLResponse)
async def employee_create_page(request: Request, db: Session = Depends(get_db)):
    """新增員工頁面"""
    employee_code = generate_employee_code(db)
    return templates.TemplateResponse("employees/form.html", {
        "request": request,
        "employee_code": employee_code,
        "active_menu": "employees"
    })

@router.get("/{employee_id}/edit", response_class=HTMLResponse)
async def employee_edit_page(request: Request, employee_id: int, db: Session = Depends(get_db)):
    """編輯員工頁面"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="員工不存在")
    return templates.TemplateResponse("employees/form.html", {
        "request": request,
        "employee": employee,
        "active_menu": "employees"
    })

# ============== API 路由 ==============

@router.get("/api/list")
async def get_employees(
    db: Session = Depends(get_db),
    keyword: Optional[str] = Query(None, description="關鍵字搜尋"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得員工列表 API"""
    query = db.query(Employee).filter(Employee.is_active == True)
    
    if keyword:
        query = query.filter(or_(
            Employee.name.contains(keyword),
            Employee.mobile.contains(keyword),
            Employee.employee_code.contains(keyword),
            Employee.department.contains(keyword)
        ))
    
    total = query.count()
    employees = query.order_by(Employee.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": e.id,
            "employee_code": e.employee_code,
            "name": e.name,
            "gender": e.gender,
            "mobile": e.mobile,
            "department": e.department,
            "position": e.position,
            "hire_date": str(e.hire_date) if e.hire_date else None,
            "salary_type": e.salary_type,
            "base_salary": float(e.base_salary) if e.base_salary else 0
        } for e in employees],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/api/{employee_id}")
async def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """取得單一員工資料"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="員工不存在")
    return {"success": True, "data": employee}

@router.post("/api/create")
async def create_employee(request: Request, db: Session = Depends(get_db)):
    """新增員工 API"""
    form_data = await request.form()
    
    employee = Employee(
        employee_code=form_data.get("employee_code") or generate_employee_code(db),
        name=form_data.get("name"),
        id_number=form_data.get("id_number"),
        birth_date=parse_date(form_data.get("birth_date")),
        gender=form_data.get("gender"),
        hire_date=parse_date(form_data.get("hire_date")),
        address=form_data.get("address"),
        phone=form_data.get("phone"),
        mobile=form_data.get("mobile"),
        email=form_data.get("email"),
        emergency_contact=form_data.get("emergency_contact"),
        emergency_phone=form_data.get("emergency_phone"),
        department=form_data.get("department"),
        position=form_data.get("position"),
        salary_type=form_data.get("salary_type", "月薪"),
        base_salary=float(form_data.get("base_salary") or 0),
        bank_name=form_data.get("bank_name"),
        bank_account=form_data.get("bank_account"),
        labor_insurance=form_data.get("labor_insurance") == "on",
        health_insurance=form_data.get("health_insurance") == "on",
        notes=form_data.get("notes")
    )
    
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return {"success": True, "message": "員工建立成功", "data": {"id": employee.id}}

@router.post("/api/{employee_id}/update")
async def update_employee(employee_id: int, request: Request, db: Session = Depends(get_db)):
    """更新員工 API"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="員工不存在")
    
    form_data = await request.form()
    
    employee.name = form_data.get("name") or employee.name
    employee.id_number = form_data.get("id_number")
    employee.birth_date = parse_date(form_data.get("birth_date"))
    employee.gender = form_data.get("gender")
    employee.hire_date = parse_date(form_data.get("hire_date"))
    employee.address = form_data.get("address")
    employee.phone = form_data.get("phone")
    employee.mobile = form_data.get("mobile")
    employee.email = form_data.get("email")
    employee.emergency_contact = form_data.get("emergency_contact")
    employee.emergency_phone = form_data.get("emergency_phone")
    employee.department = form_data.get("department")
    employee.position = form_data.get("position")
    employee.salary_type = form_data.get("salary_type", "月薪")
    employee.base_salary = float(form_data.get("base_salary") or 0)
    employee.bank_name = form_data.get("bank_name")
    employee.bank_account = form_data.get("bank_account")
    employee.labor_insurance = form_data.get("labor_insurance") == "on"
    employee.health_insurance = form_data.get("health_insurance") == "on"
    employee.notes = form_data.get("notes")
    
    db.commit()
    
    return {"success": True, "message": "員工更新成功"}

@router.post("/api/{employee_id}/delete")
async def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """刪除員工 API (軟刪除)"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="員工不存在")
    
    employee.is_active = False
    employee.resign_date = date.today()
    db.commit()
    
    return {"success": True, "message": "員工已離職處理"}
