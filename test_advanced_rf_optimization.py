"""
測試RF轉出高級優化功能
驗證：存貨優先、同店舖轉出、避免單件轉出
"""

import pandas as pd
import numpy as np
from app import TransferRecommendationSystem

def create_advanced_test_data():
    """創建高級測試資料，驗證存貨優先、同店舖轉出、避免單件"""
    
    test_data = []
    
    # ========== 產品P001 場景 ==========
    # Store A01 - 高存貨，可2件以上轉出，多品項 (應該最優先)
    test_data.extend([
        {'Article': 'P001', 'Article Description': 'Product 1', 'RP Type': 'RF', 'Site': 'A01', 'OM': 'OM1', 
         'MOQ': 10, 'SaSa Net Stock': 80, 'Pending Received': 0, 'Safety Stock': 20, 
         'Last Month Sold Qty': 5, 'MTD Sold Qty': 3},
        {'Article': 'P002', 'Article Description': 'Product 2', 'RP Type': 'RF', 'Site': 'A01', 'OM': 'OM1', 
         'MOQ': 8, 'SaSa Net Stock': 70, 'Pending Received': 0, 'Safety Stock': 15, 
         'Last Month Sold Qty': 4, 'MTD Sold Qty': 2},
        {'Article': 'P003', 'Article Description': 'Product 3', 'RP Type': 'RF', 'Site': 'A01', 'OM': 'OM1', 
         'MOQ': 12, 'SaSa Net Stock': 60, 'Pending Received': 0, 'Safety Stock': 18, 
         'Last Month Sold Qty': 3, 'MTD Sold Qty': 1},
    ])
    
    # Store B01 - 中等存貨，可2件轉出，雙品項 (第二優先)
    test_data.extend([
        {'Article': 'P001', 'Article Description': 'Product 1', 'RP Type': 'RF', 'Site': 'B01', 'OM': 'OM1', 
         'MOQ': 10, 'SaSa Net Stock': 50, 'Pending Received': 0, 'Safety Stock': 20, 
         'Last Month Sold Qty': 2, 'MTD Sold Qty': 1},
        {'Article': 'P002', 'Article Description': 'Product 2', 'RP Type': 'RF', 'Site': 'B01', 'OM': 'OM1', 
         'MOQ': 8, 'SaSa Net Stock': 45, 'Pending Received': 0, 'Safety Stock': 15, 
         'Last Month Sold Qty': 3, 'MTD Sold Qty': 2},
    ])
    
    # Store C01 - 低存貨，只能1件轉出，單品項 (最後優先，應該被避免)
    test_data.append({
        'Article': 'P001', 'Article Description': 'Product 1', 'RP Type': 'RF', 'Site': 'C01', 'OM': 'OM1', 
        'MOQ': 10, 'SaSa Net Stock': 21, 'Pending Received': 0, 'Safety Stock': 20, 
        'Last Month Sold Qty': 1, 'MTD Sold Qty': 1
    })
    
    # Store D01 - 極低存貨，只能1件轉出，但存貨比C01還少 (應該被跳過)
    test_data.append({
        'Article': 'P002', 'Article Description': 'Product 2', 'RP Type': 'RF', 'Site': 'D01', 'OM': 'OM1', 
        'MOQ': 8, 'SaSa Net Stock': 16, 'Pending Received': 0, 'Safety Stock': 15, 
        'Last Month Sold Qty': 1, 'MTD Sold Qty': 0
    })
    
    # ========== 接收店舖 ==========
    # Store E01 - 需要多個產品
    test_data.extend([
        {'Article': 'P001', 'Article Description': 'Product 1', 'RP Type': 'RF', 'Site': 'E01', 'OM': 'OM1', 
         'MOQ': 10, 'SaSa Net Stock': 0, 'Pending Received': 0, 'Safety Stock': 20, 
         'Last Month Sold Qty': 8, 'MTD Sold Qty': 5},  # 緊急缺貨
        {'Article': 'P002', 'Article Description': 'Product 2', 'RP Type': 'RF', 'Site': 'E01', 'OM': 'OM1', 
         'MOQ': 8, 'SaSa Net Stock': 0, 'Pending Received': 0, 'Safety Stock': 15, 
         'Last Month Sold Qty': 6, 'MTD Sold Qty': 4},   # 緊急缺貨
        {'Article': 'P003', 'Article Description': 'Product 3', 'RP Type': 'RF', 'Site': 'E01', 'OM': 'OM1', 
         'MOQ': 12, 'SaSa Net Stock': 0, 'Pending Received': 0, 'Safety Stock': 18, 
         'Last Month Sold Qty': 5, 'MTD Sold Qty': 3},   # 緊急缺貨
    ])
    
    # Store F01 - 需要P001和P002
    test_data.extend([
        {'Article': 'P001', 'Article Description': 'Product 1', 'RP Type': 'RF', 'Site': 'F01', 'OM': 'OM1', 
         'MOQ': 10, 'SaSa Net Stock': 0, 'Pending Received': 0, 'Safety Stock': 20, 
         'Last Month Sold Qty': 7, 'MTD Sold Qty': 4},   # 緊急缺貨
        {'Article': 'P002', 'Article Description': 'Product 2', 'RP Type': 'RF', 'Site': 'F01', 'OM': 'OM1', 
         'MOQ': 8, 'SaSa Net Stock': 0, 'Pending Received': 0, 'Safety Stock': 15, 
         'Last Month Sold Qty': 5, 'MTD Sold Qty': 3},   # 緊急缺貨
    ])
    
    return pd.DataFrame(test_data)

def analyze_optimization_results(suggestions, mode):
    """分析優化結果"""
    print(f"\n📊 {mode}模式優化結果分析:")
    print("-" * 40)
    
    if not suggestions:
        print("   ⚠️  無調貨建議")
        return
    
    df_suggestions = pd.DataFrame(suggestions)
    rf_suggestions = df_suggestions[df_suggestions['Transfer_Type'].str.contains('RF')]
    
    if rf_suggestions.empty:
        print("   ⚠️  無RF轉出建議")
        return
    
    # 1. 按轉出店舖分析
    print("🏪 轉出店舖分析:")
    store_analysis = rf_suggestions.groupby('Transfer_Site').agg({
        'Article': 'count',
        'Transfer_Qty': 'sum',
        'Original_Stock': 'first'  # 取第一個原始存貨作為參考
    }).rename(columns={'Article': 'Products', 'Transfer_Qty': 'Total_Qty', 'Original_Stock': 'Stock_Sample'})
    
    # 按產品數量和總存貨排序
    store_analysis = store_analysis.sort_values(['Products', 'Total_Qty'], ascending=False)
    print(store_analysis)
    
    # 2. 單件轉出分析
    single_transfers = rf_suggestions[rf_suggestions['Transfer_Qty'] == 1]
    multi_transfers = rf_suggestions[rf_suggestions['Transfer_Qty'] >= 2]
    
    print(f"\n📈 轉出數量分析:")
    print(f"   - 單件轉出: {len(single_transfers)} 條 ({len(single_transfers)/len(rf_suggestions)*100:.1f}%)")
    print(f"   - 多件轉出: {len(multi_transfers)} 條 ({len(multi_transfers)/len(rf_suggestions)*100:.1f}%)")
    
    if not single_transfers.empty:
        print(f"   ⚠️  單件轉出詳情:")
        for _, row in single_transfers.iterrows():
            print(f"      - {row['Transfer_Site']}: {row['Article']} (原存貨: {row['Original_Stock']})")
    
    # 3. 同店舖轉出效果
    multi_item_stores = store_analysis[store_analysis['Products'] > 1]
    if not multi_item_stores.empty:
        print(f"\n🎯 多品項同店舖轉出成功: {len(multi_item_stores)} 個店舖")
        for store in multi_item_stores.index:
            products = multi_item_stores.loc[store, 'Products']
            total_qty = multi_item_stores.loc[store, 'Total_Qty']
            print(f"   - {store}: {products} 個產品, 總計 {total_qty} 件")
    
    return {
        'total_rf_suggestions': len(rf_suggestions),
        'single_piece_count': len(single_transfers),
        'multi_piece_count': len(multi_transfers),
        'multi_item_stores': len(multi_item_stores),
        'store_analysis': store_analysis
    }

def test_advanced_rf_optimization():
    """測試RF轉出高級優化功能"""
    print("🧪 測試RF轉出高級優化功能")
    print("✅ 存貨優先 + 同店舖轉出 + 避免單件")
    print("=" * 60)
    
    # 創建測試資料
    df = create_advanced_test_data()
    print(f"📊 測試資料: {len(df)} 條記錄")
    print(f"   - 店舖數量: {df['Site'].nunique()}")
    print(f"   - 產品數量: {df['Article'].nunique()}")
    
    # 顯示店舖存貨概況
    print("\n🏪 店舖存貨分佈:")
    store_summary = df[df['RP Type'] == 'RF'].groupby(['Site']).agg({
        'Article': 'count',
        'SaSa Net Stock': ['sum', 'mean']
    }).round(2)
    store_summary.columns = ['Products', 'Total_Stock', 'Avg_Stock']
    store_summary = store_summary.sort_values(['Products', 'Total_Stock'], ascending=False)
    print(store_summary)
    
    # 理論預期：A01 > B01 > C01 > D01 (按存貨和品項數排序)
    print("\n💡 理論預期優先級:")
    print("   1. A01 (80+70+60=210總存貨, 3品項, 可多件)")
    print("   2. B01 (50+45=95總存貨, 2品項, 可多件)")  
    print("   3. C01 (21總存貨, 1品項, 僅1件)")
    print("   4. D01 (16總存貨, 1品項, 僅1件)")
    
    analyzer = TransferRecommendationSystem()
    analyzer.df = df
    
    # 測試A模式和B模式
    results = {}
    for mode in ["A", "B"]:
        success, message = analyzer.generate_recommendations(mode)
        if success:
            suggestions = analyzer.transfer_suggestions
            print(f"\n✅ {mode}模式: {message}")
            results[mode] = analyze_optimization_results(suggestions, mode)
        else:
            print(f"\n❌ {mode}模式: {message}")
            results[mode] = None
    
    # 比較兩種模式
    print("\n" + "=" * 60)
    print("📋 模式比較總結")
    print("=" * 60)
    
    for mode in ["A", "B"]:
        if results[mode]:
            r = results[mode]
            print(f"\n{mode}模式:")
            print(f"   - RF轉出總數: {r['total_rf_suggestions']} 條")
            print(f"   - 單件轉出: {r['single_piece_count']} 條")
            print(f"   - 多件轉出: {r['multi_piece_count']} 條")
            print(f"   - 多品項店舖: {r['multi_item_stores']} 個")
            
            # 檢查是否成功避免不必要的單件轉出
            if r['single_piece_count'] == 0:
                print(f"   ✅ 完全避免單件轉出")
            elif r['single_piece_count'] <= 2:
                print(f"   ✅ 基本避免單件轉出")
            else:
                print(f"   ⚠️  仍有較多單件轉出")
    
    print("\n✅ 高級優化功能測試完成")

if __name__ == "__main__":
    test_advanced_rf_optimization()
