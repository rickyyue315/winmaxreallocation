#!/bin/bash

# 調貨建議生成系統 v1.5 - 快速啟動腳本

echo "========================================="
echo "   調貨建議生成系統 v1.6"
echo "   由 Ricky 開發 | © 2025"
echo "========================================="
echo ""

# 檢查 Python 是否安裝
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤: 未找到 Python 安裝"
    echo "請先安裝 Python 3.8 或更高版本"
    exit 1
fi

# 確定 Python 命令
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "🔍 檢查依賴包..."

# 檢查是否需要安裝依賴
if ! $PYTHON_CMD -c "import streamlit, pandas, matplotlib" &> /dev/null; then
    echo "📦 安裝必要依賴包..."
    $PYTHON_CMD -m pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "❌ 依賴安裝失敗，請檢查網絡連接或手動安裝"
        exit 1
    fi
else
    echo "✅ 依賴包檢查完成"
fi

echo ""
echo "🚀 啟動調貨建議生成系統..."
echo "瀏覽器將自動打開 http://localhost:8501"
echo ""
echo "使用 Ctrl+C 停止服務"
echo ""

# 啟動 Streamlit 應用
$PYTHON_CMD -m streamlit run app.py
