"""
測試模式B同店舖同SKU轉出/接收衝突問題 - 簡化版本
"""
import pandas as pd
import numpy as np

class SimpleTransferSystem:
    """簡化的調貨系統 - 僅包含核心邏輯"""
    
    def __init__(self):
        self.df = None
    
    def calculate_effective_sales(self, row):
        """計算有效銷量"""
        return row['MTD Sold Qty']
    
    def identify_transfer_candidates(self, mode="A"):
        """識別轉出候選 - 簡化版"""
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
                # 計算該產品的最高銷量
                product_data = self.df[self.df['Article'] == article]
                max_sales = product_data.apply(self.calculate_effective_sales, axis=1).max()
                
                # 只有銷量低於最高銷量的才考慮轉出
                if effective_sales < max_sales:
                    total_available = current_stock + pending
                    
                    if mode == "B":  # 加強轉貨模式
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
                                    'Priority': 2,
                                    'Original_Stock': current_stock,
                                    'Safety_Stock': safety_stock,
                                    'Effective_Sales': effective_sales,
                                    'Remaining_Stock': remaining_stock
                                })
        
        candidates.sort(key=lambda x: (x['Priority'], x['Effective_Sales']))
        return candidates
    
    def identify_receive_candidates(self):
        """識別接收候選 - 簡化版"""
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
                product_data = self.df[self.df['Article'] == article]
                max_sales = product_data.apply(self.calculate_effective_sales, axis=1).max()
                
                # 緊急缺貨補貨
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
                        'Effective_Sales': effective_sales
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
                            'Priority': 2,
                            'Current_Stock': current_stock,
                            'Safety_Stock': safety_stock,
                            'Effective_Sales': effective_sales
                        })
                
                # 潛在缺貨補貨
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
                            'Effective_Sales': effective_sales
                        })
        
        candidates.sort(key=lambda x: (x['Priority'], -x['Effective_Sales']))
        return candidates

def test_same_store_conflict():
    """測試同店舖同SKU同時轉出和接收的衝突情況"""
    
    # 創建測試數據 - 模擬可能發生衝突的情況
    test_data = pd.DataFrame([
        {
            'Article': 'TEST001',
            'OM': 'OM1',
            'Site': 'Store A',
            'SaSa Net Stock': 15,  # 高庫存 - 可能轉出
            'Pending Received': 0,
            'Safety Stock': 8,
            'RP Type': 'RF',
            'MTD Sold Qty': 5,     # 低銷量 - 適合轉出
            'MOQ': 6
        },
        {
            'Article': 'TEST001',  # 同一SKU
            'OM': 'OM1',          # 同一OM
            'Site': 'Store A',     # 同一店舖
            'SaSa Net Stock': 3,   # 低庫存 - 需要接收
            'Pending Received': 0,
            'Safety Stock': 8,
            'RP Type': 'RF',
            'MTD Sold Qty': 12,    # 高銷量 - 需要補貨
            'MOQ': 6
        },
        {
            'Article': 'TEST001',
            'OM': 'OM1',
            'Site': 'Store B',
            'SaSa Net Stock': 20,
            'Pending Received': 0,
            'Safety Stock': 10,
            'RP Type': 'RF',
            'MTD Sold Qty': 8,
            'MOQ': 6
        }
    ])
    
    system = SimpleTransferSystem()
    system.df = test_data
    
    print("=== 測試數據 ===")
    print(test_data[['Article', 'OM', 'Site', 'SaSa Net Stock', 'Safety Stock', 'MTD Sold Qty']])
    
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
    
    return conflicts

if __name__ == "__main__":
    conflicts = test_same_store_conflict()
    print(f"\n總結：發現 {len(conflicts)} 個衝突")