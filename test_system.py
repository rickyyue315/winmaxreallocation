"""
調貨建議系統功能測試腳本
測試基本功能是否正常運行
"""

import pandas as pd
import numpy as np
from app import TransferRecommendationSystem
import os

def test_system_functionality():
    """測試系統核心功能"""
    
    print("=" * 50)
    print("📦 調貨建議系統功能測試")
    print("=" * 50)
    
    # 初始化系統
    system = TransferRecommendationSystem()
    
    # 測試數據載入
    print("\n1. 測試數據載入...")
    
    # 檢查示例文件是否存在
    sample_file = "/workspace/user_input_files/ELE_08Sep2025 - Dummy.XLSX"
    if not os.path.exists(sample_file):
        print("❌ 示例文件不存在")
        return False
    
    # 載入數據
    try:
        with open(sample_file, 'rb') as f:
            success, message = system.load_and_preprocess_data(f)
        
        if success:
            print(f"✅ 數據載入成功: {message}")
            print(f"   - 總記錄數: {len(system.df)}")
            print(f"   - 產品數量: {system.df['Article'].nunique()}")
            print(f"   - 店鋪數量: {system.df['Site'].nunique()}")
            print(f"   - OM數量: {system.df['OM'].nunique()}")
        else:
            print(f"❌ 數據載入失敗: {message}")
            return False
            
    except Exception as e:
        print(f"❌ 數據載入異常: {e}")
        return False
    
    # 測試A模式調貨建議生成
    print("\n2. 測試A模式調貨建議生成...")
    try:
        success, message = system.generate_recommendations("A")
        if success:
            print(f"✅ A模式建議生成成功: {message}")
            print(f"   - 建議數量: {len(system.transfer_suggestions)}")
            print(f"   - 總調貨件數: {system.statistics['total_qty']}")
        else:
            print(f"❌ A模式建議生成失敗: {message}")
            return False
    except Exception as e:
        print(f"❌ A模式建議生成異常: {e}")
        return False
    
    # 測試B模式調貨建議生成
    print("\n3. 測試B模式調貨建議生成...")
    try:
        success, message = system.generate_recommendations("B")
        if success:
            print(f"✅ B模式建議生成成功: {message}")
            print(f"   - 建議數量: {len(system.transfer_suggestions)}")
            print(f"   - 總調貨件數: {system.statistics['total_qty']}")
        else:
            print(f"❌ B模式建議生成失敗: {message}")
            return False
    except Exception as e:
        print(f"❌ B模式建議生成異常: {e}")
        return False
    
    # 測試統計分析
    print("\n4. 測試統計分析...")
    try:
        if system.statistics:
            print("✅ 統計分析正常")
            print(f"   - 按產品統計: {len(system.statistics['article_stats'])} 個產品")
            print(f"   - 按OM統計: {len(system.statistics['om_stats'])} 個OM")
            print(f"   - 轉出類型: {len(system.statistics['transfer_type_stats'])} 種類型")
            print(f"   - 接收類型: {len(system.statistics['receive_type_stats'])} 種類型")
        else:
            print("❌ 統計分析數據為空")
            return False
    except Exception as e:
        print(f"❌ 統計分析異常: {e}")
        return False
    
    # 測試圖表生成
    print("\n5. 測試圖表生成...")
    try:
        fig = system.create_visualization()
        if fig:
            print("✅ 圖表生成成功")
        else:
            print("⚠️ 圖表為空（可能無數據）")
    except Exception as e:
        print(f"❌ 圖表生成異常: {e}")
        return False
    
    # 測試Excel匯出
    print("\n6. 測試Excel匯出...")
    try:
        excel_data, filename = system.export_to_excel()
        if excel_data:
            print(f"✅ Excel匯出成功: {filename}")
            print(f"   - 文件大小: {len(excel_data)} bytes")
        else:
            print("❌ Excel匯出失敗")
            return False
    except Exception as e:
        print(f"❌ Excel匯出異常: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 所有測試通過！系統運行正常")
    print("=" * 50)
    
    return True

def create_test_data():
    """創建測試數據"""
    print("\n📋 創建額外測試數據...")
    
    # 創建包含ND類型的測試數據
    test_data = {
        'Article': ['TEST001', 'TEST002', 'TEST003', 'TEST004', 'TEST005'],
        'Article Description': ['測試產品1', '測試產品2', '測試產品3', '測試產品4', '測試產品5'],
        'RP Type': ['ND', 'RF', 'RF', 'ND', 'RF'],
        'Site': ['S001', 'S002', 'S003', 'S004', 'S005'],
        'OM': ['OM1', 'OM1', 'OM2', 'OM2', 'OM1'],
        'MOQ': [10, 5, 8, 12, 6],
        'SaSa Net Stock': [20, 15, 3, 25, 0],
        'Pending Received': [0, 5, 2, 0, 8],
        'Safety Stock': [5, 8, 10, 6, 12],
        'Last Month Sold Qty': [0, 12, 8, 0, 15],
        'MTD Sold Qty': [2, 3, 5, 1, 8]
    }
    
    df_test = pd.DataFrame(test_data)
    
    # 保存測試數據
    test_file = "/workspace/test_data.xlsx"
    df_test.to_excel(test_file, index=False)
    
    print(f"✅ 測試數據已創建: {test_file}")
    return test_file

def test_with_custom_data():
    """使用自定義測試數據測試"""
    
    print("\n" + "=" * 50)
    print("🧪 自定義數據測試")
    print("=" * 50)
    
    # 創建測試數據
    test_file = create_test_data()
    
    # 初始化系統
    system = TransferRecommendationSystem()
    
    # 載入測試數據
    try:
        with open(test_file, 'rb') as f:
            success, message = system.load_and_preprocess_data(f)
        
        if success:
            print(f"✅ 測試數據載入成功: {message}")
        else:
            print(f"❌ 測試數據載入失敗: {message}")
            return False
    except Exception as e:
        print(f"❌ 測試數據載入異常: {e}")
        return False
    
    # 測試A模式
    success, message = system.generate_recommendations("A")
    if success:
        print(f"✅ A模式測試成功: {message}")
        if system.transfer_suggestions:
            print("   調貨建議詳情:")
            for suggestion in system.transfer_suggestions:
                print(f"     {suggestion['Article']}: {suggestion['Transfer_Site']} -> {suggestion['Receive_Site']}, 數量: {suggestion['Transfer_Qty']}")
    
    # 測試B模式
    success, message = system.generate_recommendations("B")
    if success:
        print(f"✅ B模式測試成功: {message}")
        if system.transfer_suggestions:
            print("   調貨建議詳情:")
            for suggestion in system.transfer_suggestions:
                print(f"     {suggestion['Article']}: {suggestion['Transfer_Site']} -> {suggestion['Receive_Site']}, 數量: {suggestion['Transfer_Qty']}")
    
    return True

if __name__ == "__main__":
    # 運行基本功能測試
    basic_test_passed = test_system_functionality()
    
    # 運行自定義數據測試
    if basic_test_passed:
        test_with_custom_data()
    
    print("\n🏁 測試完成")
