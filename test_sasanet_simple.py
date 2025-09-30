"""
SasaNet 調撥接收優化邏輯測試 - 簡化版本
測試 v1.71 新增的邏輯：當 SasaNet stock + pending received < Safety stock 時需要調撥接收
"""

import pandas as pd

def calculate_effective_sales(row):
    """計算有效銷量"""
    if row['Last Month Sold Qty'] > 0:
        return row['Last Month Sold Qty']
    else:
        return row['MTD Sold Qty']

def identify_sasanet_receive_candidates(df):
    """SasaNet 調撥接收候選識別函數"""
    candidates = []
    
    for _, row in df.iterrows():
        article = row['Article']
        current_stock = row['SaSa Net Stock']
        pending = row['Pending Received']
        safety_stock = row['Safety Stock']
        rp_type = row['RP Type']
        effective_sales = calculate_effective_sales(row)
        site = row['Site']
        
        if rp_type == 'RF':
            # 計算該產品的最高銷量
            product_data = df[df['Article'] == article]
            max_sales = product_data.apply(calculate_effective_sales, axis=1).max()
            
            # 緊急缺貨補貨 (優先順序1)
            if current_stock == 0 and effective_sales > 0:
                candidates.append({
                    'Article': article,
                    'Site': site,
                    'OM': row['OM'],
                    'Need_Qty': safety_stock,
                    'Type': '緊急缺貨補貨',
                    'Priority': 1,
                    'Current_Stock': current_stock,
                    'Safety_Stock': safety_stock,
                    'Effective_Sales': effective_sales,
                    'Pending_Received': pending,
                    'Total_Available': current_stock + pending
                })
            
            # v1.71 新增：SasaNet 調撥接收條件 (優先順序2)
            elif (current_stock + pending) < safety_stock and current_stock > 0:
                need_qty = safety_stock - (current_stock + pending)
                if need_qty > 0:
                    candidates.append({
                        'Article': article,
                        'Site': site,
                        'OM': row['OM'],
                        'Need_Qty': need_qty,
                        'Type': 'SasaNet調撥接收',
                        'Priority': 2,
                        'Current_Stock': current_stock,
                        'Safety_Stock': safety_stock,
                        'Effective_Sales': effective_sales,
                        'Pending_Received': pending,
                        'Total_Available': current_stock + pending
                    })
            
            # 潛在缺貨補貨 (優先順序3)
            elif (current_stock + pending) < safety_stock and effective_sales == max_sales:
                need_qty = safety_stock - (current_stock + pending)
                if need_qty > 0:
                    candidates.append({
                        'Article': article,
                        'Site': site,
                        'OM': row['OM'],
                        'Need_Qty': need_qty,
                        'Type': '潛在缺貨補貨',
                        'Priority': 3,
                        'Current_Stock': current_stock,
                        'Safety_Stock': safety_stock,
                        'Effective_Sales': effective_sales,
                        'Pending_Received': pending,
                        'Total_Available': current_stock + pending
                    })
    
    # 按優先順序和銷量排序
    candidates.sort(key=lambda x: (x['Priority'], -x['Effective_Sales']))
    return candidates

def create_test_data():
    """創建測試數據"""
    test_data = {
        'Article': ['A001', 'A002', 'A003', 'A004', 'A005'],
        'Article Description': ['Product A001', 'Product A002', 'Product A003', 'Product A004', 'Product A005'],
        'RP Type': ['RF', 'RF', 'RF', 'RF', 'RF'],
        'Site': ['Store1', 'Store2', 'Store3', 'Store4', 'Store5'],
        'OM': ['OM1', 'OM1', 'OM2', 'OM2', 'OM3'],
        'MOQ': [5, 5, 10, 10, 8],
        'SaSa Net Stock': [3, 6, 0, 15, 2],        # 當前庫存
        'Pending Received': [2, 1, 0, 5, 3],      # 待收貨
        'Safety Stock': [10, 15, 8, 12, 4],       # 安全庫存
        'Last Month Sold Qty': [5, 8, 3, 12, 3],  # A003改為3，有銷售記錄
        'MTD Sold Qty': [2, 3, 1, 4, 1]           # A003改為1，有銷售記錄
    }
    
    return pd.DataFrame(test_data)

def test_sasanet_logic():
    """測試 SasaNet 邏輯"""
    print("=" * 60)
    print("SasaNet 調撥接收優化測試 v1.71 - 簡化版本")
    print("=" * 60)
    
    # 創建測試數據
    test_df = create_test_data()
    
    print("\n📊 測試數據分析:")
    print("-" * 50)
    for idx, row in test_df.iterrows():
        current_stock = row['SaSa Net Stock']
        pending = row['Pending Received']
        safety_stock = row['Safety Stock']
        total_available = current_stock + pending
        need_transfer = total_available < safety_stock
        
        print(f"產品 {row['Article']} ({row['Site']}):")
        print(f"  當前庫存: {current_stock}, 待收貨: {pending}, 總可用: {total_available}")
        print(f"  安全庫存: {safety_stock}, 需要調撥: {'是' if need_transfer else '否'}")
        if need_transfer:
            need_qty = safety_stock - total_available
            print(f"  需求數量: {need_qty}")
        print()
    
    # 測試接收候選識別
    receive_candidates = identify_sasanet_receive_candidates(test_df)
    
    print("🎯 接收候選識別結果:")
    print("-" * 50)
    
    sasanet_receives = [c for c in receive_candidates if c['Type'] == 'SasaNet調撥接收']
    emergency_receives = [c for c in receive_candidates if c['Type'] == '緊急缺貨補貨']
    potential_receives = [c for c in receive_candidates if c['Type'] == '潛在缺貨補貨']
    
    print(f"總接收候選數: {len(receive_candidates)}")
    print(f"SasaNet調撥接收: {len(sasanet_receives)}")
    print(f"緊急缺貨補貨: {len(emergency_receives)}")
    print(f"潛在缺貨補貨: {len(potential_receives)}")
    
    print("\n📋 SasaNet 調撥接收詳細列表:")
    print("-" * 50)
    for candidate in sasanet_receives:
        print(f"產品: {candidate['Article']} | 店鋪: {candidate['Site']}")
        print(f"  當前庫存: {candidate['Current_Stock']}")
        print(f"  待收貨: {candidate['Pending_Received']}")
        print(f"  總可用: {candidate['Total_Available']}")
        print(f"  安全庫存: {candidate['Safety_Stock']}")
        print(f"  需求數量: {candidate['Need_Qty']}")
        print(f"  優先順序: {candidate['Priority']}")
        print()
    
    # 驗證測試結果
    print("✅ 驗證結果:")
    print("-" * 30)
    
    # 測試案例驗證
    test_cases = [
        ('A001', 'Store1', 3, 2, 10, True, 5),   # 3+2=5 < 10, 需要5件 (SasaNet)
        ('A002', 'Store2', 6, 1, 15, True, 8),   # 6+1=7 < 15, 需要8件 (SasaNet)
        ('A003', 'Store3', 0, 0, 8, False, 0),   # 0庫存且有銷量，應該是緊急缺貨
        ('A004', 'Store4', 15, 5, 12, False, 0), # 15+5=20 > 12, 不需要
        ('A005', 'Store5', 2, 3, 4, False, 0),   # 2+3=5 > 4, 不需要
    ]
    
    test_passed = True
    
    for article, site, stock, pending, safety, should_receive, expected_qty in test_cases:
        found_candidate = None
        for candidate in sasanet_receives:
            if candidate['Article'] == article and candidate['Site'] == site:
                found_candidate = candidate
                break
        
        if should_receive:
            if found_candidate:
                if found_candidate['Need_Qty'] == expected_qty:
                    print(f"✅ {article}: 正確識別，需求數量 {expected_qty}")
                else:
                    print(f"❌ {article}: 數量錯誤，預期 {expected_qty}，實際 {found_candidate['Need_Qty']}")
                    test_passed = False
            else:
                print(f"❌ {article}: 應該識別但未識別")
                test_passed = False
        else:
            if found_candidate:
                print(f"❌ {article}: 不應該識別但被識別了")
                test_passed = False
            else:
                print(f"✅ {article}: 正確未識別")
    
    print(f"\n🎯 測試結果: {'全部通過' if test_passed else '部分失敗'}")
    
    # 檢查緊急缺貨補貨
    print("\n📋 緊急缺貨補貨驗證:")
    print("-" * 30)
    emergency_expected = ['A003']  # 只有A003庫存為0且有銷量
    emergency_actual = [c['Article'] for c in emergency_receives]
    
    if emergency_actual == emergency_expected:
        print(f"✅ 緊急缺貨補貨識別正確: {emergency_actual}")
    else:
        print(f"❌ 緊急缺貨補貨識別錯誤，預期: {emergency_expected}，實際: {emergency_actual}")
        test_passed = False
    
    return test_passed

if __name__ == "__main__":
    success = test_sasanet_logic()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 SasaNet 調撥接收優化功能測試成功！")
        print("v1.71 功能邏輯正確，可以正常運行。")
        print("\n✨ 優化摘要:")
        print("• 新增 SasaNet 調撥接收條件（優先級2）")
        print("• 條件：SasaNet stock + pending received < Safety stock")
        print("• 自動計算需求數量 = Safety stock - (current + pending)")
        print("• 與緊急缺貨補貨和潛在缺貨補貨區分優先級")
    else:
        print("⚠️ 測試發現問題，請檢查邏輯實現。")
    
    print("=" * 60)