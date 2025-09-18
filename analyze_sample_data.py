import pandas as pd
import numpy as np

def analyze_excel_file():
    try:
        # Read the Excel file
        file_path = "/workspace/user_input_files/ELE_08Sep2025 - Dummy.XLSX"
        df = pd.read_excel(file_path)
        
        print("=== Excel文件結構分析 ===")
        print(f"總行數: {len(df)}")
        print(f"總列數: {len(df.columns)}")
        print("\n=== 欄位列表 ===")
        for i, col in enumerate(df.columns):
            print(f"{i+1}. {col}")
        
        print("\n=== 數據類型 ===")
        print(df.dtypes)
        
        print("\n=== 前5行樣本數據 ===")
        print(df.head())
        
        print("\n=== 基本統計信息 ===")
        print(df.describe())
        
        print("\n=== 空值統計 ===")
        print(df.isnull().sum())
        
        # Check for specific columns mentioned in requirements
        required_columns = [
            'Article', 'Article Description', 'RP Type', 'Site', 'OM', 
            'MOQ', 'SaSa Net Stock', 'Pending Received', 'Safety Stock', 
            'Last Month Sold Qty', 'MTD Sold Qty'
        ]
        
        print("\n=== 必需欄位檢查 ===")
        for col in required_columns:
            if col in df.columns:
                print(f"✅ {col} - 存在")
            else:
                print(f"❌ {col} - 缺失")
        
        # Check RP Type values
        if 'RP Type' in df.columns:
            print(f"\n=== RP Type值分佈 ===")
            print(df['RP Type'].value_counts())
        
        return df
        
    except Exception as e:
        print(f"讀取文件時出錯: {e}")
        return None

if __name__ == "__main__":
    df = analyze_excel_file()
