"""
認證路由
Authentication Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.config import settings

router = APIRouter(prefix="/auth", tags=["認證"])

templates = Jinja2Templates(directory="templates")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"密碼驗證錯誤: {e}")
        return False

def get_password_hash(password: str) -> str:
    """加密密碼"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登入頁面"""
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    """處理登入"""
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "帳號或密碼錯誤"
        })
    
    if not user.is_active:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "此帳號已被停用"
        })
    
    # 更新最後登入時間
    user.last_login = datetime.now()
    db.commit()
    
    # 建立 token
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/logout")
async def logout():
    """登出"""
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

@router.get("/init-admin")
async def init_admin(db: Session = Depends(get_db)):
    """初始化管理員帳號"""
    existing_admin = db.query(User).filter(User.username == "admin").first()
    if existing_admin:
        return {"message": "管理員帳號已存在"}
    
    admin = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        name="系統管理員",
        role="admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    return {"message": "管理員帳號建立成功", "username": "admin", "password": "admin123"}
