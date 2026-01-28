"""
薪資管理路由
Payroll Router
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
from app.models.payroll import Payroll, PayrollDetail
from app.models.employee import Employee

router = APIRouter(prefix="/payroll", tags=["薪資管理"])
templates = Jinja2Templates(directory="templates")

def parse_date(date_str: str) -> Optional[date]:
    """解析日期字串"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return None

def generate_payroll_no(db: Session, year: int, month: int) -> str:
    """產生薪資單號"""
    roc_year = year - 1911
    prefix = f"PR{roc_year}{month:02d}"
    
    last = db.query(Payroll).filter(
        Payroll.payroll_no.like(f"{prefix}%")
    ).order_by(Payroll.payroll_no.desc()).first()
    
    if last:
        try:
            last_seq = int(last.payroll_no[-3:])
            return f"{prefix}{str(last_seq + 1).zfill(3)}"
        except:
            pass
    
    return f"{prefix}001"

# ============== 頁面路由 ==============

@router.get("/", response_class=HTMLResponse)
async def payroll_list_page(request: Request, db: Session = Depends(get_db)):
    """薪資單列表頁面"""
    payrolls = db.query(Payroll).order_by(Payroll.id.desc()).limit(100).all()
    return templates.TemplateResponse("payroll/list.html", {
        "request": request,
        "payrolls": payrolls,
        "active_menu": "payroll"
    })

@router.get("/create", response_class=HTMLResponse)
async def payroll_create_page(request: Request, db: Session = Depends(get_db)):
    """新增薪資單頁面"""
    today = date.today()
    payroll_no = generate_payroll_no(db, today.year, today.month)
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    return templates.TemplateResponse("payroll/form.html", {
        "request": request,
        "payroll_no": payroll_no,
        "employees": employees,
        "current_year": today.year,
        "current_month": today.month,
        "active_menu": "payroll"
    })

@router.get("/{payroll_id}", response_class=HTMLResponse)
async def payroll_detail_page(request: Request, payroll_id: int, db: Session = Depends(get_db)):
    """薪資單詳情頁面"""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="薪資單不存在")
    return templates.TemplateResponse("payroll/detail.html", {
        "request": request,
        "payroll": payroll,
        "active_menu": "payroll"
    })

@router.get("/{payroll_id}/edit", response_class=HTMLResponse)
async def payroll_edit_page(request: Request, payroll_id: int, db: Session = Depends(get_db)):
    """編輯薪資單頁面"""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="薪資單不存在")
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    return templates.TemplateResponse("payroll/form.html", {
        "request": request,
        "payroll": payroll,
        "employees": employees,
        "active_menu": "payroll"
    })

# ============== API 路由 ==============

@router.get("/api/list")
async def get_payrolls(
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """取得薪資單列表 API"""
    query = db.query(Payroll)
    
    if year:
        query = query.filter(Payroll.payroll_year == year)
    if month:
        query = query.filter(Payroll.payroll_month == month)
    if status:
        query = query.filter(Payroll.status == status)
    
    total = query.count()
    payrolls = query.order_by(Payroll.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": [{
            "id": p.id,
            "payroll_no": p.payroll_no,
            "payroll_year": p.payroll_year,
            "payroll_month": p.payroll_month,
            "total_employees": p.total_employees,
            "total_amount": float(p.total_amount) if p.total_amount else 0,
            "status": p.status,
            "pay_date": str(p.pay_date) if p.pay_date else None
        } for p in payrolls],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/api/{payroll_id}")
async def get_payroll(payroll_id: int, db: Session = Depends(get_db)):
    """取得單一薪資單"""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="薪資單不存在")
    
    details = [{
        "id": d.id,
        "employee_id": d.employee_id,
        "employee_name": d.employee.name if d.employee else None,
        "base_salary": float(d.base_salary) if d.base_salary else 0,
        "daily_wage": float(d.daily_wage) if d.daily_wage else 0,
        "work_days": d.work_days,
        "bonus": float(d.bonus) if d.bonus else 0,
        "full_attendance": float(d.full_attendance) if d.full_attendance else 0,
        "overtime_pay": float(d.overtime_pay) if d.overtime_pay else 0,
        "other_allowance": float(d.other_allowance) if d.other_allowance else 0,
        "labor_insurance": float(d.labor_insurance) if d.labor_insurance else 0,
        "health_insurance": float(d.health_insurance) if d.health_insurance else 0,
        "absence_deduction": float(d.absence_deduction) if d.absence_deduction else 0,
        "sick_leave_deduction": float(d.sick_leave_deduction) if d.sick_leave_deduction else 0,
        "other_deduction": float(d.other_deduction) if d.other_deduction else 0,
        "gross_salary": float(d.gross_salary) if d.gross_salary else 0,
        "total_deduction": float(d.total_deduction) if d.total_deduction else 0,
        "net_salary": float(d.net_salary) if d.net_salary else 0,
        "payment_method": d.payment_method,
        "is_paid": d.is_paid
    } for d in payroll.details]
    
    return {
        "success": True,
        "data": {
            "id": payroll.id,
            "payroll_no": payroll.payroll_no,
            "payroll_year": payroll.payroll_year,
            "payroll_month": payroll.payroll_month,
            "total_employees": payroll.total_employees,
            "total_amount": float(payroll.total_amount) if payroll.total_amount else 0,
            "status": payroll.status,
            "pay_date": str(payroll.pay_date) if payroll.pay_date else None,
            "details": details
        }
    }

@router.post("/api/create")
async def create_payroll(request: Request, db: Session = Depends(get_db)):
    """新增薪資單 API"""
    form_data = await request.form()
    
    year = int(form_data.get("payroll_year") or date.today().year)
    month = int(form_data.get("payroll_month") or date.today().month)
    
    # 檢查是否已存在該月薪資單
    existing = db.query(Payroll).filter(
        Payroll.payroll_year == year,
        Payroll.payroll_month == month
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"{year}年{month}月薪資單已存在")
    
    payroll = Payroll(
        payroll_no=form_data.get("payroll_no") or generate_payroll_no(db, year, month),
        payroll_year=year,
        payroll_month=month,
        pay_date=parse_date(form_data.get("pay_date")),
        notes=form_data.get("notes")
    )
    
    db.add(payroll)
    db.flush()
    
    # 取得所有在職員工
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    
    total_amount = Decimal(0)
    
    for emp in employees:
        # 計算薪資
        base_salary = emp.base_salary or Decimal(0)
        daily_wage = Decimal(form_data.get(f"emp_{emp.id}_daily_wage", 0) or 0)
        work_days = int(form_data.get(f"emp_{emp.id}_work_days", 0) or 0)
        bonus = Decimal(form_data.get(f"emp_{emp.id}_bonus", 0) or 0)
        full_attendance = Decimal(form_data.get(f"emp_{emp.id}_full_attendance", 0) or 0)
        overtime_pay = Decimal(form_data.get(f"emp_{emp.id}_overtime_pay", 0) or 0)
        other_allowance = Decimal(form_data.get(f"emp_{emp.id}_other_allowance", 0) or 0)
        
        labor_insurance = Decimal(form_data.get(f"emp_{emp.id}_labor_insurance", 0) or 0)
        health_insurance = Decimal(form_data.get(f"emp_{emp.id}_health_insurance", 0) or 0)
        absence_deduction = Decimal(form_data.get(f"emp_{emp.id}_absence_deduction", 0) or 0)
        sick_leave_deduction = Decimal(form_data.get(f"emp_{emp.id}_sick_leave_deduction", 0) or 0)
        other_deduction = Decimal(form_data.get(f"emp_{emp.id}_other_deduction", 0) or 0)
        
        # 計算應發薪資
        if emp.salary_type == "日薪":
            gross_salary = daily_wage * work_days + bonus + full_attendance + overtime_pay + other_allowance
        else:
            gross_salary = base_salary + bonus + full_attendance + overtime_pay + other_allowance
        
        # 計算扣款總計
        total_deduction = labor_insurance + health_insurance + absence_deduction + sick_leave_deduction + other_deduction
        
        # 計算實發薪資
        net_salary = gross_salary - total_deduction
        
        detail = PayrollDetail(
            payroll_id=payroll.id,
            employee_id=emp.id,
            base_salary=base_salary,
            daily_wage=daily_wage,
            work_days=work_days,
            bonus=bonus,
            full_attendance=full_attendance,
            overtime_pay=overtime_pay,
            other_allowance=other_allowance,
            labor_insurance=labor_insurance,
            health_insurance=health_insurance,
            absence_deduction=absence_deduction,
            sick_leave_deduction=sick_leave_deduction,
            other_deduction=other_deduction,
            gross_salary=gross_salary,
            total_deduction=total_deduction,
            net_salary=net_salary,
            payment_method=form_data.get(f"emp_{emp.id}_payment_method", "轉帳"),
            bank_name=emp.bank_name,
            bank_account=emp.bank_account
        )
        db.add(detail)
        
        total_amount += net_salary
    
    payroll.total_employees = len(employees)
    payroll.total_amount = total_amount
    
    db.commit()
    
    return {"success": True, "message": "薪資單建立成功", "data": {"id": payroll.id}}

@router.post("/api/{payroll_id}/confirm")
async def confirm_payroll(payroll_id: int, db: Session = Depends(get_db)):
    """確認薪資單"""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="薪資單不存在")
    
    payroll.status = "已確認"
    db.commit()
    
    return {"success": True, "message": "薪資單已確認"}

@router.post("/api/{payroll_id}/pay")
async def pay_payroll(payroll_id: int, request: Request, db: Session = Depends(get_db)):
    """發放薪資"""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="薪資單不存在")
    
    form_data = await request.form()
    pay_date = parse_date(form_data.get("pay_date")) or date.today()
    
    payroll.status = "已發放"
    payroll.pay_date = pay_date
    
    # 更新所有明細為已發放
    for detail in payroll.details:
        detail.is_paid = True
        detail.paid_date = pay_date
    
    db.commit()
    
    return {"success": True, "message": "薪資已發放"}

@router.post("/api/detail/{detail_id}/update")
async def update_payroll_detail(detail_id: int, request: Request, db: Session = Depends(get_db)):
    """更新薪資明細"""
    detail = db.query(PayrollDetail).filter(PayrollDetail.id == detail_id).first()
    if not detail:
        raise HTTPException(status_code=404, detail="薪資明細不存在")
    
    form_data = await request.form()
    
    detail.base_salary = Decimal(form_data.get("base_salary", 0) or 0)
    detail.daily_wage = Decimal(form_data.get("daily_wage", 0) or 0)
    detail.work_days = int(form_data.get("work_days", 0) or 0)
    detail.bonus = Decimal(form_data.get("bonus", 0) or 0)
    detail.full_attendance = Decimal(form_data.get("full_attendance", 0) or 0)
    detail.overtime_pay = Decimal(form_data.get("overtime_pay", 0) or 0)
    detail.other_allowance = Decimal(form_data.get("other_allowance", 0) or 0)
    detail.labor_insurance = Decimal(form_data.get("labor_insurance", 0) or 0)
    detail.health_insurance = Decimal(form_data.get("health_insurance", 0) or 0)
    detail.absence_deduction = Decimal(form_data.get("absence_deduction", 0) or 0)
    detail.sick_leave_deduction = Decimal(form_data.get("sick_leave_deduction", 0) or 0)
    detail.other_deduction = Decimal(form_data.get("other_deduction", 0) or 0)
    detail.payment_method = form_data.get("payment_method", "轉帳")
    
    # 重新計算
    if detail.employee and detail.employee.salary_type == "日薪":
        detail.gross_salary = detail.daily_wage * detail.work_days + detail.bonus + detail.full_attendance + detail.overtime_pay + detail.other_allowance
    else:
        detail.gross_salary = detail.base_salary + detail.bonus + detail.full_attendance + detail.overtime_pay + detail.other_allowance
    
    detail.total_deduction = detail.labor_insurance + detail.health_insurance + detail.absence_deduction + detail.sick_leave_deduction + detail.other_deduction
    detail.net_salary = detail.gross_salary - detail.total_deduction
    
    # 更新薪資單總額
    payroll = detail.payroll
    payroll.total_amount = sum(d.net_salary for d in payroll.details)
    
    db.commit()
    
    return {"success": True, "message": "薪資明細更新成功"}

@router.get("/api/statistics")
async def get_payroll_statistics(
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None)
):
    """取得薪資統計"""
    query = db.query(Payroll)
    
    if year:
        query = query.filter(Payroll.payroll_year == year)
    
    # 年度薪資總額
    total_amount = query.with_entities(func.sum(Payroll.total_amount)).scalar() or 0
    
    # 各月薪資統計
    monthly_stats = db.query(
        Payroll.payroll_month,
        func.sum(Payroll.total_amount),
        func.sum(Payroll.total_employees)
    ).filter(
        Payroll.payroll_year == (year or date.today().year)
    ).group_by(Payroll.payroll_month).all()
    
    return {
        "success": True,
        "data": {
            "total_amount": float(total_amount),
            "monthly_stats": [{
                "month": m[0],
                "amount": float(m[1]) if m[1] else 0,
                "employees": m[2] or 0
            } for m in monthly_stats]
        }
    }
