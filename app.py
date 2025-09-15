import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

def load_and_preprocess_data(uploaded_file):
    """加載並預處理數據"""
    try:
        # 讀取Excel文件，確保Article為字符串格式
        df = pd.read_excel(uploaded_file, dtype={'Article': str})
        
        # 數據清理和類型轉換
        # 處理整數欄位
        int_columns = ['SaSa Net Stock', 'Pending Received', 'Safety Stock', 'Last Month Sold Qty', 'MTD Sold Qty']
        for col in int_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            # 處理負值
            df.loc[df[col] < 0, col] = 0
            # 處理銷量異常值
            if col in ['Last Month Sold Qty', 'MTD Sold Qty']:
                mask = df[col] > 100000
                df.loc[mask, col] = 100000
                if mask.sum() > 0:
                    df.loc[mask, 'Notes'] = df.loc[mask, 'Notes'].fillna('') + '銷量數據超出範圍;'
        
        # 處理字符串欄位
        string_columns = ['OM', 'RP Type', 'Site']
        for col in string_columns:
            df[col] = df[col].fillna('').astype(str)
        
        # 添加Notes欄位如果不存在
        if 'Notes' not in df.columns:
            df['Notes'] = ''
        
        return df
        
    except Exception as e:
        st.error(f"數據加載錯誤：{str(e)}")
        return None

def calculate_effective_sold_qty(row):
    """計算有效銷量"""
    return row['Last Month Sold Qty'] if row['Last Month Sold Qty'] > 0 else row['MTD Sold Qty']

def identify_transfer_candidates(group_df):
    """識別轉出候選"""
    transfer_candidates = []
    
    for idx, row in group_df.iterrows():
        article = row['Article']
        om = row['OM']
        site = row['Site']
        rp_type = row['RP Type']
        net_stock = row['SaSa Net Stock']
        pending_received = row['Pending Received']
        safety_stock = row['Safety Stock']
        effective_sold = calculate_effective_sold_qty(row)
        
        # 計算最高銷量
        max_sold = group_df.apply(calculate_effective_sold_qty, axis=1).max()
        
        # 優先級1：ND類型轉出
        if rp_type == 'ND':
            available_qty = net_stock
            if available_qty > 0:
                transfer_candidates.append({
                    'Article': article,
                    'OM': om,
                    'Site': site,
                    'Priority': 1,
                    'Type': 'ND轉出',
                    'Available_Qty': available_qty,
                    'Effective_Sold': effective_sold
                })
        
        # 優先級2：RF類型過剩轉出（新增限制）
        elif rp_type == 'RF':
            total_stock = net_stock + pending_received
            if total_stock > safety_stock and effective_sold < max_sold:
                base_available = total_stock - safety_stock
                
                # 新增限制條件
                # 轉出上限為存貨+Pending Received的20%，且最少2件
                upper_limit = int(total_stock * 0.2)
                available_qty = min(base_available, max(upper_limit, 2))
                
                # 確保不超過實際庫存
                available_qty = min(available_qty, net_stock)
                
                if available_qty >= 2:  # 最少2件
                    transfer_candidates.append({
                        'Article': article,
                        'OM': om,
                        'Site': site,
                        'Priority': 2,
                        'Type': 'RF過剩轉出',
                        'Available_Qty': available_qty,
                        'Effective_Sold': effective_sold
                    })
    
    return transfer_candidates

def identify_receive_candidates(group_df):
    """識別接收候選"""
    receive_candidates = []
    
    # 計算最高銷量
    max_sold = group_df.apply(calculate_effective_sold_qty, axis=1).max()
    
    for idx, row in group_df.iterrows():
        article = row['Article']
        om = row['OM']
        site = row['Site']
        rp_type = row['RP Type']
        net_stock = row['SaSa Net Stock']
        pending_received = row['Pending Received']
        safety_stock = row['Safety Stock']
        effective_sold = calculate_effective_sold_qty(row)
        
        if rp_type == 'RF':
            # 優先級1：緊急缺貨補貨
            if net_stock == 0 and effective_sold > 0:
                need_qty = safety_stock
                if need_qty > 0:
                    receive_candidates.append({
                        'Article': article,
                        'OM': om,
                        'Site': site,
                        'Priority': 1,
                        'Type': '緊急缺貨補貨',
                        'Need_Qty': need_qty,
                        'Effective_Sold': effective_sold
                    })
            
            # 優先級2：潛在缺貨補貨
            elif (net_stock + pending_received) < safety_stock and effective_sold == max_sold and effective_sold > 0:
                need_qty = safety_stock - (net_stock + pending_received)
                if need_qty > 0:
                    receive_candidates.append({
                        'Article': article,
                        'OM': om,
                        'Site': site,
                        'Priority': 2,
                        'Type': '潛在缺貨補貨',
                        'Need_Qty': need_qty,
                        'Effective_Sold': effective_sold
                    })
    
    return receive_candidates

def match_transfer_receive(transfer_candidates, receive_candidates, original_df):
    """匹配轉出和接收候選"""
    recommendations = []
    
    # 排序候選
    transfer_candidates = sorted(transfer_candidates, key=lambda x: (x['Priority'], -x['Available_Qty']))
    receive_candidates = sorted(receive_candidates, key=lambda x: (x['Priority'], -x['Need_Qty']))
    
    # 匹配邏輯
    for transfer in transfer_candidates:
        if transfer['Available_Qty'] <= 0:
            continue
            
        for receive in receive_candidates:
            if receive['Need_Qty'] <= 0:
                continue
                
            # 確保不是同一個Site
            if transfer['Site'] == receive['Site']:
                continue
                
            # 計算轉移數量
            transfer_qty = min(transfer['Available_Qty'], receive['Need_Qty'])
            
            if transfer_qty > 0:
                # 獲取轉出店鋪的原始庫存信息
                transfer_site_data = original_df[
                    (original_df['Article'] == transfer['Article']) & 
                    (original_df['OM'] == transfer['OM']) & 
                    (original_df['Site'] == transfer['Site'])
                ].iloc[0]
                
                original_stock = transfer_site_data['SaSa Net Stock']
                safety_stock = transfer_site_data['Safety Stock']
                
                # 優化：如果調貨數量只有1件便需要調高成2件，只要調高後被轉出店鋪調貨後的存貨不少於Safety stock便可
                if transfer_qty == 1:
                    # 檢查是否可以調高到2件
                    if original_stock - 2 >= safety_stock and transfer['Available_Qty'] >= 2:
                        transfer_qty = 2
                
                after_transfer_stock = original_stock - transfer_qty
                
                recommendations.append({
                    'Article': transfer['Article'],
                    'OM': transfer['OM'],
                    'Transfer_Site': transfer['Site'],
                    'Receive_Site': receive['Site'],
                    'Transfer_Qty': transfer_qty,
                    'Transfer_Type': transfer['Type'],
                    'Receive_Type': receive['Type'],
                    'Original_Stock': original_stock,
                    'After_Transfer_Stock': after_transfer_stock,
                    'Safety_Stock': safety_stock,
                    'Notes': f"{transfer['Type']} -> {receive['Type']}"
                })
                
                # 更新剩餘數量
                transfer['Available_Qty'] -= transfer_qty
                receive['Need_Qty'] -= transfer_qty
    
    return recommendations

def generate_transfer_recommendations(df):
    """生成調貨建議"""
    all_recommendations = []
    
    # 按Article和OM分組處理
    grouped = df.groupby(['Article', 'OM'])
    
    for (article, om), group in grouped:
        # 識別轉出和接收候選
        transfer_candidates = identify_transfer_candidates(group)
        receive_candidates = identify_receive_candidates(group)
        
        # 匹配並生成建議
        recommendations = match_transfer_receive(transfer_candidates, receive_candidates, df)
        all_recommendations.extend(recommendations)
    
    return pd.DataFrame(all_recommendations)

def generate_summary_statistics(recommendations_df, original_df):
    """生成統計摘要"""
    if recommendations_df.empty:
        return {
            'total_recommendations': 0,
            'total_transfer_qty': 0,
            'by_article': pd.DataFrame(),
            'by_om': pd.DataFrame(),
            'transfer_type_dist': pd.DataFrame(),
            'receive_type_dist': pd.DataFrame()
        }
    
    # 基本統計
    total_recommendations = len(recommendations_df)
    total_transfer_qty = recommendations_df['Transfer_Qty'].sum()
    
    # 按Article統計
    by_article = recommendations_df.groupby('Article').agg({
        'Transfer_Qty': ['sum', 'count'],
        'OM': 'nunique'
    }).round(2)
    by_article.columns = ['總調貨件數', '涉及行數', '涉及OM數量']
    
    # 按OM統計
    by_om = recommendations_df.groupby('OM').agg({
        'Transfer_Qty': ['sum', 'count'],
        'Article': 'nunique'
    }).round(2)
    by_om.columns = ['總調貨件數', '涉及行數', '涉及Article數量']
    
    # 轉出類型分布
    transfer_type_dist = recommendations_df.groupby('Transfer_Type').agg({
        'Transfer_Qty': 'sum',
        'Article': 'count'
    })
    transfer_type_dist.columns = ['總件數', '涉及行數']
    
    # 接收類型分布
    receive_type_dist = recommendations_df.groupby('Receive_Type').agg({
        'Transfer_Qty': 'sum',
        'Article': 'count'
    })
    receive_type_dist.columns = ['總件數', '涉及行數']
    
    return {
        'total_recommendations': total_recommendations,
        'total_transfer_qty': total_transfer_qty,
        'by_article': by_article,
        'by_om': by_om,
        'transfer_type_dist': transfer_type_dist,
        'receive_type_dist': receive_type_dist
    }

def create_excel_output(recommendations_df, summary_stats, original_df):
    """創建Excel輸出"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 工作表1：調貨建議
        if not recommendations_df.empty:
            # 合併產品描述
            merged_df = recommendations_df.merge(
                original_df[['Article', 'Article Description']].drop_duplicates(),
                on='Article',
                how='left'
            )
            
            # 重新排列欄位
            output_columns = ['Article', 'Article Description', 'OM', 'Transfer_Site', 
                            'Receive_Site', 'Transfer_Qty', 'Original_Stock', 
                            'After_Transfer_Stock', 'Safety_Stock', 'Notes']
            final_df = merged_df[output_columns].rename(columns={
                'Article Description': 'Product Desc',
                'Transfer_Site': 'Transfer Site',
                'Receive_Site': 'Receive Site',
                'Transfer_Qty': 'Transfer Qty',
                'Original_Stock': 'Original Stock',
                'After_Transfer_Stock': 'After Transfer Stock',
                'Safety_Stock': 'Safety Stock'
            })
            
            final_df.to_excel(writer, sheet_name='調貨建議', index=False)
        else:
            # 空結果
            empty_df = pd.DataFrame(columns=['Article', 'Product Desc', 'OM', 'Transfer Site', 
                                           'Receive Site', 'Transfer Qty', 'Original Stock',
                                           'After Transfer Stock', 'Safety Stock', 'Notes'])
            empty_df.to_excel(writer, sheet_name='調貨建議', index=False)
        
        # 工作表2：統計摘要 - 修復：直接在同一個writer中創建
        start_row = 0
        
        # KPI概覽
        kpi_df = pd.DataFrame({
            'KPI': ['總調貨建議數量', '總調貨件數'],
            '數值': [summary_stats['total_recommendations'], summary_stats['total_transfer_qty']]
        })
        kpi_df.to_excel(writer, sheet_name='統計摘要', startrow=start_row, index=False)
        start_row += len(kpi_df) + 3
        
        # 各統計表
        tables = [
            ('按Article統計', summary_stats['by_article']),
            ('按OM統計', summary_stats['by_om']),
            ('轉出類型分布', summary_stats['transfer_type_dist']),
            ('接收類型分布', summary_stats['receive_type_dist'])
        ]
        
        for title, table in tables:
            if not table.empty:
                # 寫入標題
                title_df = pd.DataFrame([[title]], columns=[''])
                title_df.to_excel(writer, sheet_name='統計摘要', 
                                startrow=start_row, index=False, header=False)
                start_row += 2
                
                # 寫入表格
                table.to_excel(writer, sheet_name='統計摘要', startrow=start_row)
                start_row += len(table) + 3
    
    output.seek(0)
    return output

def main():
    st.set_page_config(
        page_title="調貨建議生成系統",
        page_icon="📦",
        layout="wide"
    )
    
    st.title("📦 調貨建議生成系統")
    st.markdown("---")
    
    # 側邊欄信息
    st.sidebar.header("系統信息")
    st.sidebar.info("""
    **優化特點：**
    - ✅ RF類型過剩轉出限制（20%上限，最少2件）
    - ✅ 智能優先級匹配
    - ✅ 完整統計分析
    - ✅ Excel格式輸出
    """)
    
    # 文件上傳
    st.header("📁 數據上傳")
    
    uploaded_file = st.file_uploader(
        "選擇Excel文件", 
        type=['xlsx', 'xls'],
        help="支持.xlsx和.xls格式，請上傳包含庫存和銷售數據的Excel文件"
    )
    
    if uploaded_file is None:
        st.info("📤 請上傳Excel文件以開始分析")
        st.markdown("""
        **所需數據欄位：**
        - Article (產品編號)
        - RP Type (轉出類型：ND或RF)
        - Site (店鋪編號)
        - OM (營運管理單位)
        - SaSa Net Stock (現有庫存)
        - Pending Received (在途訂單)
        - Safety Stock (安全庫存)
        - Last Month Sold Qty (上月銷量)
        - MTD Sold Qty (本月至今銷量)
        """)
    
    if uploaded_file is not None:
        # 加載數據
        with st.spinner("🔄 正在加載數據..."):
            df = load_and_preprocess_data(uploaded_file)
        
        if df is not None:
            st.success(f"✅ 數據加載成功! 共 {len(df)} 行，{len(df.columns)} 列")
            
            # 數據預覽
            st.header("👀 數據預覽")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("基本統計")
                st.write(f"**總記錄數:** {len(df):,}")
                st.write(f"**產品數量:** {df['Article'].nunique():,}")
                st.write(f"**店鋪數量:** {df['Site'].nunique():,}")
                st.write(f"**OM數量:** {df['OM'].nunique():,}")
            
            with col2:
                st.subheader("RP Type分布")
                rp_type_dist = df['RP Type'].value_counts()
                st.dataframe(rp_type_dist)
            
            # 顯示前幾行
            st.subheader("數據樣本")
            display_columns = ['Article', 'RP Type', 'Site', 'OM', 'SaSa Net Stock', 
                             'Pending Received', 'Safety Stock', 'Last Month Sold Qty', 'MTD Sold Qty']
            st.dataframe(df[display_columns].head(10))
            
            # 生成調貨建議
            st.header("⚙️ 生成調貨建議")
            
            if st.button("🚀 開始分析", type="primary"):
                with st.spinner("🔄 正在分析數據並生成調貨建議..."):
                    # 生成建議
                    recommendations_df = generate_transfer_recommendations(df)
                    
                    # 生成統計
                    summary_stats = generate_summary_statistics(recommendations_df, df)
                
                st.success("✅ 調貨建議生成完成!")
                
                # 顯示結果
                st.header("📊 分析結果")
                
                # KPI概覽
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("總建議數", summary_stats['total_recommendations'])
                
                with col2:
                    st.metric("總調貨件數", summary_stats['total_transfer_qty'])
                
                with col3:
                    involved_articles = len(summary_stats['by_article']) if not summary_stats['by_article'].empty else 0
                    st.metric("涉及產品數", involved_articles)
                
                with col4:
                    involved_oms = len(summary_stats['by_om']) if not summary_stats['by_om'].empty else 0
                    st.metric("涉及OM數", involved_oms)
                
                # 調貨建議表
                st.subheader("🔄 調貨建議明細")
                if not recommendations_df.empty:
                    # 添加產品描述
                    display_df = recommendations_df.merge(
                        df[['Article', 'Article Description']].drop_duplicates(),
                        on='Article',
                        how='left'
                    )
                    
                    # 重新排列和重命名欄位
                    display_columns = {
                        'Article': '產品編號',
                        'Article Description': '產品描述',
                        'OM': 'OM',
                        'Transfer_Site': '轉出店鋪',
                        'Receive_Site': '接收店鋪',
                        'Transfer_Qty': '調貨數量',
                        'Original_Stock': '轉出店鋪原有數量',
                        'After_Transfer_Stock': '轉出後數量',
                        'Safety_Stock': 'Safety數量',
                        'Transfer_Type': '轉出類型',
                        'Receive_Type': '接收類型',
                        'Notes': '備註'
                    }
                    
                    final_display = display_df.rename(columns=display_columns)
                    st.dataframe(final_display, use_container_width=True)
                else:
                    st.info("📝 根據當前數據和業務規則，暫無調貨建議。")
                
                # 統計分析
                if summary_stats['total_recommendations'] > 0:
                    st.subheader("📈 統計分析")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**按產品統計**")
                        if not summary_stats['by_article'].empty:
                            st.dataframe(summary_stats['by_article'])
                        
                        st.write("**轉出類型分布**")
                        if not summary_stats['transfer_type_dist'].empty:
                            st.dataframe(summary_stats['transfer_type_dist'])
                    
                    with col2:
                        st.write("**按OM統計**")
                        if not summary_stats['by_om'].empty:
                            st.dataframe(summary_stats['by_om'])
                        
                        st.write("**接收類型分布**")
                        if not summary_stats['receive_type_dist'].empty:
                            st.dataframe(summary_stats['receive_type_dist'])
                
                # 生成Excel文件
                st.header("💾 導出結果")
                
                with st.spinner("🔄 正在生成Excel文件..."):
                    excel_output = create_excel_output(recommendations_df, summary_stats, df)
                
                # 下載按鈕
                current_date = datetime.now().strftime("%Y%m%d")
                filename = f"調貨建議_{current_date}.xlsx"
                
                st.download_button(
                    label="📥 下載調貨建議Excel",
                    data=excel_output,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.success(f"✅ Excel文件已準備就緒: {filename}")
    
    # 底部信息
    st.markdown("---")
    st.markdown("*由 MiniMax Agent 開發 | © 2025*")

if __name__ == "__main__":
    main()
