"""
改進版調貨建議系統（繁體中文版）
實施混合策略優化20%轉出限制規則

使用方法:
    python transfer_recommendation_improved_tc.py <input_file.xlsx>
    
範例:
    python transfer_recommendation_improved_tc.py ELE_15Sep2025.xlsx
"""

import pandas as pd
import sys
import os
import warnings
warnings.filterwarnings('ignore')

def improved_process_data_tc(df):
    """
    改進的調貨建議處理函數（繁體中文版）
    
    主要改進:
    1. 階梯式轉出限制 - 小庫存店鋪允許更高比例轉出
    2. 降低最小轉出量從2件到1件
    3. 動態計算轉出上限
    """
    
    transfer_recommendations = []
    
    print("=== 改進版調貨建議處理 ===")
    
    for article in df['Article'].unique():
        print(f"處理產品: {article}")
        article_data = df[df['Article'] == article].copy()
        
        nd_data = article_data[article_data['RP Type'] == 'ND']
        rf_data = article_data[article_data['RP Type'] == 'RF']
        
        print(f"  ND記錄: {len(nd_data)}, RF記錄: {len(rf_data)}")
        
        # Priority 1: ND缺貨補充 (保持原邏輯)
        nd_shortage = nd_data[nd_data['SaSa Net Stock'] <= 0]
        rf_surplus = rf_data[rf_data['SaSa Net Stock'] > 2]
        
        print(f"  ND缺貨: {len(nd_shortage)}, RF過剩: {len(rf_surplus)}")
        
        for _, nd_row in nd_shortage.iterrows():
            shortage = 2 - nd_row['SaSa Net Stock']
            
            for _, rf_row in rf_surplus.iterrows():
                if rf_row['Shop'] != nd_row['Shop']:
                    available = rf_row['SaSa Net Stock'] - 2
                    transfer_qty = min(shortage, available)
                    
                    if transfer_qty >= 1:  # 降低最小轉出量到1件
                        transfer_recommendations.append({
                            '優先級': 1,
                            '類型': 'ND缺貨補充',
                            '產品編號': article,
                            '調出店鋪': rf_row['Shop'],
                            '調入店鋪': nd_row['Shop'],
                            '調貨數量': int(transfer_qty),
                            '調出店庫存': rf_row['SaSa Net Stock'],
                            '調入店庫存': nd_row['SaSa Net Stock'],
                            '轉出方法': '原規則',
                            '原因': f'ND缺貨{shortage}件，調入{transfer_qty}件'
                        })
                        shortage -= transfer_qty
                        if shortage <= 0:
                            break
        
        # Priority 2: RF內部調配 (應用改進規則)
        rf_shortage = rf_data[rf_data['SaSa Net Stock'] <= 2]
        
        for _, surplus_row in rf_surplus.iterrows():
            excess = surplus_row['SaSa Net Stock'] - 2
            current_stock = surplus_row['SaSa Net Stock']
            pending = surplus_row['Pending Received']
            total_available = current_stock + pending
            
            # 改進的轉出限制計算
            if current_stock <= 10:
                # 小庫存店鋪：30%轉出，最少1件
                transfer_cap = max(total_available * 0.3, 1)
                method = '小庫存30%規則'
            else:
                # 大庫存店鋪：20%轉出，最少2件
                transfer_cap = max(total_available * 0.2, 2)
                method = '大庫存20%規則'
            
            # 實際可轉出量
            max_transfer = min(excess, transfer_cap)
            
            print(f"    {surplus_row['Shop']}: 庫存{current_stock}, 過剩{excess}, 限制{transfer_cap:.1f}, 可轉{max_transfer:.1f}")
            
            if max_transfer >= 1:  # 最少1件才轉
                for _, shortage_row in rf_shortage.iterrows():
                    if surplus_row['Shop'] != shortage_row['Shop']:
                        need = 3 - shortage_row['SaSa Net Stock']
                        actual_transfer = min(max_transfer, need)
                        
                        if actual_transfer >= 1:
                            transfer_recommendations.append({
                                '優先級': 2,
                                '類型': 'RF內部調配',
                                '產品編號': article,
                                '調出店鋪': surplus_row['Shop'],
                                '調入店鋪': shortage_row['Shop'],
                                '調貨數量': int(actual_transfer),
                                '調出店庫存': surplus_row['SaSa Net Stock'],
                                '調入店庫存': shortage_row['SaSa Net Stock'],
                                '轉出上限': round(transfer_cap, 1),
                                '轉出方法': method,
                                '原因': f'{method}，可轉{max_transfer:.1f}件，實際{actual_transfer}件'
                            })
                            max_transfer -= actual_transfer
                            if max_transfer < 1:
                                break
    
    return pd.DataFrame(transfer_recommendations)


def compare_results_tc(original_df, improved_df):
    """對比原版和改進版的結果（繁體中文版）"""
    
    print("\\n=== 改進效果對比 ===")
    print(f"{'指標':<20} {'原版':<15} {'改進版':<15} {'提升幅度':<15}")
    print("-" * 70)
    
    # 建議數量對比
    orig_count = len(original_df) if len(original_df) > 0 else 0
    impr_count = len(improved_df) if len(improved_df) > 0 else 0
    count_improve = f"+{impr_count - orig_count}" if impr_count > orig_count else str(impr_count - orig_count)
    print(f"{'調貨建議數':<20} {orig_count:<15} {impr_count:<15} {count_improve:<15}")
    
    # 調貨總量對比
    orig_qty = original_df['Transfer_Qty'].sum() if len(original_df) > 0 and 'Transfer_Qty' in original_df.columns else 0
    impr_qty = improved_df['調貨數量'].sum() if len(improved_df) > 0 else 0
    qty_improve = f"+{impr_qty - orig_qty}" if impr_qty > orig_qty else str(impr_qty - orig_qty)
    print(f"{'總調貨量':<20} {orig_qty:<15} {impr_qty:<15} {qty_improve:<15}")
    
    # 平均調貨量對比
    orig_avg = orig_qty / orig_count if orig_count > 0 else 0
    impr_avg = impr_qty / impr_count if impr_count > 0 else 0
    avg_improve = f"+{impr_avg - orig_avg:.1f}" if impr_avg > orig_avg else f"{impr_avg - orig_avg:.1f}"
    print(f"{'平均調貨量':<20} {orig_avg:<15.1f} {impr_avg:<15.1f} {avg_improve:<15}")
    
    # 覆蓋店鋪數對比
    if len(original_df) > 0 and 'From_Shop' in original_df.columns and 'To_Shop' in original_df.columns:
        orig_shops = len(set(list(original_df['From_Shop']) + list(original_df['To_Shop'])))
    else:
        orig_shops = 0
    
    if len(improved_df) > 0:
        impr_shops = len(set(list(improved_df['調出店鋪']) + list(improved_df['調入店鋪'])))
    else:
        impr_shops = 0
    
    shops_improve = f"+{impr_shops - orig_shops}" if impr_shops > orig_shops else str(impr_shops - orig_shops)
    print(f"{'涉及店鋪數':<20} {orig_shops:<15} {impr_shops:<15} {shops_improve:<15}")


def analyze_improved_results_tc(improved_df):
    """分析改進版結果的詳細情況（繁體中文版）"""
    
    print("\\n=== 改進版調貨建議詳細分析 ===")
    print(f"總建議數: {len(improved_df)}條")
    
    if len(improved_df) == 0:
        print("沒有生成任何調貨建議！")
        return
    
    # 按類型分析
    print(f"\\n按類型分布:")
    print(improved_df['類型'].value_counts())
    
    # 按轉出方法分析
    print(f"\\n按轉出方法分布:")
    print(improved_df['轉出方法'].value_counts())
    
    # 調貨量分析
    print(f"\\n調貨量統計:")
    print(f"總調貨量: {improved_df['調貨數量'].sum()}件")
    print(f"平均調貨量: {improved_df['調貨數量'].mean():.2f}件")
    print(f"調貨量分布:")
    print(improved_df['調貨數量'].value_counts().sort_index())
    
    # 最活躍的調出店鋪
    print(f"\\n最活躍的調出店鋪(前10):")
    from_stats = improved_df['調出店鋪'].value_counts().head(10)
    for shop, count in from_stats.items():
        total_qty = improved_df[improved_df['調出店鋪'] == shop]['調貨數量'].sum()
        print(f"  {shop}: {count}次調出, 共{total_qty}件")
    
    # 最需要補充的調入店鋪
    print(f"\\n最需要補充的調入店鋪(前10):")
    to_stats = improved_df['調入店鋪'].value_counts().head(10)
    for shop, count in to_stats.items():
        total_qty = improved_df[improved_df['調入店鋪'] == shop]['調貨數量'].sum()
        print(f"  {shop}: {count}次調入, 共{total_qty}件")


if __name__ == "__main__":
    # 檢查命令行參數
    if len(sys.argv) != 2:
        print("=" * 60)
        print("📦 改進版調貨建議系統（繁體中文版）")
        print("=" * 60)
        print()
        print("🔧 使用方法:")
        print("   python transfer_recommendation_improved_tc.py <輸入文件.xlsx>")
        print()
        print("💡 範例:")
        print("   python transfer_recommendation_improved_tc.py ELE_15Sep2025.xlsx")
        print("   python transfer_recommendation_improved_tc.py my_inventory_data.xlsx")
        print()
        print("📋 輸入文件需包含以下欄位:")
        print("   - Article (產品編號)")
        print("   - OM (營運市場)")  
        print("   - RP Type (補貨類型: ND/RF)")
        print("   - Shop (店鋪)")
        print("   - SaSa Net Stock (薩薩淨庫存)")
        print("   - Pending Received (待收庫存)")
        print("   - Safety Stock (安全庫存)")
        print("   - Last Month Sold Qty (上月銷量)")
        print("   - MTD Sold Qty (本月至今銷量)")
        print()
        sys.exit(1)
    
    # 讀取輸入數據
    input_file = sys.argv[1]
    
    # 檢查文件是否存在
    if not os.path.exists(input_file):
        print(f"❌ 錯誤: 找不到輸入文件 '{input_file}'")
        print(f"   請確認文件路徑是否正確")
        sys.exit(1)
    
    print(f"📖 正在讀取文件: {input_file}")
    
    try:
        df = pd.read_excel(input_file)
        print(f"✅ 成功讀取 {len(df)} 行數據")
    except Exception as e:
        print(f"❌ 讀取文件失敗: {e}")
        sys.exit(1)
    
    # 讀取原版結果（如果存在）
    try:
        original_results = pd.read_excel('調貨建議_分析結果.xlsx')
    except:
        original_results = pd.DataFrame()
    
    # 生成改進版結果
    improved_results = improved_process_data_tc(df)
    
    # 保存改進版結果（繁體中文版）
    improved_results.to_excel('調貨建議_改進版結果_繁體.xlsx', index=False)
    
    # 對比分析
    compare_results_tc(original_results, improved_results)
    
    # 詳細分析改進版結果
    analyze_improved_results_tc(improved_results)
    
    print(f"\\n改進版結果已保存到: 調貨建議_改進版結果_繁體.xlsx")
    print(f"詳細分析報告: 調貨建議效果分析報告_繁體.md")
    print(f"效果總結報告: 調貨建議改進效果總結_繁體.md")
