"""
測試預計統計功能
"""

import sys
sys.path.append('/workspace')

from app import TransferRecommendationSystem
import pandas as pd

def test_preliminary_statistics():
    """測試預計統計功能"""
    
    print("=" * 50)
    print("📊 預計統計功能測試")
    print("=" * 50)
    
    # 初始化系統
    system = TransferRecommendationSystem()
    
    # 載入示例數據
    sample_file = "/workspace/user_input_files/ELE_08Sep2025 - Dummy.XLSX"
    
    try:
        with open(sample_file, 'rb') as f:
            success, message = system.load_and_preprocess_data(f)
        
        if success:
            print(f"✅ 數據載入成功: {message}")
            
            # 檢查預計統計是否生成
            if hasattr(system, 'preliminary_stats') and system.preliminary_stats:
                print("\n📈 預計統計結果:")
                
                # A模式統計
                conservative = system.preliminary_stats['conservative']
                print(f"\n🔹 A模式 (保守轉貨):")
                print(f"   預計轉出數量: {conservative['estimated_transfer']}")
                print(f"   預計接收數量: {conservative['estimated_receive']}")
                print(f"   預計需求數量: {conservative['estimated_demand']}")
                
                # B模式統計
                enhanced = system.preliminary_stats['enhanced']
                print(f"\n🔹 B模式 (加強轉貨):")
                print(f"   預計轉出數量: {enhanced['estimated_transfer']}")
                print(f"   預計接收數量: {enhanced['estimated_receive']}")
                print(f"   預計需求數量: {enhanced['estimated_demand']}")
                
                print("\n✅ 預計統計功能正常工作")
                
                # 比較兩種模式
                print(f"\n📊 模式比較:")
                print(f"   A模式轉出量: {conservative['estimated_transfer']}")
                print(f"   B模式轉出量: {enhanced['estimated_transfer']}")
                print(f"   差異: {enhanced['estimated_transfer'] - conservative['estimated_transfer']}")
                
            else:
                print("❌ 預計統計數據未生成")
                return False
                
        else:
            print(f"❌ 數據載入失敗: {message}")
            return False
            
    except Exception as e:
        print(f"❌ 測試異常: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_preliminary_statistics()
    if success:
        print("\n🎉 預計統計功能測試成功!")
    else:
        print("\n❌ 預計統計功能測試失敗!")