"""
測試 SasaNet 調撥接收優化功能
驗證 v1.71 新增的 SasaNet 自動調撥接收條件

測試條件：當 SasaNet stock + pending received < Safety stock 時，需要調撥接收
"""

import pandas as pd
import sys
import os

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import TransferRecommendationSystem

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
        'Last Month Sold Qty': [5, 8, 0, 12, 3],
        'MTD Sold Qty': [2, 3, 0, 4, 1]
    }
    
    return pd.DataFrame(test_data)

def test_sasanet_receive_conditions():
    """測試 SasaNet 調撥接收條件"""
    print("=" * 60)
    print("SasaNet 調撥接收優化測試 v1.71")
    print("=" * 60)
    
    # 創建測試系統
    system = TransferRecommendationSystem()
    
    # 創建測試數據
    test_df = create_test_data()
    system.df = test_df
    
    print("\n📊 測試數據分析:")
    print("-" * 40)
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
    receive_candidates = system.identify_receive_candidates()
    
    print("🎯 接收候選識別結果:")
    print("-" * 40)
    
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
    expected_sasanet_receives = []
    
    for _, row in test_df.iterrows():
        current_stock = row['SaSa Net Stock']
        pending = row['Pending Received']
        safety_stock = row['Safety Stock']
        
        # 檢查是否應該觸發 SasaNet 調撥接收
        if (current_stock + pending) < safety_stock and current_stock > 0:
            expected_sasanet_receives.append(row['Article'])
    
    actual_sasanet_articles = [c['Article'] for c in sasanet_receives]
    
    print(f"預期 SasaNet 調撥接收產品: {expected_sasanet_receives}")
    print(f"實際 SasaNet 調撥接收產品: {actual_sasanet_articles}")
    
    # 驗證邏輯正確性
    test_passed = True
    
    # 檢查每個測試案例
    test_cases = [
        ('A001', 'Store1', 3, 2, 10, True, 5),  # 3+2=5 < 10, 需要5件
        ('A002', 'Store2', 6, 1, 15, True, 8),  # 6+1=7 < 15, 需要8件
        ('A003', 'Store3', 0, 0, 8, False, 0),  # 0庫存，應該是緊急缺貨
        ('A004', 'Store4', 15, 5, 12, False, 0), # 15+5=20 > 12, 不需要
        ('A005', 'Store5', 2, 3, 4, False, 0),  # 2+3=5 > 4, 不需要
    ]
    
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
    return test_passed

if __name__ == "__main__":
    success = test_sasanet_receive_conditions()
    
    if success:
        print("\n🎉 SasaNet 調撥接收優化功能測試成功！")
        print("v1.71 功能正常運行，邏輯正確。")
    else:
        print("\n⚠️ 測試發現問題，請檢查邏輯實現。")
    
    print("\n" + "=" * 60)