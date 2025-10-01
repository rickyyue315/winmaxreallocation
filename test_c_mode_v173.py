"""
測試 v1.73 C模式（重點補0）功能
條件：(SaSa Net Stock + Pending Received) ≤ 1
補充至：min(Safety Stock, MOQ + 1)
"""
import pandas as pd

class SimpleTransferSystemV173:
    """v1.73 系統 - 包含C模式功能"""
    
    def __init__(self):
        self.df = None
    
    def calculate_effective_sales(self, row):
        return row['MTD Sold Qty']
    
    def identify_receive_candidates_mode_c(self):
        """C模式：重點補0"""
        candidates = []
        
        for _, row in self.df.iterrows():
            article = row['Article']
            current_stock = row['SaSa Net Stock']
            pending = row['Pending Received']
            safety_stock = row['Safety Stock']
            rp_type = row['RP Type']
            effective_sales = self.calculate_effective_sales(row)
            site = row['Site']
            moq = row['MOQ']
            
            if rp_type == 'RF':
                total_available = current_stock + pending
                
                # C模式條件：總可用量 ≤ 1
                if total_available <= 1:
                    # 補充目標：取Safety Stock和MOQ+1的較小值
                    target_stock = min(safety_stock, moq + 1)
                    need_qty = target_stock - total_available
                    
                    if need_qty > 0:
                        candidates.append({
                            'Article': article,
                            'Site': site,
                            'OM': row['OM'],
                            'Need_Qty': need_qty,
                            'Type': '重點補0',
                            'Priority': 1,
                            'Current_Stock': current_stock,
                            'Safety_Stock': safety_stock,
                            'Effective_Sales': effective_sales,
                            'Pending_Received': pending,
                            'Total_Available': total_available,
                            'MOQ': moq,
                            'Target_Stock': target_stock
                        })
        
        # 按銷量排序（高銷量優先）
        candidates.sort(key=lambda x: -x['Effective_Sales'])
        return candidates

def test_c_mode():
    """測試C模式功能"""
    
    # 創建包含各種情況的測試數據
    test_data = pd.DataFrame([
        # 案例1：極低庫存，需要補0
        {
            'Article': 'A001',
            'OM': 'OM1',
            'Site': 'Store1',
            'SaSa Net Stock': 0,      # 庫存0
            'Pending Received': 1,    # 待收1
            'Safety Stock': 10,       # 安全庫存10
            'RP Type': 'RF',
            'MTD Sold Qty': 15,       # 高銷量
            'MOQ': 12                 # MOQ 12
        },
        # 案例2：極低庫存，MOQ較小
        {
            'Article': 'A002',
            'OM': 'OM1',
            'Site': 'Store2',
            'SaSa Net Stock': 1,      # 庫存1
            'Pending Received': 0,    # 待收0
            'Safety Stock': 15,       # 安全庫存15
            'RP Type': 'RF',
            'MTD Sold Qty': 8,
            'MOQ': 5                  # MOQ 5，較小
        },
        # 案例3：完全沒庫存
        {
            'Article': 'A003',
            'OM': 'OM1',
            'Site': 'Store3',
            'SaSa Net Stock': 0,      # 庫存0
            'Pending Received': 0,    # 待收0
            'Safety Stock': 8,
            'RP Type': 'RF',
            'MTD Sold Qty': 12,
            'MOQ': 6
        },
        # 案例4：庫存超過1，不符合C模式條件
        {
            'Article': 'A004',
            'OM': 'OM1',
            'Site': 'Store4',
            'SaSa Net Stock': 2,      # 庫存2
            'Pending Received': 0,    # 待收0
            'Safety Stock': 10,
            'RP Type': 'RF',
            'MTD Sold Qty': 5,
            'MOQ': 8
        },
        # 案例5：ND類型，不處理
        {
            'Article': 'A005',
            'OM': 'OM1',
            'Site': 'Store5',
            'SaSa Net Stock': 0,
            'Pending Received': 1,
            'Safety Stock': 10,
            'RP Type': 'ND',          # ND類型
            'MTD Sold Qty': 3,
            'MOQ': 8
        }
    ])
    
    system = SimpleTransferSystemV173()
    system.df = test_data
    
    print("=== v1.73 C模式（重點補0）測試 ===")
    print("\n=== 測試數據 ===")
    print("條件：(SaSa Net Stock + Pending Received) ≤ 1")
    print("補充至：min(Safety Stock, MOQ + 1)")
    print()
    print(test_data[['Article', 'Site', 'SaSa Net Stock', 'Pending Received', 'Safety Stock', 'MOQ', 'RP Type', 'MTD Sold Qty']])
    
    # 測試C模式接收候選識別
    print("\n=== C模式接收候選識別 ===")
    c_candidates = system.identify_receive_candidates_mode_c()
    
    if c_candidates:
        print(f"發現 {len(c_candidates)} 個重點補0候選：")
        for i, candidate in enumerate(c_candidates):
            print(f"  {i+1}. {candidate['Site']} - {candidate['Article']}:")
            print(f"     - 當前庫存: {candidate['Current_Stock']}")
            print(f"     - 待收貨: {candidate['Pending_Received']}")
            print(f"     - 總可用: {candidate['Total_Available']}")
            print(f"     - 安全庫存: {candidate['Safety_Stock']}")
            print(f"     - MOQ: {candidate['MOQ']}")
            print(f"     - 補充目標: {candidate['Target_Stock']} = min({candidate['Safety_Stock']}, {candidate['MOQ']}+1)")
            print(f"     - 需要補充: {candidate['Need_Qty']}件")
            print(f"     - 銷量: {candidate['Effective_Sales']}")
            print()
    else:
        print("無重點補0候選")
    
    # 驗證邏輯正確性
    print("=== 邏輯驗證 ===")
    
    # 驗證每個測試案例
    expected_results = {
        'A001': {'should_qualify': True, 'expected_need': min(10, 12+1) - (0+1), 'target': min(10, 13)},  # min(10,13)-1 = 9
        'A002': {'should_qualify': True, 'expected_need': min(15, 5+1) - (1+0), 'target': min(15, 6)},   # min(15,6)-1 = 5
        'A003': {'should_qualify': True, 'expected_need': min(8, 6+1) - (0+0), 'target': min(8, 7)},     # min(8,7)-0 = 7
        'A004': {'should_qualify': False, 'reason': '總可用量2>1'},
        'A005': {'should_qualify': False, 'reason': 'ND類型不處理'}
    }
    
    qualified_articles = [c['Article'] for c in c_candidates]
    
    for article, expected in expected_results.items():
        if expected['should_qualify']:
            if article in qualified_articles:
                candidate = next(c for c in c_candidates if c['Article'] == article)
                actual_need = candidate['Need_Qty']
                expected_need = expected['expected_need']
                if actual_need == expected_need:
                    print(f"✅ {article}: 正確識別，需要補充{actual_need}件")
                else:
                    print(f"❌ {article}: 需求計算錯誤，預期{expected_need}件，實際{actual_need}件")
            else:
                print(f"❌ {article}: 應該被識別但未被識別")
        else:
            if article not in qualified_articles:
                print(f"✅ {article}: 正確排除 - {expected['reason']}")
            else:
                print(f"❌ {article}: 不應被識別但被識別了")
    
    return len(c_candidates) > 0

if __name__ == "__main__":
    success = test_c_mode()
    print(f"\n🎯 C模式測試結果: {'成功' if success else '失敗'}")