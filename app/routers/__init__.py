"""
路由初始化
Routers initialization
"""
from app.routers import customers, suppliers, employees, purchases, sales, cattle, accounting, payroll, reports, system, auth

__all__ = [
    "customers",
    "suppliers",
    "employees",
    "purchases",
    "sales",
    "cattle",
    "accounting",
    "payroll",
    "reports",
    "system",
    "auth"
]
