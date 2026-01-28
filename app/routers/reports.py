"""
報表管理路由
Reports Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
import io

from app.database import get_db
from app.models.purchase import Purchase, PurchaseDetail, PurchaseMisc
from app.models.sales import Sales, SalesDetail, CattleDeath
from app.models.cattle import Cattle
from app.models.accounting import PayableAccount, ReceivableAccount
from app.models.payroll import Payroll
from app.models.customer import Customer
from app.models.supplier import Supplier

router = APIRouter(prefix="/reports", tags=["報表管理"])
templates = Jinja2Templates(directory="templates")

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
async def reports_index(request: Request):
    """報表首頁"""
    return templates.TemplateResponse("reports/index.html", {
        "request": request,
        "active_menu": "reports"
    })

@router.get("/cattle", response_class=HTMLResponse)
async def cattle_report_page(request: Request, db: Session = Depends(get_db)):
    """牛隻報表頁面"""
    return templates.TemplateResponse("reports/report.html", {
        "request": request,
        "active_menu": "reports",
        "report_type": "cattle",
        "report_title": "牛隻統計報表",
        "chart_data": {"labels": [], "data": []}
    })

@router.get("/purchase", response_class=HTMLResponse)
async def purchase_report_page(request: Request, db: Session = Depends(get_db)):
    """進貨年度報表頁面"""
    return templates.TemplateResponse("reports/report.html", {
        "request": request,
        "active_menu": "reports",
        "report_type": "purchase",
        "report_title": "進貨年度報表",
        "chart_data": {"labels": [], "data": []}
    })

@router.get("/sales", response_class=HTMLResponse)
async def sales_report_page(request: Request, db: Session = Depends(get_db)):
    """銷貨年度報表頁面"""
    return templates.TemplateResponse("reports/report.html", {
        "request": request,
        "active_menu": "reports",
        "report_type": "sales",
        "report_title": "銷貨年度報表",
        "chart_data": {"labels": [], "data": []}
    })

@router.get("/payable", response_class=HTMLResponse)
async def payable_report_page(request: Request, db: Session = Depends(get_db)):
    """應付帳款報表頁面"""
    return templates.TemplateResponse("reports/report.html", {
        "request": request,
        "active_menu": "reports",
        "report_type": "payable",
        "report_title": "應付帳款報表",
        "chart_data": {"labels": [], "data": []}
    })

@router.get("/receivable", response_class=HTMLResponse)
async def receivable_report_page(request: Request, db: Session = Depends(get_db)):
    """應收帳款報表頁面"""
    return templates.TemplateResponse("reports/report.html", {
        "request": request,
        "active_menu": "reports",
        "report_type": "receivable",
        "report_title": "應收帳款報表",
        "chart_data": {"labels": [], "data": []}
    })

@router.get("/profit", response_class=HTMLResponse)
async def profit_report_page(request: Request, db: Session = Depends(get_db)):
    """營利分析報表頁面"""
    from app.models.sales import Sales
    from app.models.purchase import Purchase
    from sqlalchemy import func
    
    # 計算營收與成本
    sales_revenue = db.query(func.sum(Sales.total_amount)).scalar() or 0
    purchase_cost = db.query(func.sum(Purchase.total_amount)).scalar() or 0
    gross_profit = float(sales_revenue) - float(purchase_cost)
    profit_margin = (gross_profit / float(sales_revenue) * 100) if sales_revenue > 0 else 0
    
    summary = {
        "sales_revenue": float(sales_revenue),
        "purchase_cost": float(purchase_cost),
        "gross_profit": gross_profit,
        "profit": gross_profit,  # 使用 gross_profit 作為 profit
        "profit_margin": profit_margin
    }
    
    return templates.TemplateResponse("reports/profit.html", {
        "request": request,
        "active_menu": "reports",
        "summary": summary,
        "chart_data": {"labels": [], "data": []}
    })

# ============== API 路由 ==============

@router.get("/api/purchase/yearly")
async def get_purchase_yearly_report(
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None)
):
    """進貨年度報表 API"""
    target_year = year or date.today().year
    
    # 月度統計
    monthly_stats = db.query(
        extract('month', Purchase.purchase_date).label('month'),
        func.sum(Purchase.total_amount),
        func.sum(Purchase.total_quantity)
    ).filter(
        extract('year', Purchase.purchase_date) == target_year
    ).group_by(extract('month', Purchase.purchase_date)).all()
    
    # 廠商統計
    supplier_stats = db.query(
        Supplier.name,
        func.sum(Purchase.total_amount),
        func.sum(Purchase.total_quantity)
    ).join(Purchase).filter(
        extract('year', Purchase.purchase_date) == target_year
    ).group_by(Supplier.id).all()
    
    # 類別統計
    category_stats = db.query(
        PurchaseDetail.category,
        func.count(PurchaseDetail.id),
        func.sum(PurchaseDetail.weight),
        func.sum(PurchaseDetail.amount)
    ).join(Purchase).filter(
        extract('year', Purchase.purchase_date) == target_year
    ).group_by(PurchaseDetail.category).all()
    
    # 雜項統計
    misc_stats = db.query(
        PurchaseMisc.category,
        func.sum(PurchaseMisc.amount)
    ).filter(
        extract('year', PurchaseMisc.misc_date) == target_year
    ).group_by(PurchaseMisc.category).all()
    
    # 總計
    total_amount = sum(m[1] or 0 for m in monthly_stats)
    total_quantity = sum(m[2] or 0 for m in monthly_stats)
    total_misc = sum(m[1] or 0 for m in misc_stats)
    
    return {
        "success": True,
        "data": {
            "year": target_year,
            "monthly_stats": [{
                "month": int(m[0]),
                "amount": float(m[1]) if m[1] else 0,
                "quantity": m[2] or 0
            } for m in monthly_stats],
            "supplier_stats": [{
                "name": s[0],
                "amount": float(s[1]) if s[1] else 0,
                "quantity": s[2] or 0
            } for s in supplier_stats],
            "category_stats": [{
                "category": c[0],
                "count": c[1],
                "weight": float(c[2]) if c[2] else 0,
                "amount": float(c[3]) if c[3] else 0
            } for c in category_stats],
            "misc_stats": [{
                "category": m[0],
                "amount": float(m[1]) if m[1] else 0
            } for m in misc_stats],
            "total_amount": float(total_amount),
            "total_quantity": total_quantity,
            "total_misc": float(total_misc),
            "grand_total": float(total_amount + total_misc)
        }
    }

@router.get("/api/sales/yearly")
async def get_sales_yearly_report(
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None)
):
    """銷貨年度報表 API"""
    target_year = year or date.today().year
    
    # 月度統計
    monthly_stats = db.query(
        extract('month', Sales.sales_date).label('month'),
        func.sum(Sales.total_amount),
        func.sum(Sales.total_quantity)
    ).filter(
        extract('year', Sales.sales_date) == target_year
    ).group_by(extract('month', Sales.sales_date)).all()
    
    # 客戶統計
    customer_stats = db.query(
        Customer.name,
        func.sum(Sales.total_amount),
        func.sum(Sales.total_quantity)
    ).join(Sales).filter(
        extract('year', Sales.sales_date) == target_year
    ).group_by(Customer.id).all()
    
    # 類別統計
    category_stats = db.query(
        SalesDetail.category,
        func.count(SalesDetail.id),
        func.sum(SalesDetail.weight),
        func.sum(SalesDetail.amount)
    ).join(Sales).filter(
        extract('year', Sales.sales_date) == target_year
    ).group_by(SalesDetail.category).all()
    
    # 死亡損失統計
    death_stats = db.query(
        func.count(CattleDeath.id),
        func.sum(CattleDeath.estimated_loss)
    ).filter(
        extract('year', CattleDeath.death_date) == target_year
    ).first()
    
    # 總計
    total_amount = sum(m[1] or 0 for m in monthly_stats)
    total_quantity = sum(m[2] or 0 for m in monthly_stats)
    
    return {
        "success": True,
        "data": {
            "year": target_year,
            "monthly_stats": [{
                "month": int(m[0]),
                "amount": float(m[1]) if m[1] else 0,
                "quantity": m[2] or 0
            } for m in monthly_stats],
            "customer_stats": [{
                "name": c[0],
                "amount": float(c[1]) if c[1] else 0,
                "quantity": c[2] or 0
            } for c in customer_stats],
            "category_stats": [{
                "category": c[0],
                "count": c[1],
                "weight": float(c[2]) if c[2] else 0,
                "amount": float(c[3]) if c[3] else 0
            } for c in category_stats],
            "death_count": death_stats[0] if death_stats else 0,
            "death_loss": float(death_stats[1]) if death_stats and death_stats[1] else 0,
            "total_amount": float(total_amount),
            "total_quantity": total_quantity
        }
    }

@router.get("/api/payable/yearly")
async def get_payable_yearly_report(
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None)
):
    """應付帳款年度報表 API"""
    target_year = year or date.today().year
    
    # 應付總額
    total_payable = db.query(func.sum(PayableAccount.amount)).filter(
        extract('year', PayableAccount.payable_date) == target_year
    ).scalar() or 0
    
    # 已付總額
    total_paid = db.query(func.sum(PayableAccount.paid_amount)).filter(
        extract('year', PayableAccount.payable_date) == target_year
    ).scalar() or 0
    
    # 未付總額
    total_unpaid = db.query(func.sum(PayableAccount.amount - PayableAccount.paid_amount)).filter(
        PayableAccount.status != "已付款"
    ).scalar() or 0
    
    # 廠商統計
    supplier_stats = db.query(
        Supplier.name,
        func.sum(PayableAccount.amount),
        func.sum(PayableAccount.paid_amount)
    ).join(PayableAccount).filter(
        extract('year', PayableAccount.payable_date) == target_year
    ).group_by(Supplier.id).all()
    
    return {
        "success": True,
        "data": {
            "year": target_year,
            "total_payable": float(total_payable),
            "total_paid": float(total_paid),
            "total_unpaid": float(total_unpaid),
            "supplier_stats": [{
                "name": s[0],
                "amount": float(s[1]) if s[1] else 0,
                "paid": float(s[2]) if s[2] else 0,
                "balance": float((s[1] or 0) - (s[2] or 0))
            } for s in supplier_stats]
        }
    }

@router.get("/api/receivable/yearly")
async def get_receivable_yearly_report(
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None)
):
    """應收帳款年度報表 API"""
    target_year = year or date.today().year
    
    # 應收總額
    total_receivable = db.query(func.sum(ReceivableAccount.amount)).filter(
        extract('year', ReceivableAccount.receivable_date) == target_year
    ).scalar() or 0
    
    # 已收總額
    total_received = db.query(func.sum(ReceivableAccount.received_amount)).filter(
        extract('year', ReceivableAccount.receivable_date) == target_year
    ).scalar() or 0
    
    # 未收總額
    total_unreceived = db.query(func.sum(ReceivableAccount.amount - ReceivableAccount.received_amount)).filter(
        ReceivableAccount.status != "已收款"
    ).scalar() or 0
    
    # 客戶統計
    customer_stats = db.query(
        Customer.name,
        func.sum(ReceivableAccount.amount),
        func.sum(ReceivableAccount.received_amount)
    ).join(ReceivableAccount).filter(
        extract('year', ReceivableAccount.receivable_date) == target_year
    ).group_by(Customer.id).all()
    
    return {
        "success": True,
        "data": {
            "year": target_year,
            "total_receivable": float(total_receivable),
            "total_received": float(total_received),
            "total_unreceived": float(total_unreceived),
            "customer_stats": [{
                "name": c[0],
                "amount": float(c[1]) if c[1] else 0,
                "received": float(c[2]) if c[2] else 0,
                "balance": float((c[1] or 0) - (c[2] or 0))
            } for c in customer_stats]
        }
    }

@router.get("/api/profit/analysis")
async def get_profit_analysis(
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None)
):
    """營利分析報表 API"""
    target_year = year or date.today().year
    
    # 銷貨收入
    sales_income = db.query(func.sum(Sales.total_amount)).filter(
        extract('year', Sales.sales_date) == target_year
    ).scalar() or 0
    
    # 進貨成本
    purchase_cost = db.query(func.sum(Purchase.total_amount)).filter(
        extract('year', Purchase.purchase_date) == target_year
    ).scalar() or 0
    
    # 雜項支出
    misc_cost = db.query(func.sum(PurchaseMisc.amount)).filter(
        extract('year', PurchaseMisc.misc_date) == target_year
    ).scalar() or 0
    
    # 薪資支出
    payroll_cost = db.query(func.sum(Payroll.total_amount)).filter(
        Payroll.payroll_year == target_year
    ).scalar() or 0
    
    # 死亡損失
    death_loss = db.query(func.sum(CattleDeath.estimated_loss)).filter(
        extract('year', CattleDeath.death_date) == target_year
    ).scalar() or 0
    
    # 總成本
    total_cost = float(purchase_cost) + float(misc_cost) + float(payroll_cost) + float(death_loss)
    
    # 毛利
    gross_profit = float(sales_income) - float(purchase_cost)
    
    # 淨利
    net_profit = float(sales_income) - total_cost
    
    # 月度分析
    monthly_analysis = []
    for month in range(1, 13):
        month_sales = db.query(func.sum(Sales.total_amount)).filter(
            extract('year', Sales.sales_date) == target_year,
            extract('month', Sales.sales_date) == month
        ).scalar() or 0
        
        month_purchase = db.query(func.sum(Purchase.total_amount)).filter(
            extract('year', Purchase.purchase_date) == target_year,
            extract('month', Purchase.purchase_date) == month
        ).scalar() or 0
        
        month_misc = db.query(func.sum(PurchaseMisc.amount)).filter(
            extract('year', PurchaseMisc.misc_date) == target_year,
            extract('month', PurchaseMisc.misc_date) == month
        ).scalar() or 0
        
        monthly_analysis.append({
            "month": month,
            "sales": float(month_sales),
            "purchase": float(month_purchase),
            "misc": float(month_misc),
            "profit": float(month_sales) - float(month_purchase) - float(month_misc)
        })
    
    return {
        "success": True,
        "data": {
            "year": target_year,
            "sales_income": float(sales_income),
            "purchase_cost": float(purchase_cost),
            "misc_cost": float(misc_cost),
            "payroll_cost": float(payroll_cost),
            "death_loss": float(death_loss),
            "total_cost": total_cost,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "profit_margin": round(net_profit / float(sales_income) * 100, 2) if sales_income else 0,
            "monthly_analysis": monthly_analysis
        }
    }

@router.get("/api/cattle/inventory")
async def get_cattle_inventory_report(db: Session = Depends(get_db)):
    """牛隻盤存報表"""
    # 在養統計
    in_farm_stats = db.query(
        Cattle.category,
        func.count(Cattle.id),
        func.sum(Cattle.entry_weight),
        func.sum(Cattle.current_weight)
    ).filter(
        Cattle.status == "在養",
        Cattle.is_archived == False
    ).group_by(Cattle.category).all()
    
    # 進出統計
    total_in = db.query(func.count(Cattle.id)).scalar() or 0
    total_sold = db.query(func.count(Cattle.id)).filter(Cattle.status == "已售出").scalar() or 0
    total_dead = db.query(func.count(Cattle.id)).filter(Cattle.status == "死亡").scalar() or 0
    total_in_farm = db.query(func.count(Cattle.id)).filter(Cattle.status == "在養").scalar() or 0
    
    return {
        "success": True,
        "data": {
            "in_farm_stats": [{
                "category": c[0],
                "count": c[1],
                "entry_weight": float(c[2]) if c[2] else 0,
                "current_weight": float(c[3]) if c[3] else 0
            } for c in in_farm_stats],
            "total_in": total_in,
            "total_sold": total_sold,
            "total_dead": total_dead,
            "total_in_farm": total_in_farm
        }
    }
