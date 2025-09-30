"""
測試模式B同店舖同SKU轉出/接收衝突問題
"""
import pandas as pd
import sys
sys.path.append('/workspace')
from app import TransferRecommendationSystem

def test_same_store_conflict():
    """測試同店舖同SKU同時轉出和接收的衝突情況"""
    
    # 創建測試數據 - 模擬可能發生衝突的情況
    test_data = pd.DataFrame([
        {
            'Article': 'TEST001',
            'OM': 'OM1',
            'Site': 'Store A',
            'SaSa Net Stock': 15,  # 當前庫存15
            'Pending Received': 0,
            'Safety Stock': 8,     # 安全庫存8
            'RP Type': 'RF',
            'MTD Sold Qty': 5,     # 銷量5 (較低)
            'MOQ': 6
        },
        {
            'Article': 'TEST001',  # 同一SKU
            'OM': 'OM1',          # 同一OM
            'Site': 'Store A',     # 同一店舖！
            'SaSa Net Stock': 3,   # 但這個記錄顯示庫存3 (低於安全庫存)
            'Pending Received': 0,
            'Safety Stock': 8,     # 安全庫存8
            'RP Type': 'RF',
            'MTD Sold Qty': 7,     # 銷量7 (較高)
            'MOQ': 6
        },
        {
            'Article': 'TEST001',
            'OM': 'OM1',
            'Site': 'Store B',     # 其他店舖
            'SaSa Net Stock': 20,
            'Pending Received': 0,
            'Safety Stock': 10,
            'RP Type': 'RF',
            'MTD Sold Qty': 12,
            'MOQ': 6
        }
    ])
    
    # 創建系統實例
    system = TransferRecommendationSystem()
    system.df = test_data
    
    print("=== 測試數據 ===")
    print(test_data[['Article', 'OM', 'Site', 'SaSa Net Stock', 'Safety Stock', 'MTD Sold Qty']])
    
    # 測試模式B
    print("\n=== 模式B轉出候選 ===")
    transfer_candidates = system.identify_transfer_candidates("B")
    for i, candidate in enumerate(transfer_candidates):
        print(f"{i+1}. {candidate['Site']} - {candidate['Article']} - 轉出{candidate['Transfer_Qty']}件 - {candidate['Type']}")
    
    print("\n=== 接收候選 ===")
    receive_candidates = system.identify_receive_candidates()
    for i, candidate in enumerate(receive_candidates):
        print(f"{i+1}. {candidate['Site']} - {candidate['Article']} - 需要{candidate['Need_Qty']}件 - {candidate['Type']}")
    
    # 檢查是否存在同店舖同SKU衝突
    print("\n=== 衝突檢查 ===")
    conflicts = []
    for transfer in transfer_candidates:
        for receive in receive_candidates:
            if (transfer['Site'] == receive['Site'] and 
                transfer['Article'] == receive['Article'] and
                transfer['OM'] == receive['OM']):
                conflicts.append({
                    'Site': transfer['Site'],
                    'Article': transfer['Article'],
                    'OM': transfer['OM'],
                    'Transfer_Qty': transfer['Transfer_Qty'],
                    'Need_Qty': receive['Need_Qty'],
                    'Transfer_Type': transfer['Type'],
                    'Receive_Type': receive['Type']
                })
    
    if conflicts:
        print("⚠️  發現衝突：")
        for conflict in conflicts:
            print(f"   {conflict['Site']} - {conflict['Article']} 同時轉出{conflict['Transfer_Qty']}件({conflict['Transfer_Type']})和接收{conflict['Need_Qty']}件({conflict['Receive_Type']})")
    else:
        print("✅ 無衝突")
    
    # 生成建議並檢查結果
    print("\n=== 調貨建議 ===")
    suggestions = system.match_transfer_suggestions(transfer_candidates, receive_candidates)
    for i, suggestion in enumerate(suggestions):
        print(f"{i+1}. {suggestion['Transfer_Site']} -> {suggestion['Receive_Site']} - {suggestion['Article']} - {suggestion['Transfer_Qty']}件")
    
    return conflicts

if __name__ == "__main__":
    conflicts = test_same_store_conflict()
    print(f"\n總結：發現 {len(conflicts)} 個衝突")