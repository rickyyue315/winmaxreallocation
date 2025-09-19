"""
测试B模式转出类型分类优化
验证根据转出后剩余库存与Safety stock关系来确定转出类型的逻辑
"""

import pandas as pd
import sys
from app import TransferRecommendationSystem

def create_test_data():
    """创建测试数据"""
    test_data = [
        # 测试案例1: 转出后剩余库存 >= Safety stock -> RF过剩转出
        {
            'Article': 'A001',
            'Article Description': 'Test Product A001',
            'Site': 'Store1',
            'OM': 'OM1',
            'SaSa Net Stock': 20,  # 当前库存20
            'Pending Received': 5,   # 待收5，总可用25
            'Safety Stock': 8,       # 安全库存8
            'RP Type': 'RF',
            'MOQ': 3,               # MOQ+1=4，转出量 = min(25-4, max(25*0.5, 2), 20) = min(21, 12, 20) = 12
            'Last Month Sold Qty': 2,  # 剩余库存 = 20-12 = 8 >= 8 (Safety Stock) -> RF过剩转出
            'MTD Sold Qty': 1
        },
        # 测试案例2: 转出后剩余库存 < Safety stock -> RF加强转出
        {
            'Article': 'A002',
            'Article Description': 'Test Product A002',
            'Site': 'Store2',
            'OM': 'OM1',
            'SaSa Net Stock': 15,  # 当前库存15
            'Pending Received': 3,   # 待收3，总可用18
            'Safety Stock': 10,      # 安全库存10
            'RP Type': 'RF',
            'MOQ': 2,               # MOQ+1=3，转出量 = min(18-3, max(18*0.5, 2), 15) = min(15, 9, 15) = 9
            'Last Month Sold Qty': 1,  # 剩余库存 = 15-9 = 6 < 10 (Safety Stock) -> RF加强转出
            'MTD Sold Qty': 2
        },
        # 测试案例3: 边界情况 - 剩余库存正好等于Safety stock
        {
            'Article': 'A003',
            'Article Description': 'Test Product A003',
            'Site': 'Store3',
            'OM': 'OM2',
            'SaSa Net Stock': 18,  # 当前库存18
            'Pending Received': 2,   # 待收2，总可用20
            'Safety Stock': 12,      # 安全库存12
            'RP Type': 'RF',
            'MOQ': 4,               # MOQ+1=5，转出量 = min(20-5, max(20*0.5, 2), 18) = min(15, 10, 18) = 10
            'Last Month Sold Qty': 3,  # 剩余库存 = 18-10 = 8 < 12 (Safety Stock) -> RF加强转出
            'MTD Sold Qty': 1
        },
        # 对比案例: 相同产品在另一店铺的较高销量（确保低销量店铺被识别为转出候选）
        {
            'Article': 'A001',
            'Article Description': 'Test Product A001',
            'Site': 'Store4',
            'OM': 'OM1',
            'SaSa Net Stock': 10,
            'Pending Received': 0,
            'Safety Stock': 5,
            'RP Type': 'RF',
            'MOQ': 2,
            'Last Month Sold Qty': 8,  # 高销量
            'MTD Sold Qty': 4
        },
        {
            'Article': 'A002',
            'Article Description': 'Test Product A002',
            'Site': 'Store5',
            'OM': 'OM1',
            'SaSa Net Stock': 12,
            'Pending Received': 0,
            'Safety Stock': 6,
            'RP Type': 'RF',
            'MOQ': 2,
            'Last Month Sold Qty': 6,  # 高销量
            'MTD Sold Qty': 3
        },
        {
            'Article': 'A003',
            'Article Description': 'Test Product A003',
            'Site': 'Store6',
            'OM': 'OM2',
            'SaSa Net Stock': 15,
            'Pending Received': 0,
            'Safety Stock': 8,
            'RP Type': 'RF',
            'MOQ': 3,
            'Last Month Sold Qty': 7,  # 高销量
            'MTD Sold Qty': 4
        }
    ]
    
    return pd.DataFrame(test_data)

def test_b_mode_transfer_classification():
    """测试B模式的转出类型分类逻辑"""
    print("=== B模式转出类型分类优化测试 ===\n")
    
    # 创建测试数据
    test_df = create_test_data()
    print("测试数据:")
    print(test_df[['Article', 'Site', 'SaSa Net Stock', 'Safety Stock', 'RP Type', 'Last Month Sold Qty']].to_string())
    print("\n")
    
    # 创建系统实例并加载数据
    system = TransferRecommendationSystem()
    system.df = test_df
    
    # 测试B模式转出候选识别
    transfer_candidates = system.identify_transfer_candidates("B")
    
    print("B模式转出候选结果:")
    print("-" * 80)
    
    for i, candidate in enumerate(transfer_candidates, 1):
        print(f"候选 {i}:")
        print(f"  产品: {candidate['Article']}")
        print(f"  店铺: {candidate['Site']}")
        print(f"  原始库存: {candidate['Original_Stock']}")
        print(f"  转出数量: {candidate['Transfer_Qty']}")
        print(f"  剩余库存: {candidate['Remaining_Stock']}")
        print(f"  安全库存: {candidate['Safety_Stock']}")
        print(f"  转出类型: {candidate['Type']}")
        
        # 验证逻辑
        if candidate['Remaining_Stock'] >= candidate['Safety_Stock']:
            expected_type = 'RF過剩轉出'  # 使用繁体中文
        else:
            expected_type = 'RF加強轉出'  # 使用繁体中文
        
        if candidate['Type'] == expected_type:
            print(f"  ✅ 分类正确: 剩余库存({candidate['Remaining_Stock']}) {'>=&' if candidate['Remaining_Stock'] >= candidate['Safety_Stock'] else '<'} 安全库存({candidate['Safety_Stock']})")
        else:
            print(f"  ❌ 分类错误: 期望 {expected_type}, 实际 {candidate['Type']}")
        
        print()
    
    # 统计转出类型分布
    type_counts = {}
    for candidate in transfer_candidates:
        type_counts[candidate['Type']] = type_counts.get(candidate['Type'], 0) + 1
    
    print("转出类型分布统计:")
    print("-" * 40)
    for transfer_type, count in type_counts.items():
        print(f"  {transfer_type}: {count} 笔")
    
    print(f"\n总转出候选数: {len(transfer_candidates)}")
    
    # 验证数据一致性
    print("\n=== 数据一致性验证 ===")
    all_have_remaining_stock = all('Remaining_Stock' in candidate for candidate in transfer_candidates)
    print(f"所有候选都包含剩余库存信息: {'✅' if all_have_remaining_stock else '❌'}")
    
    return transfer_candidates

if __name__ == "__main__":
    test_b_mode_transfer_classification()
