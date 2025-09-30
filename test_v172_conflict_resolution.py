"""
測試v1.72修正：模式B同店舖同SKU轉出/接收衝突問題解決方案
"""
import pandas as pd

class SimpleTransferSystemV172:
    """模擬v1.72的衝突解決功能"""
    
    def __init__(self):
        self.df = None
    
    def calculate_effective_sales(self, row):
        return row['MTD Sold Qty']
    
    def identify_transfer_candidates(self, mode="B"):
        """識別轉出候選"""
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
                    
                    if mode == "B":
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
        
        return candidates
    
    def identify_receive_candidates(self):
        """識別接收候選"""
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
        
        return candidates
    
    def resolve_same_store_conflicts(self, transfer_candidates, receive_candidates):
        """v1.72: 解決同店舖同SKU衝突問題"""
        # 創建接收候選的查找表
        receive_lookup = {}
        for receive in receive_candidates:
            key = (receive['Site'], receive['Article'], receive['OM'])
            receive_lookup[key] = receive
        
        # 檢查轉出候選中的衝突並移除
        filtered_transfer_candidates = []
        conflicts_resolved = []
        
        for transfer in transfer_candidates:
            key = (transfer['Site'], transfer['Article'], transfer['OM'])
            
            if key in receive_lookup:
                # 發現衝突：優先保持接收，移除轉出
                receive_info = receive_lookup[key]
                conflicts_resolved.append({
                    'site': transfer['Site'],
                    'article': transfer['Article'],
                    'om': transfer['OM'],
                    'transfer_qty': transfer['Transfer_Qty'],
                    'transfer_type': transfer['Type'],
                    'receive_qty': receive_info['Need_Qty'],
                    'receive_type': receive_info['Type']
                })
                continue
            else:
                # 無衝突，保留轉出候選
                filtered_transfer_candidates.append(transfer)
        
        return filtered_transfer_candidates, receive_candidates, conflicts_resolved

def test_conflict_resolution():
    """測試衝突解決功能"""
    
    # 創建包含衝突的測試數據
    test_data = pd.DataFrame([
        {
            'Article': 'TEST001',
            'OM': 'OM1',
            'Site': 'Store A',
            'SaSa Net Stock': 15,  # 高庫存 - 會被識別為轉出候選
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
            'SaSa Net Stock': 3,   # 低庫存 - 會被識別為接收候選
            'Pending Received': 0,
            'Safety Stock': 8,
            'RP Type': 'RF',
            'MTD Sold Qty': 12,    # 高銷量
            'MOQ': 6
        },
        {
            'Article': 'TEST002',
            'OM': 'OM1',
            'Site': 'Store A',
            'SaSa Net Stock': 20,  # 只轉出，無衝突
            'Pending Received': 0,
            'Safety Stock': 10,
            'RP Type': 'RF',
            'MTD Sold Qty': 3,
            'MOQ': 6
        },
        {
            'Article': 'TEST001',
            'OM': 'OM1',
            'Site': 'Store B',
            'SaSa Net Stock': 20,  # 其他店舖，無衝突
            'Pending Received': 0,
            'Safety Stock': 10,
            'RP Type': 'RF',
            'MTD Sold Qty': 8,
            'MOQ': 6
        }
    ])
    
    system = SimpleTransferSystemV172()
    system.df = test_data
    
    print("=== v1.72 衝突解決測試 ===")
    print("測試數據：")
    print(test_data[['Article', 'OM', 'Site', 'SaSa Net Stock', 'Safety Stock', 'MTD Sold Qty']])
    
    # 步驟1：識別原始候選
    print("\n=== 步驟1：原始候選識別 ===")
    transfer_candidates = system.identify_transfer_candidates("B")
    receive_candidates = system.identify_receive_candidates()
    
    print("轉出候選：")
    for i, candidate in enumerate(transfer_candidates):
        print(f"  {i+1}. {candidate['Site']} - {candidate['Article']} - 轉出{candidate['Transfer_Qty']}件 - {candidate['Type']}")
    
    print("接收候選：")
    for i, candidate in enumerate(receive_candidates):
        print(f"  {i+1}. {candidate['Site']} - {candidate['Article']} - 需要{candidate['Need_Qty']}件 - {candidate['Type']}")
    
    # 步驟2：檢查衝突
    print("\n=== 步驟2：衝突檢查 ===")
    conflicts = []
    for transfer in transfer_candidates:
        for receive in receive_candidates:
            if (transfer['Site'] == receive['Site'] and 
                transfer['Article'] == receive['Article'] and
                transfer['OM'] == receive['OM']):
                conflicts.append(f"{transfer['Site']} - {transfer['Article']}")
    
    if conflicts:
        print(f"⚠️  發現 {len(conflicts)} 個衝突：{conflicts}")
    else:
        print("✅ 無衝突")
    
    # 步驟3：應用衝突解決
    print("\n=== 步驟3：衝突解決 ===")
    filtered_transfers, filtered_receives, resolved_conflicts = system.resolve_same_store_conflicts(
        transfer_candidates, receive_candidates)
    
    if resolved_conflicts:
        print("🔧 已解決衝突：")
        for conflict in resolved_conflicts:
            print(f"   {conflict['site']} - {conflict['article']}: 移除轉出{conflict['transfer_qty']}件({conflict['transfer_type']})，保持接收{conflict['receive_qty']}件({conflict['receive_type']})")
    else:
        print("無衝突需要解決")
    
    # 步驟4：驗證結果
    print("\n=== 步驟4：修正後結果 ===")
    print("修正後轉出候選：")
    for i, candidate in enumerate(filtered_transfers):
        print(f"  {i+1}. {candidate['Site']} - {candidate['Article']} - 轉出{candidate['Transfer_Qty']}件 - {candidate['Type']}")
    
    print("接收候選（未變更）：")
    for i, candidate in enumerate(filtered_receives):
        print(f"  {i+1}. {candidate['Site']} - {candidate['Article']} - 需要{candidate['Need_Qty']}件 - {candidate['Type']}")
    
    # 最終驗證：檢查是否還有衝突
    print("\n=== 最終驗證 ===")
    final_conflicts = []
    for transfer in filtered_transfers:
        for receive in filtered_receives:
            if (transfer['Site'] == receive['Site'] and 
                transfer['Article'] == receive['Article'] and
                transfer['OM'] == receive['OM']):
                final_conflicts.append(f"{transfer['Site']} - {transfer['Article']}")
    
    if final_conflicts:
        print(f"❌ 仍有衝突：{final_conflicts}")
        return False
    else:
        print("✅ 衝突已完全解決！")
        return True

if __name__ == "__main__":
    success = test_conflict_resolution()
    print(f"\n測試結果：{'成功' if success else '失敗'}")