@echo off
chcp 65001 >nul

echo =========================================
echo    調貨建議生成系統 v1.6
echo    由 Ricky 開發 ^| © 2025
echo =========================================
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤: 未找到 Python 安裝
    echo 請先安裝 Python 3.8 或更高版本
    pause
    exit /b 1
)

echo 🔍 檢查依賴包...

REM 檢查是否需要安裝依賴
python -c "import streamlit, pandas, matplotlib" >nul 2>&1
if errorlevel 1 (
    echo 📦 安裝必要依賴包...
    python -m pip install -r requirements.txt
    
    if errorlevel 1 (
        echo ❌ 依賴安裝失敗，請檢查網絡連接或手動安裝
        pause
        exit /b 1
    )
) else (
    echo ✅ 依賴包檢查完成
)

echo.
echo 🚀 啟動調貨建議生成系統...
echo 瀏覽器將自動打開 http://localhost:8501
echo.
echo 使用 Ctrl+C 停止服務
echo.

REM 啟動 Streamlit 應用
python -m streamlit run app.py

pause
