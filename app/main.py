"""
清發畜牧場管理系統 - 主程式
Ching Fa Cattle Farm Management System - Main Application
"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import os

from app.database import init_db, get_db
from app.config import settings
from app.routers import customers, suppliers, employees, purchases, sales, cattle, accounting, payroll, reports, system, auth

# 建立必要目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "images"), exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# 登入驗證中間件
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 不需要驗證的路徑
        public_paths = ["/auth/login", "/auth/init-admin", "/static"]
        
        # 檢查是否為公開路徑
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # 檢查是否有 access_token cookie
        access_token = request.cookies.get("access_token")
        if not access_token:
            return RedirectResponse(url="/auth/login", status_code=302)
        
        return await call_next(request)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期"""
    # 啟動時初始化資料庫
    init_db()
    yield
    # 關閉時的清理工作

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# 添加認證中間件
app.add_middleware(AuthMiddleware)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態檔案
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 模板
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# 註冊路由
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(suppliers.router)
app.include_router(employees.router)
app.include_router(cattle.router)
app.include_router(purchases.router)
app.include_router(sales.router)
app.include_router(accounting.router)
app.include_router(payroll.router)
app.include_router(reports.router)
app.include_router(system.router)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首頁 - 儀表板"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_menu": "dashboard"
    })

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(db = Depends(get_db)):
    """取得儀表板統計資料"""
    from sqlalchemy import func
    from datetime import date
    from app.models.cattle import Cattle
    from app.models.customer import Customer
    from app.models.supplier import Supplier
    from app.models.purchase import Purchase
    from app.models.sales import Sales
    
    # 牛隻統計
    cattle_in_farm = db.query(func.count(Cattle.id)).filter(
        Cattle.status == "在養",
        Cattle.is_archived == False
    ).scalar() or 0
    
    # 客戶數
    customer_count = db.query(func.count(Customer.id)).filter(
        Customer.is_active == True
    ).scalar() or 0
    
    # 廠商數
    supplier_count = db.query(func.count(Supplier.id)).filter(
        Supplier.is_active == True
    ).scalar() or 0
    
    # 本月進貨
    today = date.today()
    month_start = today.replace(day=1)
    month_purchase = db.query(func.sum(Purchase.total_amount)).filter(
        Purchase.purchase_date >= month_start
    ).scalar() or 0
    
    # 本月銷貨
    month_sales = db.query(func.sum(Sales.total_amount)).filter(
        Sales.sales_date >= month_start
    ).scalar() or 0
    
    return {
        "success": True,
        "data": {
            "cattle_in_farm": cattle_in_farm,
            "customer_count": customer_count,
            "supplier_count": supplier_count,
            "month_purchase": float(month_purchase),
            "month_sales": float(month_sales),
            "month_profit": float(month_sales) - float(month_purchase)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
