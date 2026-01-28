#!/bin/bash

# 清發畜牧場管理系統 - 啟動腳本

echo "========================================="
echo "   清發畜牧場管理系統"
echo "========================================="
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "錯誤: 找不到 Python 3，請先安裝 Python 3"
    exit 1
fi

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "建立虛擬環境..."
    python3 -m venv venv
fi

# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴
echo "檢查並安裝依賴..."
pip install -r requirements.txt -q

# 建立必要目錄
mkdir -p data backups

# 啟動應用
echo ""
echo "啟動應用程式..."
echo "請在瀏覽器開啟: http://localhost:8000"
echo "預設帳號: admin / admin123"
echo ""
echo "按 Ctrl+C 停止服務"
echo ""

cd app
python main.py
