# 調貨建議生成系統 v1.6 - 部署指南

## 系統概述
這是一個基於 Streamlit 的智能調貨建議生成系統，專為優化庫存調配而設計。

## 版本更新記錄
- **v1.6**: 條形圖改為按調貨類型分布，使用指定顏色和英文標籤避免亂碼
- **v1.5**: 修復條形圖中文顯示亂碼問題，改用英文顯示
- **v1.4**: 更新統計分析用詞為"涉及行數"
- **v1.3**: 新增調貨數量優化功能（1件自動調升為2件）
- **v1.2**: 完善業務邏輯和統計功能
- **v1.1**: 基礎功能實現

## 系統功能特點
✅ **智能調貨算法**: 基於庫存、銷量和安全庫存的智能匹配
✅ **數量優化**: 自動將1件調貨優化為2件（在安全範圍內）
✅ **RF過剩限制**: 20%轉出上限，最少2件機制
✅ **新版圖表**: 按調貨類型分布的條形圖，使用指定顏色
✅ **完整統計**: 多維度數據分析
✅ **Excel導出**: 一鍵生成完整報告

## 新版圖表特色 (v1.6)
📊 **按調貨類型分布顯示**:
- 🔵 ND Transfer (深藍色 #1f4788)
- 🔷 RF Excess Transfer (淺藍色 #4682B4)
- 🟠 Emergency Shortage (深橘色 #FF4500)
- 🍊 Potential Shortage (淺橘色 #FF8C69)

## 安裝部署

### 環境要求
- Python 3.8+
- 操作系統: Windows/MacOS/Linux

### 快速部署步驟

1. **解壓項目文件**
   ```bash
   unzip stock_transfer_app_v1.6_final.zip
   cd stock_transfer_app_v1.6_final
   ```

2. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

3. **啟動應用**
   ```bash
   streamlit run app.py
   ```

4. **訪問系統**
   在瀏覽器中打開：http://localhost:8501

### Docker 部署（可選）

創建 Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

構建並運行:
```bash
docker build -t stock-transfer-app .
docker run -p 8501:8501 stock-transfer-app
```

## 使用指南

### 1. 數據準備
確保Excel文件包含以下必要欄位：
- Article (產品編號)
- Article Description (產品描述)
- RP Type (轉出類型：ND或RF)
- Site (店鋪編號)
- OM (營運管理單位)
- SaSa Net Stock (現有庫存)
- Pending Received (在途訂單)
- Safety Stock (安全庫存)
- Last Month Sold Qty (上月銷量)
- MTD Sold Qty (本月至今銷量)

### 2. 操作流程
1. 上傳Excel數據文件
2. 系統自動進行數據驗證和預處理
3. 點擊"開始分析"生成調貨建議
4. 查看分析結果和新版類型分布圖表
5. 下載Excel格式的完整報告

### 3. 業務規則說明

**轉出優先級：**
1. ND類型：全部可用庫存
2. RF過剩：超出安全庫存的20%（最少2件）

**接收優先級：**
1. 緊急缺貨：庫存為0且有銷量
2. 潛在缺貨：總庫存低於安全庫存且為最高銷量

**數量優化：**
- 當調貨數量為1件時，自動檢查是否可升級為2件
- 條件：轉出店鋪調貨後庫存仍≥安全庫存

## v1.6 新功能亮點

### 圖表優化
- **按類型分布**: 不再只顯示轉出/接收總量，改為顯示詳細的調貨類型分布
- **色彩編碼**: 使用直觀的顏色區分不同調貨類型
- **英文標籤**: 完全避免中文顯示亂碼問題
- **分組顯示**: 按OM單位分組，便於比較分析

### 視覺改進
- 更大的圖表尺寸 (14x8)
- 圖例位置優化，不遮擋數據
- 數值標籤清晰顯示
- 專業的配色方案

## 故障排除

### 常見問題

**Q: 上傳文件後顯示錯誤**
A: 檢查Excel文件格式和必要欄位是否完整

**Q: 圖表顯示異常**
A: v1.6版本已優化圖表顯示，使用英文標籤和指定顏色

**Q: 沒有生成調貨建議**
A: 檢查數據是否符合業務規則條件

### 技術支持
如遇到技術問題，請檢查：
1. Python版本是否符合要求
2. 依賴包是否正確安裝
3. 數據格式是否標準

## 開發信息
- **開發者**: Ricky
- **版本**: v1.6
- **更新日期**: 2025年
- **技術框架**: Streamlit + Pandas + Matplotlib

---
*由 Ricky 開發 | © 2025*
