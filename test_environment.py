#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
調貨建議生成系統 v1.5 - 環境測試腳本
測試系統依賴和功能是否正常
"""

import sys
import importlib

def test_python_version():
    """測試 Python 版本"""
    print("🐍 測試 Python 版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - 版本符合要求")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - 需要 Python 3.8+")
        return False

def test_package(package_name, import_name=None):
    """測試單個包是否可用"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'Unknown')
        print(f"   ✅ {package_name} {version}")
        return True
    except ImportError as e:
        print(f"   ❌ {package_name} - 未安裝或導入失敗: {e}")
        return False

def test_dependencies():
    """測試所有依賴包"""
    print("\n📦 測試依賴包...")
    
    packages = [
        ('Streamlit', 'streamlit'),
        ('Pandas', 'pandas'),
        ('NumPy', 'numpy'),
        ('OpenPyXL', 'openpyxl'),
        ('Matplotlib', 'matplotlib'),
        ('Seaborn', 'seaborn')
    ]
    
    all_ok = True
    for package_name, import_name in packages:
        if not test_package(package_name, import_name):
            all_ok = False
    
    return all_ok

def test_functionality():
    """測試基本功能"""
    print("\n🔧 測試基本功能...")
    
    try:
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        
        # 測試基本數據處理
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['x', 'y', 'z']
        })
        
        # 測試圖表生成
        plt.figure(figsize=(5, 3))
        plt.bar(['A', 'B', 'C'], [1, 2, 3])
        plt.title('Test Chart')
        plt.close()
        
        print("   ✅ 數據處理功能正常")
        print("   ✅ 圖表生成功能正常")
        return True
        
    except Exception as e:
        print(f"   ❌ 功能測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 50)
    print("  調貨建議生成系統 v1.5 - 環境測試")
    print("  由 Ricky 開發 | © 2025")
    print("=" * 50)
    
    # 執行所有測試
    tests = [
        test_python_version(),
        test_dependencies(),
        test_functionality()
    ]
    
    # 結果總結
    print("\n" + "=" * 50)
    if all(tests):
        print("🎉 所有測試通過！系統環境正常")
        print("💡 您可以運行以下命令啟動系統:")
        print("   Windows: run.bat")
        print("   Linux/Mac: bash run.sh")
        print("   手動啟動: streamlit run app.py")
    else:
        print("⚠️  部分測試失敗，請先安裝缺失的依賴:")
        print("   pip install -r requirements.txt")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
