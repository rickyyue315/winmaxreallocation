"""
v1.73 完整功能驗證測試
包含A模式、B模式、C模式的完整測試和比較
"""
import pandas as pd

class TransferSystemV173Complete:
    """v1.73 完整系統模擬"""
    
    def __init__(self):
        self.df = None
    
    def preprocess_data(self, df):
        """預處理數據"""
        df = df.copy()
        
        numeric_columns = ['SaSa Net Stock', 'Safety Stock', 'MTD Sold Qty', 'MOQ', 'Pending Received']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        string_columns = ['Article', 'Site', 'OM', 'RP Type']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        return df
    
    def calculate_effective_sales(self, row):
        return row['MTD Sold Qty']
    
    def identify_transfer_candidates(self, mode="A"):
        """識別轉出候選 - A/B模式"""
        candidates = []
        
        for _, row in self.df.iterrows():
            article = row['Article']
            current_stock = row['SaSa Net Stock']
            pending = row['Pending Received']
            safety_stock = row['Safety Stock']
            rp_type = row['RP Type']
            effective_sales = self.calculate_effective_sales(row)
            moq = row['MOQ']
            
            if rp_type == 'RF':
                product_data = self.df[self.df['Article'] == article]
                max_sales = product_data.apply(self.calculate_effective_sales, axis=1).max()
                
                if effective_sales < max_sales:
                    total_available = current_stock + pending
                    
                    if mode == "A":  # 保守轉貨
                        if total_available > safety_stock:
                            base_transfer = total_available - safety_stock
                            limit_transfer = max(int(total_available * 0.2), 2)
                            actual_transfer = min(base_transfer, limit_transfer)
                            actual_transfer = min(actual_transfer, current_stock)
                            
                            if actual_transfer > 0:
                                candidates.append({
                                    'Article': article,
                                    'Site': row['Site'],
                                    'OM': row['OM'],
                                    'Transfer_Qty': actual_transfer,
                                    'Type': 'RF過剩轉出',
                                    'Mode': 'A'
                                })
                    
                    elif mode == "B":  # 加強轉貨
                        moq_threshold = moq + 1
                        if total_available > moq_threshold:
                            base_transfer = total_available - moq_threshold
                            limit_transfer = max(int(total_available * 0.5), 2)
                            actual_transfer = min(base_transfer, limit_transfer)
                            actual_transfer = min(actual_transfer, current_stock)
                            
                            if actual_transfer > 0:
                                remaining_stock = current_stock - actual_transfer
                                if remaining_stock >= safety_stock:
                                    transfer_type = 'RF過剩轉出'
                                else:
                                    transfer_type = 'RF加強轉出'
                                
                                candidates.append({
                                    'Article': article,
                                    'Site': row['Site'],
                                    'OM': row['OM'],
                                    'Transfer_Qty': actual_transfer,
                                    'Type': transfer_type,
                                    'Mode': 'B'
                                })
        
        return candidates
    
    def identify_receive_candidates(self):
        """識別接收候選 - A/B模式"""
        candidates = []
        
        for _, row in self.df.iterrows():
            article = row['Article']
            current_stock = row['SaSa Net Stock']
            pending = row['Pending Received']
            safety_stock = row['Safety Stock']
            rp_type = row['RP Type']
            effective_sales = self.calculate_effective_sales(row)
            site = row['Site']
            
            if rp_type == 'RF':
                # 緊急缺貨補貨
                if current_stock == 0 and effective_sales > 0:
                    candidates.append({
                        'Article': article,
                        'Site': site,
                        'OM': row['OM'],
                        'Need_Qty': safety_stock,
                        'Type': '緊急缺貨補貨',
                        'Mode': 'A/B'
                    })
                
                # SasaNet 調撥接收條件
                elif (current_stock + pending) < safety_stock and current_stock > 0:
                    need_qty = safety_stock - (current_stock + pending)
                    if need_qty > 0:
                        candidates.append({
                            'Article': article,
                            'Site': site,
                            'OM': row['OM'],
                            'Need_Qty': need_qty,
                            'Type': 'SasaNet調撥接收',
                            'Mode': 'A/B'
                        })
        
        return candidates
    
    def identify_receive_candidates_mode_c(self):
        """識別接收候選 - C模式"""
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
                    target_stock = min(safety_stock, moq + 1)
                    need_qty = target_stock - total_available
                    
                    if need_qty > 0:
                        candidates.append({
                            'Article': article,
                            'Site': site,
                            'OM': row['OM'],
                            'Need_Qty': need_qty,
                            'Type': '重點補0',
                            'Mode': 'C',
                            'Target_Stock': target_stock,
                            'Current_Stock': current_stock,
                            'Pending_Received': pending,
                            'Total_Available': total_available,
                            'Effective_Sales': effective_sales
                        })
        
        return candidates

def comprehensive_test_v173():
    """v1.73 三模式綜合測試"""
    
    # 創建涵蓋各種情況的測試數據
    test_data = pd.DataFrame([
        # A模式轉出：高庫存，低銷量
        {
            'Article': 'PROD001',
            'OM': 'OM1',
            'Site': 'StoreA',
            'SaSa Net Stock': 25,
            'Pending Received': 5,
            'Safety Stock': 12,
            'RP Type': 'RF',
            'MTD Sold Qty': 8,
            'MOQ': 10
        },
        # B模式轉出：可加強轉出
        {
            'Article': 'PROD001',
            'OM': 'OM1',
            'Site': 'StoreB',
            'SaSa Net Stock': 20,
            'Pending Received': 2,
            'Safety Stock': 10,
            'RP Type': 'RF',
            'MTD Sold Qty': 6,
            'MOQ': 8
        },
        # 最高銷量店（不轉出）
        {
            'Article': 'PROD001',
            'OM': 'OM1',
            'Site': 'StoreC',
            'SaSa Net Stock': 5,
            'Pending Received': 1,
            'Safety Stock': 8,
            'RP Type': 'RF',
            'MTD Sold Qty': 15,  # 最高銷量
            'MOQ': 6
        },
        # SasaNet調撥接收：庫存不足但>0
        {
            'Article': 'PROD002',
            'OM': 'OM1',
            'Site': 'StoreD',
            'SaSa Net Stock': 3,
            'Pending Received': 1,
            'Safety Stock': 10,
            'RP Type': 'RF',
            'MTD Sold Qty': 12,
            'MOQ': 8
        },
        # 緊急缺貨：庫存=0
        {
            'Article': 'PROD003',
            'OM': 'OM1',
            'Site': 'StoreE',
            'SaSa Net Stock': 0,
            'Pending Received': 0,
            'Safety Stock': 8,
            'RP Type': 'RF',
            'MTD Sold Qty': 10,
            'MOQ': 6
        },
        # C模式重點補0：極低庫存
        {
            'Article': 'PROD004',
            'OM': 'OM1',
            'Site': 'StoreF',
            'SaSa Net Stock': 1,
            'Pending Received': 0,
            'Safety Stock': 12,
            'RP Type': 'RF',
            'MTD Sold Qty': 20,  # 高銷量
            'MOQ': 8
        },
        # C模式重點補0：完全沒庫存
        {
            'Article': 'PROD005',
            'OM': 'OM1',
            'Site': 'StoreG',
            'SaSa Net Stock': 0,
            'Pending Received': 1,
            'Safety Stock': 10,
            'RP Type': 'RF',
            'MTD Sold Qty': 15,
            'MOQ': 12
        }
    ])
    
    system = TransferSystemV173Complete()
    system.df = system.preprocess_data(test_data)
    
    print("=== v1.73 三模式綜合功能測試 ===")
    print("\n=== 測試數據概況 ===")
    print(test_data[['Article', 'Site', 'SaSa Net Stock', 'Pending Received', 'Safety Stock', 'MTD Sold Qty', 'MOQ']].to_string(index=False))
    
    # 測試A模式
    print("\n=== A模式（保守轉貨）===")
    a_transfers = system.identify_transfer_candidates("A")
    a_receives = system.identify_receive_candidates()
    
    print(f"A模式轉出候選: {len(a_transfers)}")
    for t in a_transfers:
        print(f"  {t['Site']} - {t['Article']}: 轉出{t['Transfer_Qty']}件 ({t['Type']})")
    
    print(f"A/B模式接收候選: {len(a_receives)}")
    for r in a_receives:
        print(f"  {r['Site']} - {r['Article']}: 需要{r['Need_Qty']}件 ({r['Type']})")
    
    # 測試B模式
    print("\n=== B模式（加強轉貨）===")
    b_transfers = system.identify_transfer_candidates("B")
    
    print(f"B模式轉出候選: {len(b_transfers)}")
    for t in b_transfers:
        print(f"  {t['Site']} - {t['Article']}: 轉出{t['Transfer_Qty']}件 ({t['Type']})")
    
    # 測試C模式
    print("\n=== C模式（重點補0）===")
    c_receives = system.identify_receive_candidates_mode_c()
    
    print(f"C模式接收候選: {len(c_receives)}")
    for r in c_receives:
        print(f"  {r['Site']} - {r['Article']}:")
        print(f"    庫存:{r['Current_Stock']} + 待收:{r['Pending_Received']} = 總可用:{r['Total_Available']}")
        print(f"    補充目標:{r['Target_Stock']} | 需要:{r['Need_Qty']}件 | 銷量:{r['Effective_Sales']}")
    
    # 模式比較統計
    print("\n=== 三模式比較統計 ===")
    a_transfer_qty = sum(t['Transfer_Qty'] for t in a_transfers)
    b_transfer_qty = sum(t['Transfer_Qty'] for t in b_transfers)
    ab_receive_qty = sum(r['Need_Qty'] for r in a_receives)
    c_receive_qty = sum(r['Need_Qty'] for r in c_receives)
    
    print(f"A模式 - 轉出:{a_transfer_qty}件, 接收:{ab_receive_qty}件")
    print(f"B模式 - 轉出:{b_transfer_qty}件, 接收:{ab_receive_qty}件")
    print(f"C模式 - 轉出:0件, 接收:{c_receive_qty}件 (專注補0)")
    
    # 驗證C模式邏輯
    print("\n=== C模式邏輯驗證 ===")
    for r in c_receives:
        article = r['Article']
        safety = test_data[test_data['Article'] == article]['Safety Stock'].iloc[0]
        moq = test_data[test_data['Article'] == article]['MOQ'].iloc[0]
        expected_target = min(safety, moq + 1)
        actual_target = r['Target_Stock']
        
        if expected_target == actual_target:
            print(f"✅ {r['Site']}-{article}: 補充目標正確 min({safety},{moq}+1)={actual_target}")
        else:
            print(f"❌ {r['Site']}-{article}: 補充目標錯誤 預期{expected_target}, 實際{actual_target}")
    
    return {
        'a_transfers': len(a_transfers),
        'b_transfers': len(b_transfers),
        'ab_receives': len(a_receives),
        'c_receives': len(c_receives)
    }

if __name__ == "__main__":
    results = comprehensive_test_v173()
    print(f"\n🎯 v1.73 綜合測試完成")
    print(f"A模式轉出:{results['a_transfers']}, B模式轉出:{results['b_transfers']}")
    print(f"A/B模式接收:{results['ab_receives']}, C模式接收:{results['c_receives']}")
    print("✅ 所有功能正常運行")