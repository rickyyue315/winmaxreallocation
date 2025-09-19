"""
測試同店舖RF轉出優化功能
驗證算法是否能有效將多品項集中在同一店舖轉出
"""

import pandas as pd
import numpy as np
from app import TransferRecommendationSystem

def create_test_data_for_same_store():
    """創建測試資料，模擬同店舖多品項轉出場景"""
    
    # 創建測試資料
    test_data = []
    
    # OM1 - 模擬多品項同店舖轉出場景
    # Store A01 - 有多個RF產品可轉出 (應該被優先安排)
    test_data.extend([
        {'Article': 'P001', 'Article Description': 'Product 1', 'RP Type': 'RF', 'Site': 'A01', 'OM': 'OM1', 
         'MOQ': 10, 'SaSa Net Stock': 50, 'Pending Received': 0, 'Safety Stock': 20, 
         'Last Month Sold Qty': 5, 'MTD Sold Qty': 3},
        {'Article': 'P002', 'Article Description': 'Product 2', 'RP Type': 'RF', 'Site': 'A01', 'OM': 'OM1', 
         'MOQ': 8, 'SaSa Net Stock': 40, 'Pending Received': 0, 'Safety Stock': 15, 
         'Last Month Sold Qty': 4, 'MTD Sold Qty': 2},
        {'Article': 'P003', 'Article Description': 'Product 3', 'RP Type': 'RF', 'Site': 'A01', 'OM': 'OM1', 
         'MOQ': 12, 'SaSa Net Stock': 35, 'Pending Received': 0, 'Safety Stock': 18, 
         'Last Month Sold Qty': 3, 'MTD Sold Qty': 1},
    ])
    
    # Store B01 - 只有1個RF產品可轉出 (應該被後安排)
    test_data.append({
        'Article': 'P001', 'Article Description': 'Product 1', 'RP Type': 'RF', 'Site': 'B01', 'OM': 'OM1', 
        'MOQ': 10, 'SaSa Net Stock': 30, 'Pending Received': 0, 'Safety Stock': 20, 
        'Last Month Sold Qty': 2, 'MTD Sold Qty': 1
    })
    
    # Store C01 - 需要接收的店舖
    test_data.extend([
        {'Article': 'P001', 'Article Description': 'Product 1', 'RP Type': 'RF', 'Site': 'C01', 'OM': 'OM1', 
         'MOQ': 10, 'SaSa Net Stock': 0, 'Pending Received': 0, 'Safety Stock': 20, 
         'Last Month Sold Qty': 8, 'MTD Sold Qty': 5},  # 緊急缺貨
        {'Article': 'P002', 'Article Description': 'Product 2', 'RP Type': 'RF', 'Site': 'C01', 'OM': 'OM1', 
         'MOQ': 8, 'SaSa Net Stock': 0, 'Pending Received': 0, 'Safety Stock': 15, 
         'Last Month Sold Qty': 6, 'MTD Sold Qty': 4},   # 緊急缺貨
        {'Article': 'P003', 'Article Description': 'Product 3', 'RP Type': 'RF', 'Site': 'C01', 'OM': 'OM1', 
         'MOQ': 12, 'SaSa Net Stock': 0, 'Pending Received': 0, 'Safety Stock': 18, 
         'Last Month Sold Qty': 5, 'MTD Sold Qty': 3},   # 緊急缺貨
    ])
    
    # 添加一些ND產品用於對比
    test_data.extend([
        {'Article': 'P004', 'Article Description': 'Product 4', 'RP Type': 'ND', 'Site': 'A01', 'OM': 'OM1', 
         'MOQ': 5, 'SaSa Net Stock': 10, 'Pending Received': 0, 'Safety Stock': 0, 
         'Last Month Sold Qty': 0, 'MTD Sold Qty': 0},
        {'Article': 'P004', 'Article Description': 'Product 4', 'RP Type': 'ND', 'Site': 'D01', 'OM': 'OM1', 
         'MOQ': 5, 'SaSa Net Stock': 0, 'Pending Received': 0, 'Safety Stock': 0, 
         'Last Month Sold Qty': 0, 'MTD Sold Qty': 0}
    ])
    
    return pd.DataFrame(test_data)

def test_same_store_optimization():
    """測試同店舖優化功能"""
    print("🧪 測試同店舖RF轉出優化功能")
    print("=" * 50)
    
    # 創建測試資料
    df = create_test_data_for_same_store()
    print(f"📊 測試資料: {len(df)} 條記錄")
    print(f"   - 店舖數量: {df['Site'].nunique()}")
    print(f"   - 產品數量: {df['Article'].nunique()}")
    print()
    
    # 顯示測試資料概況
    print("🏪 店舖庫存概況:")
    store_summary = df.groupby(['Site', 'RP Type']).agg({
        'Article': 'count',
        'SaSa Net Stock': 'sum'
    }).round(2)
    print(store_summary)
    print()
    
    # 測試A模式（保守轉貨）
    print("🔍 測試A模式（保守轉貨）:")
    analyzer = TransferRecommendationSystem()
    
    # 直接設置df屬性來模擬數據載入
    analyzer.df = df
    
    success, message = analyzer.generate_recommendations("A")
    if success:
        suggestions = analyzer.transfer_suggestions
        print(f"   ✅ {message}")
        
        # 分析同店舖轉出效果
        df_suggestions = pd.DataFrame(suggestions)
        if not df_suggestions.empty:
            rf_suggestions = df_suggestions[df_suggestions['Transfer_Type'].str.contains('RF')]
            
            if not rf_suggestions.empty:
                print("   📈 RF轉出分析:")
                rf_by_store = rf_suggestions.groupby('Transfer_Site').agg({
                    'Article': 'count',
                    'Transfer_Qty': 'sum'
                }).rename(columns={'Article': 'Products_Count', 'Transfer_Qty': 'Total_Qty'})
                print(rf_by_store)
                
                # 檢查是否有多品項同店舖轉出
                multi_item_stores = rf_by_store[rf_by_store['Products_Count'] > 1]
                if not multi_item_stores.empty:
                    print(f"   🎯 成功實現多品項同店舖轉出: {len(multi_item_stores)} 個店舖")
                    for store in multi_item_stores.index:
                        count = multi_item_stores.loc[store, 'Products_Count']
                        qty = multi_item_stores.loc[store, 'Total_Qty']
                        print(f"      - {store}: {count} 個產品, 總計 {qty} 件")
                else:
                    print("   ⚠️  未發現多品項同店舖轉出")
            else:
                print("   ⚠️  無RF轉出建議")
        else:
            print("   ⚠️  無調貨建議")
    else:
        print(f"   ❌ {message}")
    
    print()
    
    # 測試B模式（加強轉貨）
    print("🔍 測試B模式（加強轉貨）:")
    success, message = analyzer.generate_recommendations("B")
    if success:
        suggestions = analyzer.transfer_suggestions
        print(f"   ✅ {message}")
        
        # 分析同店舖轉出效果
        df_suggestions = pd.DataFrame(suggestions)
        if not df_suggestions.empty:
            rf_suggestions = df_suggestions[df_suggestions['Transfer_Type'].str.contains('RF')]
            
            if not rf_suggestions.empty:
                print("   📈 RF轉出分析:")
                rf_by_store = rf_suggestions.groupby('Transfer_Site').agg({
                    'Article': 'count',
                    'Transfer_Qty': 'sum'
                }).rename(columns={'Article': 'Products_Count', 'Transfer_Qty': 'Total_Qty'})
                print(rf_by_store)
                
                # 檢查是否有多品項同店舖轉出
                multi_item_stores = rf_by_store[rf_by_store['Products_Count'] > 1]
                if not multi_item_stores.empty:
                    print(f"   🎯 成功實現多品項同店舖轉出: {len(multi_item_stores)} 個店舖")
                    for store in multi_item_stores.index:
                        count = multi_item_stores.loc[store, 'Products_Count']
                        qty = multi_item_stores.loc[store, 'Total_Qty']
                        print(f"      - {store}: {count} 個產品, 總計 {qty} 件")
                else:
                    print("   ⚠️  未發現多品項同店舖轉出")
            else:
                print("   ⚠️  無RF轉出建議")
        else:
            print("   ⚠️  無調貨建議")
    else:
        print(f"   ❌ {message}")
    
    print("\n" + "=" * 50)
    print("✅ 同店舖優化功能測試完成")

if __name__ == "__main__":
    test_same_store_optimization()
