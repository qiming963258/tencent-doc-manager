#!/usr/bin/env python3
"""测试DeepSeekClient导入问题"""

import sys
import os

# 测试1：检查两个DeepSeekClient的不同
print("=== 测试DeepSeekClient导入 ===\n")

# 导入根目录版本
from deepseek_client import DeepSeekClient as RootDeepSeek

# 导入production版本
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/core_modules')
from deepseek_client import DeepSeekClient as ProdDeepSeek

print("1. 根目录DeepSeekClient的方法:")
print("   - 方法列表:", [m for m in dir(RootDeepSeek) if not m.startswith('_')])
print("   - 有chat_completion?", hasattr(RootDeepSeek, 'chat_completion'))
print("   - 有call_api?", hasattr(RootDeepSeek, 'call_api'))

print("\n2. Production DeepSeekClient的方法:")
print("   - 方法列表:", [m for m in dir(ProdDeepSeek) if not m.startswith('_')])
print("   - 有chat_completion?", hasattr(ProdDeepSeek, 'chat_completion'))
print("   - 有call_api?", hasattr(ProdDeepSeek, 'call_api'))

# 测试3：模拟实际使用
print("\n3. 模拟column_standardization_processor_v3使用:")
try:
    # 重置路径，模拟正常导入
    sys.path = [p for p in sys.path if 'production/core_modules' not in p]
    
    # 导入column_standardization_processor_v3
    from column_standardization_processor_v3 import ColumnStandardizationProcessorV3
    
    api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb')
    processor = ColumnStandardizationProcessorV3(api_key)
    
    # 检查processor使用的DeepSeekClient
    client = processor.deepseek_client
    print(f"   - processor使用的client类型: {type(client).__module__}.{type(client).__name__}")
    print(f"   - 有chat_completion方法? {hasattr(client, 'chat_completion')}")
    
except Exception as e:
    print(f"   错误: {e}")

print("\n4. 系统路径检查:")
print("   Python路径中的production模块:", [p for p in sys.path if 'production' in p])