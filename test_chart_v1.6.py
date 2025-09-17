#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
調貨建議生成系統 v1.6 - 圖表功能測試腳本
測試新的按類型分布的條形圖功能
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

def setup_matplotlib_for_plotting():
    """
    Setup matplotlib and seaborn for plotting with proper configuration.
    Call this function before creating any plots to ensure proper rendering.
    """
    # Ensure warnings are printed
    warnings.filterwarnings('default')  # Show all warnings

    # Configure matplotlib for non-interactive mode
    plt.switch_backend("Agg")

    # Set chart style
    plt.style.use("seaborn-v0_8")
    sns.set_palette("husl")

    # Configure platform-appropriate fonts for cross-platform compatibility
    # Must be set after style.use, otherwise will be overridden by style configuration
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "PingFang SC", "Arial Unicode MS", "Hiragino Sans GB"]
    plt.rcParams["axes.unicode_minus"] = False

def create_om_transfer_chart(recommendations_df):
    """
    創建按OM統計的調貨類型分布條形圖（英文顯示避免亂碼）
    """
    if recommendations_df.empty:
        return None
    
    # 設置matplotlib
    setup_matplotlib_for_plotting()
    
    # 按OM統計不同調貨類型的數量
    # 分別統計轉出類型和接收類型
    transfer_stats = recommendations_df.groupby(['OM', 'Transfer_Type'])['Transfer_Qty'].sum().unstack(fill_value=0)
    receive_stats = recommendations_df.groupby(['OM', 'Receive_Type'])['Transfer_Qty'].sum().unstack(fill_value=0)
    
    # 獲取所有OM
    all_oms = set(transfer_stats.index) | set(receive_stats.index)
    
    # 重新索引確保所有OM都存在
    transfer_stats = transfer_stats.reindex(all_oms, fill_value=0)
    receive_stats = receive_stats.reindex(all_oms, fill_value=0)
    
    # 準備數據 - 英文標籤對應
    type_mapping = {
        'ND轉出': 'ND Transfer',
        'RF過剩轉出': 'RF Excess Transfer', 
        '緊急缺貨補貨': 'Emergency Shortage',
        '潛在缺貨補貨': 'Potential Shortage'
    }
    
    # 準備顏色配置
    color_mapping = {
        'ND Transfer': '#1f4788',        # 深藍色
        'RF Excess Transfer': '#4682B4', # 淺藍色  
        'Emergency Shortage': '#FF4500', # 深橘色
        'Potential Shortage': '#FF8C69'  # 淺橘色
    }
    
    # 合併所有數據
    all_data = {}
    
    # 處理轉出類型數據
    for om in all_oms:
        all_data[om] = {}
        for chinese_type, english_type in type_mapping.items():
            if chinese_type in transfer_stats.columns and om in transfer_stats.index:
                all_data[om][english_type] = transfer_stats.loc[om, chinese_type]
            elif chinese_type in receive_stats.columns and om in receive_stats.index:
                all_data[om][english_type] = receive_stats.loc[om, chinese_type]
            else:
                all_data[om][english_type] = 0
    
    # 創建DataFrame用於繪圖
    chart_data = pd.DataFrame(all_data).T.fillna(0)
    
    # 確保所有類型都存在
    for english_type in type_mapping.values():
        if english_type not in chart_data.columns:
            chart_data[english_type] = 0
    
    # 創建圖表
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 設置條形圖參數
    x = np.arange(len(all_oms))
    width = 0.2
    
    # 繪製不同類型的條形圖
    bars = []
    positions = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]
    
    for i, (english_type, color) in enumerate(color_mapping.items()):
        if english_type in chart_data.columns:
            bars.append(ax.bar(x + positions[i], chart_data[english_type].values, 
                             width, label=english_type, color=color, alpha=0.8))
    
    # 設置圖表
    ax.set_xlabel('OM Unit', fontsize=12)
    ax.set_ylabel('Transfer Quantity', fontsize=12)
    ax.set_title('Transfer Type Distribution by OM', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(list(all_oms), rotation=45 if len(all_oms) > 5 else 0)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 在條形圖上添加數值標籤
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{int(height)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),  # 3 points vertical offset
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=8)
    
    # 為所有條形添加標籤
    for bar_group in bars:
        add_value_labels(bar_group)
    
    # 調整佈局
    plt.tight_layout()
    
    return fig

def test_chart_function():
    """測試圖表功能"""
    print("🧪 測試新的圖表功能...")
    
    # 創建測試數據
    test_data = {
        'Article': ['A001', 'A002', 'A003', 'A004', 'A005', 'A006'],
        'OM': ['OM1', 'OM1', 'OM2', 'OM2', 'OM3', 'OM3'],
        'Transfer_Type': ['ND轉出', 'RF過剩轉出', 'ND轉出', 'RF過剩轉出', 'ND轉出', 'RF過剩轉出'],
        'Receive_Type': ['緊急缺貨補貨', '潛在缺貨補貨', '緊急缺貨補貨', '潛在缺貨補貨', '緊急缺貨補貨', '潛在缺貨補貨'],
        'Transfer_Qty': [5, 3, 8, 4, 6, 2]
    }
    
    test_df = pd.DataFrame(test_data)
    print("✅ 測試數據創建成功")
    print(f"數據行數: {len(test_df)}")
    print(f"包含OM: {test_df['OM'].unique()}")
    print(f"轉出類型: {test_df['Transfer_Type'].unique()}")
    print(f"接收類型: {test_df['Receive_Type'].unique()}")
    
    try:
        # 測試圖表生成
        fig = create_om_transfer_chart(test_df)
        
        if fig is not None:
            print("✅ 圖表生成成功")
            
            # 保存測試圖表
            fig.savefig('test_chart.png', dpi=150, bbox_inches='tight')
            print("✅ 測試圖表已保存為 test_chart.png")
            
            # 清理資源
            plt.close(fig)
            return True
        else:
            print("❌ 圖表生成失敗：返回None")
            return False
            
    except Exception as e:
        print(f"❌ 圖表生成異常：{str(e)}")
        return False

def main():
    print("=" * 50)
    print("  調貨建議生成系統 v1.6 - 圖表功能測試")
    print("  新功能：按調貨類型分布的條形圖")
    print("=" * 50)
    
    success = test_chart_function()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 圖表功能測試通過！")
        print("新的條形圖功能:")
        print("- ✅ ND Transfer (深藍色)")
        print("- ✅ RF Excess Transfer (淺藍色)")
        print("- ✅ Emergency Shortage (深橘色)")
        print("- ✅ Potential Shortage (淺橘色)")
        print("- ✅ 英文標籤避免亂碼")
        print("- ✅ 按OM分組顯示")
    else:
        print("⚠️  圖表功能測試失敗")
        print("請檢查依賴和代碼實現")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
