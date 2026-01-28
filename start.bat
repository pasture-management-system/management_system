@echo off
chcp 65001 >nul
cls

echo =========================================
echo    清發畜牧場管理系統
echo =========================================
echo.

REM 檢查 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo 錯誤: 找不到 Python，請先安裝 Python 3
    pause
    exit /b 1
)

REM 檢查虛擬環境
if not exist "venv" (
    echo 建立虛擬環境...
    python -m venv venv
)

REM 啟動虛擬環境
call venv\Scripts\activate.bat

REM 安裝依賴
echo 檢查並安裝依賴...
pip install -r requirements.txt -q

REM 建立必要目錄
if not exist "data" mkdir data
if not exist "backups" mkdir backups

REM 啟動應用
echo.
echo 啟動應用程式...
echo 請在瀏覽器開啟: http://localhost:8000
echo 預設帳號: admin / admin123
echo.
echo 按 Ctrl+C 停止服務
echo.

cd app
python main.py

pause
