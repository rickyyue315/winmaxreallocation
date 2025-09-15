# 📦 調貨建議生成系統 - 使用說明

## 系統概述

這是一個基於Streamlit的智能調貨建議生成系統，專門為優化庫存分配而設計。系統根據庫存、銷量和安全庫存數據，自動生成跨店鋪的商品調貨建議。

### 🚀 核心優化功能

- **RF類型過剩轉出新限制**：轉出上限為存貨+Pending Received的20%，且最少2件
- **智能優先級匹配**：ND類型優先，RF類型按需分配
- **完整統計分析**：提供多維度數據分析
- **Excel格式輸出**：專業格式報告下載

## 📋 業務規則詳解

### 轉出規則（按優先順序）

#### 1. 優先級1：ND類型轉出
- **條件**：`RP Type` = "ND"
- **可轉數量**：全部 `SaSa Net Stock`

#### 2. 優先級2：RF類型過剩轉出（新優化）
- **條件**：
  - `RP Type` = "RF"
  - 庫存充足：`SaSa Net Stock` + `Pending Received` > `Safety Stock`
  - 銷量非最高：該店鋪的有效銷量不是該Article和OM組合中的最高值
- **轉出上限計算**：
  ```python
  基本可轉數量 = (SaSa Net Stock + Pending Received) - Safety Stock
  上限限制 = (SaSa Net Stock + Pending Received) × 20%
  最終可轉數量 = min(基本可轉數量, max(上限限制, 2))
  ```
- **最少轉出**：2件

### 接收規則（按優先順序）

#### 1. 優先級1：緊急缺貨補貨
- **條件**：
  - `RP Type` = "RF"
  - 完全無庫存：`SaSa Net Stock` = 0
  - 曾有銷量：有效銷量 > 0
- **需求數量**：`Safety Stock`

#### 2. 優先級2：潛在缺貨補貨
- **條件**：
  - `RP Type` = "RF"
  - 庫存不足：`SaSa Net Stock` + `Pending Received` < `Safety Stock`
  - 銷量最高：該店鋪的有效銷量是該Article和OM組合中的最高值
- **需求數量**：`Safety Stock` - (`SaSa Net Stock` + `Pending Received`)

## 🖥️ 系統界面功能

### 1. 數據上傳區
- 支持手動上傳Excel文件（.xlsx, .xls格式）
- 實時數據驗證和預處理
- 清晰的數據要求說明

### 2. 數據預覽區
- 顯示基本統計信息（記錄數、產品數、店鋪數等）
- RP Type分布圖表
- 關鍵欄位數據樣本展示

### 3. 分析執行區
- 一鍵生成調貨建議
- 實時進度顯示
- 智能匹配算法執行

### 4. 結果展示區
- KPI儀表板（總建議數、總調貨件數、涉及產品數、涉及OM數）
- 調貨建議明細表格
- 多維度統計分析圖表

### 5. 結果導出區
- Excel文件生成和下載
- 自動命名：調貨建議_YYYYMMDD.xlsx

## 📊 輸出文件結構

### 工作表1：調貨建議 (Transfer Recommendations)

| 欄位 | 說明 | 示例 |
|------|------|------|
| Article | 產品編號（12位） | 106545309001 |
| Product Desc | 產品描述 | 某某產品描述 |
| OM | 營運管理單位 | Hippo |
| Transfer Site | 轉出店鋪代碼 | HBA4 |
| Receive Site | 接收店鋪代碼 | HC42 |
| Transfer Qty | 調貨件數 | 5 |
| Notes | 調貨說明 | RF過剩轉出 -> 緊急缺貨補貨 |

### 工作表2：統計摘要 (Summary Dashboard)

#### KPI概覽
- 總調貨建議數量（條數）
- 總調貨件數（件數合計）

#### 詳細統計表
- **按產品統計**：每個Article的總調貨件數、建議數量、涉及OM數量
- **按OM統計**：每個OM的總調貨件數、建議數量、涉及Article數量
- **轉出類型分布**：ND vs RF轉出的建議數量與總件數
- **接收類型分布**：緊急缺貨 vs 潛在缺貨的建議數量與總件數

## 🛠️ 技術規格

### 系統要求
- Python 3.8+
- 主要依賴：streamlit, pandas, openpyxl, numpy

### 安裝步驟
```bash
# 安裝依賴
pip install streamlit pandas openpyxl numpy

# 運行應用
streamlit run app.py
```

### 數據要求
Excel文件必須包含以下關鍵欄位：
- Article（產品編號，12位字符串）
- RP Type（轉出類型，ND或RF）
- Site（店鋪編號）
- OM（營運管理單位）
- SaSa Net Stock（現有庫存）
- Pending Received（在途訂單）
- Safety Stock（安全庫存）
- Last Month Sold Qty（上月銷量）
- MTD Sold Qty（本月至今銷量）

## ⚡ 性能與優化

### 數據處理優化
- 智能類型轉換和異常值處理
- 缺失值自動填充
- 大數據量分組處理優化

### 算法優化
- 優先級排序算法
- 高效匹配邏輯
- 內存優化的Excel生成

### 用戶體驗優化
- 實時進度反饋
- 直觀的KPI展示
- 響應式界面設計

## 🔍 質量檢查清單

- ✅ 轉出與接收的Article和OM一致
- ✅ Transfer Qty為正整數
- ✅ Transfer Qty不超過轉出店鋪的SaSa Net Stock
- ✅ Transfer Site和Receive Site不同
- ✅ Article為12位字符串格式
- ✅ RF類型過剩轉出符合20%上限和最少2件限制
- ✅ Excel文件格式正確，可正常開啟

## 🎯 使用流程

1. **啟動系統**：運行 `streamlit run app.py`
2. **上傳數據**：手動選擇並上傳Excel文件
3. **預覽數據**：檢查數據完整性和分布情況
4. **生成建議**：點擊「開始分析」按鈕
5. **查看結果**：檢視KPI儀表板和調貨建議明細
6. **導出報告**：下載Excel格式的完整報告

## 📈 實際執行效果

基於提供的ELE_15Sep2025.XLSX文件測試結果：
- **處理記錄**：336條原始數據
- **生成建議**：37條調貨建議
- **總調貨件數**：79件
- **涉及產品**：多個Article跨不同OM
- **處理時間**：< 5秒

## 🔧 故障排除

### 常見問題

1. **文件上傳失敗**
   - 檢查文件格式（僅支持.xlsx, .xls）
   - 確認文件大小適中
   - 驗證必要欄位存在

2. **無調貨建議生成**
   - 檢查RP Type分布
   - 驗證庫存和安全庫存數據
   - 確認有效銷量數據

3. **Excel下載問題**
   - 確保瀏覽器允許下載
   - 檢查磁盤空間充足

### 聯繫支援
如遇到技術問題，請聯繫開發團隊並提供：
- 錯誤截圖
- 輸入數據樣本
- 具體錯誤信息

---
*系統由 MiniMax Agent 開發 | © 2025*
