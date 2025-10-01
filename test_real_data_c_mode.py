"""
使用真實數據 SUI LIP GU.xlsx 測試 v1.73 C模式（重點補0）功能
"""
import pandas as pd

class SimpleTransferSystemV173Real:
    """使用真實數據的v1.73系統 - 包含C模式"""
    
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

def analyze_real_data_c_mode():
    """分析真實數據的C模式情況"""
    try:
        # 讀取數據文件
        file_path = '/workspace/user_input_files/SUI LIP GU.xlsx'
        excel_file = pd.ExcelFile(file_path)
        df = pd.read_excel(file_path, sheet_name=excel_file.sheet_names[0])
        
        print("=== v1.73 C模式真實數據測試 ===")
        print(f"數據維度: {df.shape}")
        
        # 創建系統並預處理數據
        system = SimpleTransferSystemV173Real()
        df_processed = system.preprocess_data(df)
        system.df = df_processed
        
        # 分析極低庫存情況
        print("\n=== 極低庫存情況分析 ===")
        df_rf = df_processed[df_processed['RP Type'] == 'RF'].copy()
        df_rf['Total_Available'] = df_rf['SaSa Net Stock'] + df_rf['Pending Received']
        
        # 統計各庫存水位
        print("庫存水位分佈:")
        print(f"- 總可用量 = 0: {len(df_rf[df_rf['Total_Available'] == 0])}件")
        print(f"- 總可用量 = 1: {len(df_rf[df_rf['Total_Available'] == 1])}件")
        print(f"- 總可用量 ≤ 1: {len(df_rf[df_rf['Total_Available'] <= 1])}件")
        print(f"- 總可用量 ≤ 5: {len(df_rf[df_rf['Total_Available'] <= 5])}件")
        print(f"- RF類型總數: {len(df_rf)}件")
        
        # 顯示極低庫存的具體案例
        critical_cases = df_rf[df_rf['Total_Available'] <= 1].copy()
        if len(critical_cases) > 0:
            print(f"\n極低庫存（≤1）案例前10項:")
            display_cols = ['Site', 'Article', 'SaSa Net Stock', 'Pending Received', 'Total_Available', 'Safety Stock', 'MOQ', 'MTD Sold Qty']
            print(critical_cases[display_cols].head(10).to_string(index=False))
        
        # 測試C模式功能
        print("\n=== C模式接收候選識別 ===")
        c_candidates = system.identify_receive_candidates_mode_c()
        
        print(f"C模式候選數量: {len(c_candidates)}")
        
        if c_candidates:
            # 統計分析
            total_need = sum(c['Need_Qty'] for c in c_candidates)
            avg_need = total_need / len(c_candidates) if c_candidates else 0
            high_sales_count = len([c for c in c_candidates if c['Effective_Sales'] > 0])
            
            print(f"總需求數量: {total_need}件")
            print(f"平均每項需求: {avg_need:.1f}件")
            print(f"有銷量的項目: {high_sales_count}/{len(c_candidates)}")
            
            # 顯示前10個候選
            print(f"\n前10個重點補0候選:")
            for i, candidate in enumerate(c_candidates[:10]):
                print(f"  {i+1}. {candidate['Site']} - {candidate['Article']}:")
                print(f"     庫存:{candidate['Current_Stock']} + 待收:{candidate['Pending_Received']} = 總可用:{candidate['Total_Available']}")
                print(f"     補充目標:{candidate['Target_Stock']} = min(安全庫存{candidate['Safety_Stock']}, MOQ{candidate['MOQ']}+1)")
                print(f"     需要補充:{candidate['Need_Qty']}件 | 銷量:{candidate['Effective_Sales']}")
            
            # 按店舖統計
            print(f"\n=== 按店舖統計 ===")
            site_stats = {}
            for candidate in c_candidates:
                site = candidate['Site']
                if site not in site_stats:
                    site_stats[site] = {'count': 0, 'total_need': 0}
                site_stats[site]['count'] += 1
                site_stats[site]['total_need'] += candidate['Need_Qty']
            
            # 顯示需求最多的店舖
            sorted_sites = sorted(site_stats.items(), key=lambda x: x[1]['total_need'], reverse=True)
            print("需求量最高的前10個店舖:")
            for i, (site, stats) in enumerate(sorted_sites[:10]):
                print(f"  {i+1}. {site}: {stats['count']}項商品，共需{stats['total_need']}件")
        
        return c_candidates
        
    except Exception as e:
        print(f"分析失敗: {str(e)}")
        return []

if __name__ == "__main__":
    candidates = analyze_real_data_c_mode()
    print(f"\n🎯 真實數據C模式分析完成，發現 {len(candidates)} 個重點補0需求")