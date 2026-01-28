"""
系統管理路由
System Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import shutil
from datetime import datetime, date
import sqlite3

from app.database import get_db, DATABASE_DIR
from app.config import settings

router = APIRouter(prefix="/system", tags=["系統管理"])
templates = Jinja2Templates(directory="templates")

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# ============== 頁面路由 ==============

@router.get("/", response_class=HTMLResponse)
async def system_index(request: Request, db: Session = Depends(get_db)):
    """系統管理首頁"""
    from app.models.customer import Customer
    from app.models.supplier import Supplier
    from app.models.employee import Employee
    from app.models.cattle import Cattle
    from sqlalchemy import func
    
    # 統計數據
    stats = {
        "customers": db.query(func.count(Customer.id)).scalar() or 0,
        "suppliers": db.query(func.count(Supplier.id)).scalar() or 0,
        "employees": db.query(func.count(Employee.id)).scalar() or 0,
        "cattle": db.query(func.count(Cattle.id)).filter(Cattle.status == "在場").scalar() or 0
    }
    
    # 資料庫資訊
    db_path = os.path.join(DATABASE_DIR, "cattle_farm.db")
    db_info = {
        "size": os.path.getsize(db_path) if os.path.exists(db_path) else 0,
        "path": db_path,
        "last_modified": datetime.fromtimestamp(os.path.getmtime(db_path)).strftime("%Y-%m-%d %H:%M:%S") if os.path.exists(db_path) else "N/A"
    }
    
    return templates.TemplateResponse("system/index.html", {
        "request": request,
        "active_menu": "system",
        "stats": stats,
        "db_info": db_info
    })

@router.get("/backup", response_class=HTMLResponse)
async def backup_page(request: Request):
    """資料備份頁面"""
    # 列出現有備份
    backups = []
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            if f.endswith('.db'):
                filepath = os.path.join(BACKUP_DIR, f)
                stat = os.stat(filepath)
                backups.append({
                    "filename": f,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                })
    
    backups.sort(key=lambda x: x['created'], reverse=True)
    
    return templates.TemplateResponse("system/backup.html", {
        "request": request,
        "backups": backups,
        "active_menu": "system"
    })

@router.get("/maintenance", response_class=HTMLResponse)
async def maintenance_page(request: Request):
    """系統維護頁面"""
    return templates.TemplateResponse("system/maintenance.html", {
        "request": request,
        "active_menu": "system"
    })

# ============== API 路由 ==============

@router.post("/api/backup/create")
async def create_backup(db: Session = Depends(get_db)):
    """建立資料備份"""
    try:
        # 資料庫檔案路徑
        db_path = os.path.join(DATABASE_DIR, "cattle_farm.db")
        
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="資料庫檔案不存在")
        
        # 產生備份檔名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"cattle_farm_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # 複製資料庫檔案
        shutil.copy2(db_path, backup_path)
        
        return {
            "success": True,
            "message": "備份建立成功",
            "data": {
                "filename": backup_filename,
                "path": backup_path
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"備份失敗: {str(e)}")

@router.get("/api/backup/download/{filename}")
async def download_backup(filename: str):
    """下載備份檔案"""
    backup_path = os.path.join(BACKUP_DIR, filename)
    
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="備份檔案不存在")
    
    return FileResponse(
        backup_path,
        media_type="application/octet-stream",
        filename=filename
    )

@router.post("/api/backup/restore/{filename}")
async def restore_backup(filename: str, db: Session = Depends(get_db)):
    """還原備份"""
    try:
        backup_path = os.path.join(BACKUP_DIR, filename)
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="備份檔案不存在")
        
        db_path = os.path.join(DATABASE_DIR, "cattle_farm.db")
        
        # 先備份現有資料庫
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore_backup = os.path.join(BACKUP_DIR, f"pre_restore_{timestamp}.db")
        if os.path.exists(db_path):
            shutil.copy2(db_path, pre_restore_backup)
        
        # 還原備份
        shutil.copy2(backup_path, db_path)
        
        return {
            "success": True,
            "message": "備份還原成功，請重新啟動系統"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"還原失敗: {str(e)}")

@router.delete("/api/backup/{filename}")
async def delete_backup(filename: str):
    """刪除備份"""
    backup_path = os.path.join(BACKUP_DIR, filename)
    
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="備份檔案不存在")
    
    os.remove(backup_path)
    
    return {"success": True, "message": "備份已刪除"}

@router.get("/api/backup/list")
async def list_backups():
    """列出所有備份"""
    backups = []
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            if f.endswith('.db'):
                filepath = os.path.join(BACKUP_DIR, f)
                stat = os.stat(filepath)
                backups.append({
                    "filename": f,
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                })
    
    backups.sort(key=lambda x: x['created'], reverse=True)
    
    return {"success": True, "data": backups}

@router.post("/api/maintenance/vacuum")
async def vacuum_database(db: Session = Depends(get_db)):
    """資料庫重整 (VACUUM)"""
    try:
        db.execute(text("VACUUM"))
        return {"success": True, "message": "資料庫重整完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重整失敗: {str(e)}")

@router.post("/api/maintenance/analyze")
async def analyze_database(db: Session = Depends(get_db)):
    """資料庫分析 (ANALYZE)"""
    try:
        db.execute(text("ANALYZE"))
        return {"success": True, "message": "資料庫分析完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")

@router.post("/api/maintenance/integrity-check")
async def integrity_check(db: Session = Depends(get_db)):
    """資料庫完整性檢查"""
    try:
        result = db.execute(text("PRAGMA integrity_check")).fetchall()
        is_ok = len(result) == 1 and result[0][0] == "ok"
        return {
            "success": True,
            "is_ok": is_ok,
            "message": "資料庫完整性正常" if is_ok else "資料庫有問題",
            "details": [r[0] for r in result]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檢查失敗: {str(e)}")

@router.get("/api/status")
async def get_system_status(db: Session = Depends(get_db)):
    """取得系統狀態"""
    try:
        # 資料庫檔案大小
        db_path = os.path.join(DATABASE_DIR, "cattle_farm.db")
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        # 備份數量
        backup_count = len([f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]) if os.path.exists(BACKUP_DIR) else 0
        
        # 最後備份時間
        last_backup = None
        if os.path.exists(BACKUP_DIR):
            backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
            if backups:
                latest = max(backups, key=lambda f: os.path.getctime(os.path.join(BACKUP_DIR, f)))
                last_backup = datetime.fromtimestamp(os.path.getctime(os.path.join(BACKUP_DIR, latest))).strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "success": True,
            "data": {
                "db_size": db_size,
                "db_size_mb": round(db_size / 1024 / 1024, 2),
                "backup_count": backup_count,
                "last_backup": last_backup,
                "app_version": settings.APP_VERSION
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得狀態失敗: {str(e)}")

@router.post("/api/maintenance/optimize")
async def optimize_system(db: Session = Depends(get_db)):
    """系統重整優化"""
    try:
        # 1. VACUUM - 重整資料庫
        db.execute(text("VACUUM"))
        
        # 2. ANALYZE - 更新統計資訊
        db.execute(text("ANALYZE"))
        
        # 3. 建立備份
        db_path = os.path.join(DATABASE_DIR, "cattle_farm.db")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"auto_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
        
        return {
            "success": True,
            "message": "系統重整完成並已建立備份",
            "data": {
                "backup_file": backup_filename
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系統重整失敗: {str(e)}")
