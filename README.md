# 📦 調貨建議生成系統 v1.7a

## 系統概述

零售庫存調貨建議生成系統，基於Streamlit開發，提供智慧化的庫存調貨分析和建議。

## 主要功能

- ✅ ND/RF類型智慧識別
- ✅ 優先順序調貨匹配  
- ✅ RF過剩/加強轉出限制
- ✅ 統計分析和圖表
- ✅ Excel格式匯出

## 技術棧

- **前端：** Streamlit (>=1.28.0)
- **資料處理：** pandas (>=2.0.0), numpy (>=1.24.0)
- **Excel處理：** openpyxl (>=3.1.0)
- **視覺化：** matplotlib (>=3.7.0), seaborn (>=0.12.0)

## 安裝與運行

1. 安裝依賴包：
```bash
pip install -r requirements.txt
```

2. 運行應用：
```bash
streamlit run app.py
```

或使用快捷腳本：
```bash
# Windows
run.bat

# Linux/macOS
./run.sh
```

## 輸入數據格式

系統需要Excel文件包含以下必需欄位：

- Article (str) - 產品編號
- Article Description (str) - 產品描述
- RP Type (str) - 補貨類型：ND（不補貨）或 RF（補貨）
- Site (str) - 店鋪編號
- OM (str) - 營運管理單位
- MOQ (int) - 最低派貨數量
- SaSa Net Stock (int) - 現有庫存數量
- Pending Received (int) - 在途訂單數量
- Safety Stock (int) - 安全庫存數量
- Last Month Sold Qty (int) - 上月銷量
- MTD Sold Qty (int) - 本月至今銷量

## 核心業務邏輯

### A模式：保守轉貨
- RF類型：(庫存+在途) × 20%限制，最少2件
- 優先轉出低銷量店鋪的過剩庫存

### B模式：加強轉貨
- RF類型：(庫存+在途) × 50%限制，最少2件
- 基於MOQ+1件的安全邊際
- 優先轉出銷量最低的店鋪

## 版本歷史

詳見 [VERSION.md](VERSION.md)

## 開發者

**Ricky** - 系統架構與開發

---

*最後更新：2025-09-18*
