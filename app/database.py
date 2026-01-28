"""
資料庫連接設定
Database connection configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 資料庫路徑
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'cattle_farm.db')}"

# 建立引擎
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False
)

# Session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基底類別
Base = declarative_base()

def get_db():
    """取得資料庫 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化資料庫"""
    from app.models import customer, supplier, employee, cattle, purchase, sales, accounting, payroll, user
    
    # 創建所有表
    Base.metadata.create_all(bind=engine)
    
    # 檢查並創建預設管理員帳號
    db = SessionLocal()
    try:
        from app.models.user import User
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            # 使用 bcrypt 直接加密
            import bcrypt
            password = "admin123"
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            admin = User(
                username="admin",
                password_hash=password_hash,
                name="系統管理員",
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("✓ 已創建預設管理員帳號: admin / admin123")
        else:
            print("✓ 管理員帳號已存在")
    except Exception as e:
        print(f"初始化管理員帳號時發生錯誤: {e}")
        db.rollback()
    finally:
        db.close()
