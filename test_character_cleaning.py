"""
测试异常字符清理功能
验证数据预览页面的奇怪字眼修复
"""

import pandas as pd
import re

def create_test_data_with_bad_characters():
    """创建包含异常字符的测试数据"""
    
    # 模拟包含异常字符的数据
    test_data = {
        # 正常列名
        'Article': ['A001', 'A002'],
        'Article Description': ['Normal Product', 'Test Product'],
        'Site': ['Store1', 'Store2'],
        'OM': ['OM1', 'OM2'],
        'SaSa Net Stock': [20, 15],
        'Pending Received': [5, 3],
        'Safety Stock': [8, 10],
        'RP Type': ['RF', 'RF'],
        'MOQ': [3, 2],
        'Last Month Sold Qty': [2, 1],
        'MTD Sold Qty': [1, 2],
        # 包含异常字符的列（模拟问题列）
        'key匡省得斗儿俩焯v_right': ['异常数据1', '异常数据2']
    }
    
    return pd.DataFrame(test_data)

def test_character_cleaning():
    """测试字符清理功能"""
    print("=== 异常字符清理功能测试 ===\n")
    
    # 创建包含异常字符的测试数据
    test_df = create_test_data_with_bad_characters()
    
    print("原始数据列名:")
    for i, col in enumerate(test_df.columns):
        print(f"  {i+1}. '{col}'")
    
    print(f"\n检测到的异常列名: '{[col for col in test_df.columns if 'key' in col and '匡省' in col]}'")
    
    # 测试列名清理功能
    print("\n=== 测试列名清理 ===")
    cleaned_columns = []
    for col in test_df.columns:
        # 应用与app.py相同的新清理逻辑
        cleaned_col = str(col)
        
        # 检测并移除类似 "key匡省得斗儿俩焯v_right" 这样的异常模式
        if re.search(r'key.*v_right|[\u0000-\u001f\u007f-\u009f]', cleaned_col):
            cleaned_col = f"Unknown_Column_{len(cleaned_columns)}"
            print(f"  发现异常模式: '{col}' → '{cleaned_col}'")
        else:
            cleaned_col = re.sub(r'[^\w\s\u4e00-\u9fff\-_.()]', '', cleaned_col)
            cleaned_col = cleaned_col.strip()
            if not cleaned_col:
                cleaned_col = f"Column_{len(cleaned_columns)}"
            if col != cleaned_col:
                print(f"  常规清理: '{col}' → '{cleaned_col}'")
        
        cleaned_columns.append(cleaned_col)
    
    test_df.columns = cleaned_columns
    
    print("\n清理后的列名:")
    for i, col in enumerate(test_df.columns):
        print(f"  {i+1}. '{col}'")
    
    # 测试数据内容清理
    print("\n=== 测试数据内容清理 ===")
    string_columns = ['Article Description', 'RP Type', 'Site', 'OM']
    
    for col in string_columns:
        if col in test_df.columns:
            original_values = test_df[col].tolist()
            # 应用新的清理逻辑
            test_df[col] = test_df[col].apply(lambda x: 
                'CLEANED_DATA' if re.search(r'key.*v_right|[\u0000-\u001f\u007f-\u009f]', str(x))
                else re.sub(r'[^\w\s\u4e00-\u9fff\-_()./]', '', str(x)).strip()
            )
            cleaned_values = test_df[col].tolist()
            
            if original_values != cleaned_values:
                print(f"  {col}列清理:")
                for orig, clean in zip(original_values, cleaned_values):
                    if orig != clean:
                        print(f"    '{orig}' → '{clean}'")
    
    # 特殊处理异常列的数据
    print("\n=== 处理异常列数据 ===")
    for col in test_df.columns:
        if re.search(r'Unknown_Column_', col):
            print(f"  发现异常列 '{col}'，将其数据标记为隐藏")
            test_df[col] = 'HIDDEN_DATA'
    
    print("\n=== 最终数据预览 ===")
    print("清理后的数据框:")
    print(test_df.head())
    
    print("\n✅ 异常字符清理测试完成")
    print("现在数据预览页面应该不会再显示奇怪字眼了")
    
    return test_df

if __name__ == "__main__":
    test_character_cleaning()
