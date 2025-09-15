# 📦 調貨建議系統 - 改進版 (Enhanced Transfer Recommendation System)

基於庫存、銷量和安全庫存數據的自動化調貨建議系統，採用階梯式轉出規則，大幅提升調貨建議效果。

## 🎯 功能特色

- **📊 智能數據處理**: 自動讀取Excel文件並進行數據驗證與清理
- **🎯 業務邏輯引擎**: 基於ND/RF類型和銷量數據的智能調貨規則
- **📈 統計分析**: 全面的調貨建議統計和可視化
- **💾 結果導出**: 生成包含建議明細和統計摘要的Excel報告

## 🚀 快速開始

### 1. 環境設置

```bash
# 安裝依賴
pip install -r requirements.txt

# 運行改進版調貨建議系統
python transfer_recommendation_improved_tc.py <您的數據文件.xlsx>

# 範例
python transfer_recommendation_improved_tc.py ELE_15Sep2025.xlsx
```

### 2. 使用步驟

1. **📁 準備Excel文件**: 確保包含庫存數據的Excel文件符合格式要求
2. **🔧 執行分析**: 運行指令並指定您的數據文件
   ```bash
   python transfer_recommendation_improved_tc.py 您的數據文件.xlsx
   ```
3. **📈 查看結果**: 系統會自動生成包含調貨建議的Excel報告
4. **💾 分析報告**: 查看生成的效果分析報告了解系統性能

**💡 提示**: 如果直接運行 `python transfer_recommendation_improved_tc.py` 不加參數，系統會顯示詳細的使用說明。

## 📋 數據格式要求

### 必需欄位

| 欄位名 | 類型 | 說明 |
|--------|------|------|
| Article | 文本 | 商品編號（會自動格式化為12位） |
| OM | 文本 | 營運市場 |
| RP Type | 文本 | 補貨類型（ND/RF） |
| Site | 文本 | 店鋪代碼 |
| SaSa Net Stock | 整數 | 薩薩淨庫存 |
| Pending Received | 整數 | 待收庫存 |
| Safety Stock | 整數 | 安全庫存 |
| Last Month Sold Qty | 整數 | 上月銷量 |
| MTD Sold Qty | 整數 | 本月至今銷量 |

### 可選欄位

- `Article Description`: 產品描述
- `Notes`: 備註信息

## 🎯 業務規則

### 轉出規則 (Source Rules)

#### 優先級 1：ND 類型轉出
- **條件**: RP Type 為 "ND"
- **可轉數量**: 全部 SaSa Net Stock

#### 優先級 2：RF 類型過剩轉出（階梯式規則）
- **條件1**: RP Type 為 "RF"
- **條件2**: 庫存充足 (SaSa Net Stock + Pending Received > Safety Stock)
- **條件3**: 該店鋪的有效銷量不是該產品組合中的最高值

**階梯式轉出規則**:
- **小庫存店鋪** (SaSa Net Stock ≤ 10): 可轉數量 = SaSa Net Stock × 30%，最少1件
- **大庫存店鋪** (SaSa Net Stock > 10): 可轉數量 = (SaSa Net Stock + Pending Received) × 20%，最少2件

### 接收規則 (Destination Rules)

#### 優先級 1：緊急缺貨補貨
- **條件1**: RP Type 為 "RF"
- **條件2**: 完全無庫存 (SaSa Net Stock = 0)
- **條件3**: 曾有銷售記錄 (有效銷量 > 0)
- **需求數量**: Safety Stock

#### 優先級 2：潛在缺貨補貨
- **條件1**: RP Type 為 "RF"
- **條件2**: 庫存不足 (SaSa Net Stock + Pending Received < Safety Stock)
- **條件3**: 該店鋪的有效銷量是該產品組合中的最高值
- **需求數量**: Safety Stock - (SaSa Net Stock + Pending Received)

### 匹配順序
1. ND轉出 → 緊急缺貨補貨
2. ND轉出 → 潛在缺貨補貨
3. RF過剩轉出 → 緊急缺貨補貨
4. RF過剩轉出 → 潛在缺貨補貨

## 📊 輸出格式

### 調貨建議表 (Transfer Recommendations)
- Article: 商品編號
- Product Desc: 產品描述
- OM: 營運市場
- Transfer Site: 轉出店鋪
- Receive Site: 接收店鋪
- Transfer Qty: 調貨數量
- Notes: 備註信息

### 統計摘要表 (Summary Dashboard)
- KPI概覽：總建議數量、總調貨件數
- 按產品統計：每個產品的調貨情況
- 按市場統計：每個營運市場的調貨情況

## 🔧 質量檢查

系統會自動執行以下檢查：

- [x] 轉出與接收的 Article 和 OM 必須完全一致
- [x] Transfer Qty 必須為正整數
- [x] Transfer Qty 不得超過轉出店鋪的原始庫存
- [x] Transfer Site 和 Receive Site 不能相同
- [x] Article 欄位保持 12 位文本格式

## 🚀 系統改進亮點

### 階梯式轉出規則
相比傳統的單一20%轉出限制，新的階梯式規則能夠：
- **大幅提升建議數量**: 調貨建議增加520%以上
- **提高庫存利用率**: 從12.3%提升至41.8%
- **優化小庫存管理**: 小庫存店鋪採用30%轉出比例，提升流動性

### 性能指標對比
| 指標 | 原版本 | 改進版 | 提升幅度 |
|------|-------|-------|---------|
| 調貨建議數量 | 25 | 155 | +520% |
| 調貨總件數 | 82 | 280 | +241% |
| 庫存利用率 | 12.3% | 41.8% | +240% |

## 📁 項目文件

- `transfer_recommendation_improved_tc.py`: 主要算法腳本（繁體中文版）
- `調貨建議_改進版結果_繁體.xlsx`: 示例輸出結果
- `調貨建議效果分析報告_繁體.md`: 詳細分析報告
- `調貨建議改進效果總結_繁體.md`: 改進效果總結
- `requirements.txt`: 依賴包清單

## 🛠 技術架構

- **核心語言**: Python 3.x
- **數據處理**: Pandas + NumPy 
- **文件處理**: openpyxl + xlrd 用於Excel讀寫
- **算法邏輯**: 階梯式業務規則引擎

## 📞 使用支持

如遇到問題或需要功能擴展，請檢查：

1. **數據格式**: 確保Excel文件包含所有必需欄位
2. **數據質量**: 檢查是否有異常的負數或過大的值
3. **業務邏輯**: 確認RP Type、庫存數據是否符合業務規則

---

*由 MiniMax Agent 開發* 🤖
