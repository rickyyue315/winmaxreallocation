"""
使用真實數據 SUI LIP GU.xlsx 測試 v1.72 衝突解決功能
"""
import pandas as pd
import numpy as np

def analyze_real_data():
    """分析真實數據文件結構"""
    try:
        # 讀取Excel文件
        file_path = '/workspace/user_input_files/SUI LIP GU.xlsx'
        
        # 先查看所有工作表
        excel_file = pd.ExcelFile(file_path)
        print("=== Excel文件分析 ===")
        print(f"工作表: {excel_file.sheet_names}")
        
        # 讀取第一個工作表
        df = pd.read_excel(file_path, sheet_name=excel_file.sheet_names[0])
        
        print(f"\n數據維度: {df.shape}")
        print(f"列名: {list(df.columns)}")
        
        # 顯示前幾行數據
        print("\n=== 數據預覽 ===")
        print(df.head())
        
        # 檢查是否包含必要的列
        required_columns = ['Article', 'Site', 'OM', 'SaSa Net Stock', 'Safety Stock', 'RP Type', 'MTD Sold Qty', 'MOQ', 'Pending Received']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"\n⚠️ 缺少必要列: {missing_columns}")
            print("可用列:")
            for i, col in enumerate(df.columns):
                print(f"  {i}: {col}")
        else:
            print("\n✅ 所有必要列都存在")
            
        return df, None
        
    except Exception as e:
        print(f"讀取文件錯誤: {str(e)}")
        return None, str(e)

class SimpleTransferSystemV172Real:
    """使用真實數據的v1.72系統"""
    
    def __init__(self):
        self.df = None
    
    def preprocess_data(self, df):
        """預處理數據，確保數據類型正確"""
        df = df.copy()
        
        # 確保數值列為數值類型
        numeric_columns = ['SaSa Net Stock', 'Safety Stock', 'MTD Sold Qty', 'MOQ', 'Pending Received']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 確保字符列為字符類型
        string_columns = ['Article', 'Site', 'OM', 'RP Type']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        return df
    
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
                                    'Effective_Sales': effective_sales
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
                
                # SasaNet 調撥接收條件 (v1.71新增)
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
        receive_lookup = {}
        for receive in receive_candidates:
            key = (receive['Site'], receive['Article'], receive['OM'])
            receive_lookup[key] = receive
        
        filtered_transfer_candidates = []
        conflicts_resolved = []
        
        for transfer in transfer_candidates:
            key = (transfer['Site'], transfer['Article'], transfer['OM'])
            
            if key in receive_lookup:
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
            else:
                filtered_transfer_candidates.append(transfer)
        
        return filtered_transfer_candidates, receive_candidates, conflicts_resolved

def test_real_data_v172():
    """使用真實數據測試v1.72功能"""
    
    # 分析數據文件
    print("=== 步驟1：數據文件分析 ===")
    df, error = analyze_real_data()
    if error:
        print(f"無法讀取數據文件: {error}")
        return
    
    # 創建測試系統
    system = SimpleTransferSystemV172Real()
    
    # 預處理數據
    print("\n=== 步驟2：數據預處理 ===")
    df_processed = system.preprocess_data(df)
    system.df = df_processed
    
    print(f"處理後數據維度: {df_processed.shape}")
    print(f"RF類型記錄數: {len(df_processed[df_processed['RP Type'] == 'RF'])}")
    
    # 測試模式B候選識別
    print("\n=== 步驟3：模式B候選識別 ===")
    transfer_candidates = system.identify_transfer_candidates("B")
    receive_candidates = system.identify_receive_candidates()
    
    print(f"轉出候選數: {len(transfer_candidates)}")
    print(f"接收候選數: {len(receive_candidates)}")
    
    if transfer_candidates:
        print("\n轉出候選前5項:")
        for i, candidate in enumerate(transfer_candidates[:5]):
            print(f"  {i+1}. {candidate['Site']} - {candidate['Article']} - 轉出{candidate['Transfer_Qty']}件 - {candidate['Type']}")
    
    if receive_candidates:
        print("\n接收候選前5項:")
        for i, candidate in enumerate(receive_candidates[:5]):
            print(f"  {i+1}. {candidate['Site']} - {candidate['Article']} - 需要{candidate['Need_Qty']}件 - {candidate['Type']}")
    
    # 衝突檢查
    print("\n=== 步驟4：衝突檢查 ===")
    conflicts = []
    for transfer in transfer_candidates:
        for receive in receive_candidates:
            if (transfer['Site'] == receive['Site'] and 
                transfer['Article'] == receive['Article'] and
                transfer['OM'] == receive['OM']):
                conflicts.append({
                    'site': transfer['Site'],
                    'article': transfer['Article'],
                    'om': transfer['OM']
                })
    
    if conflicts:
        print(f"⚠️  發現 {len(conflicts)} 個衝突:")
        for conflict in conflicts:
            print(f"   {conflict['site']} - {conflict['article']} (OM: {conflict['om']})")
    else:
        print("✅ 無衝突發現")
    
    # 應用v1.72衝突解決
    print("\n=== 步驟5：v1.72衝突解決 ===")
    filtered_transfers, filtered_receives, resolved_conflicts = system.resolve_same_store_conflicts(
        transfer_candidates, receive_candidates)
    
    if resolved_conflicts:
        print(f"🔧 解決了 {len(resolved_conflicts)} 個衝突:")
        for conflict in resolved_conflicts:
            print(f"   {conflict['site']} - {conflict['article']}: 移除轉出{conflict['transfer_qty']}件({conflict['transfer_type']})，保持接收{conflict['receive_qty']}件({conflict['receive_type']})")
    else:
        print("無衝突需要解決")
    
    # 最終驗證
    print("\n=== 步驟6：最終驗證 ===")
    final_conflicts = []
    for transfer in filtered_transfers:
        for receive in filtered_receives:
            if (transfer['Site'] == receive['Site'] and 
                transfer['Article'] == receive['Article'] and
                transfer['OM'] == receive['OM']):
                final_conflicts.append(f"{transfer['Site']} - {transfer['Article']}")
    
    if final_conflicts:
        print(f"❌ 仍有衝突: {final_conflicts}")
        return False
    else:
        print("✅ 所有衝突已解決！")
        
    # 統計總結
    print("\n=== 總結統計 ===")
    print(f"原始轉出候選: {len(transfer_candidates)}")
    print(f"修正後轉出候選: {len(filtered_transfers)}")
    print(f"接收候選: {len(receive_candidates)}")
    print(f"解決衝突數: {len(resolved_conflicts)}")
    
    return True

if __name__ == "__main__":
    success = test_real_data_v172()
    print(f"\n🎯 真實數據測試結果: {'成功' if success else '失敗'}")