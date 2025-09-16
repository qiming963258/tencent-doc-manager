#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断8093系统问题
找出为什么修复没有生效
"""

import os
import sys
import hashlib
from pathlib import Path

def check_file_content():
    """检查文件内容"""
    
    print("\n" + "="*60)
    print("8093系统诊断")
    print("="*60)
    
    # 1. 检查主文件
    main_file = Path('/root/projects/tencent-doc-manager/production_integrated_test_system_8093.py')
    if not main_file.exists():
        print("❌ 主文件不存在")
        return
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    print(f"\n1. 文件信息:")
    print(f"   文件路径: {main_file}")
    print(f"   文件大小: {len(content)} 字节")
    print(f"   文件MD5: {hashlib.md5(content.encode()).hexdigest()}")
    print(f"   修改时间: {os.path.getmtime(main_file)}")
    
    # 2. 检查关键代码
    print(f"\n2. 检查关键代码:")
    
    # 检查是否有analyze_changes（错误的）
    if 'analyze_changes' in content:
        print("   ❌ 发现错误调用: analyze_changes")
        # 找出位置
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'analyze_changes' in line:
                print(f"      第{i}行: {line.strip()}")
    else:
        print("   ✅ 未发现analyze_changes调用")
    
    # 检查是否有analyze_modifications（正确的）
    if 'analyze_modifications' in content:
        print("   ✅ 发现正确调用: analyze_modifications")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'analyze_modifications' in line:
                print(f"      第{i}行: {line.strip()}")
    else:
        print("   ❌ 未发现analyze_modifications调用")
    
    # 检查是否有降级代码
    if '基础打分' in content or '使用基础打分' in content:
        print("   ❌ 发现降级代码: 基础打分")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if '基础打分' in line:
                print(f"      第{i}行: {line.strip()}")
    else:
        print("   ✅ 未发现降级代码")
    
    # 检查上传模块导入
    print(f"\n3. 检查上传模块导入:")
    if 'tencent_doc_uploader_ultimate' in content:
        print("   ✅ 使用终极版上传器")
    elif 'tencent_doc_uploader_fixed' in content:
        print("   ⚠️ 使用修复版上传器")
    elif 'tencent_doc_uploader' in content:
        print("   ❌ 使用原版上传器")
    else:
        print("   ❌ 未找到上传器导入")
    
    # 4. 检查L2语义分析器
    print(f"\n4. 检查L2语义分析器:")
    l2_file = Path('/root/projects/tencent-doc-manager/production/core_modules/l2_semantic_analysis_two_layer.py')
    if l2_file.exists():
        with open(l2_file, 'r') as f:
            l2_content = f.read()
        
        # 统计方法
        methods = []
        for line in l2_content.split('\n'):
            if 'def analyze' in line:
                method_name = line.strip().split('(')[0].replace('def ', '')
                methods.append(method_name)
        
        print(f"   L2SemanticAnalyzer的analyze方法:")
        for method in methods:
            print(f"   - {method}")
    
    # 5. 检查正在运行的进程
    print(f"\n5. 检查运行中的8093进程:")
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    processes = result.stdout.split('\n')
    for proc in processes:
        if '8093' in proc and 'python' in proc:
            print(f"   {proc[:120]}...")
    
    # 6. 检查端口占用
    print(f"\n6. 检查8093端口:")
    result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    for line in lines:
        if '8093' in line:
            print(f"   {line}")
    
    print("\n" + "="*60)
    print("诊断完成")
    print("="*60)

def test_modules():
    """测试模块导入"""
    print("\n7. 测试模块导入:")
    
    # 测试L2语义分析器
    try:
        from production.core_modules.l2_semantic_analysis_two_layer import L2SemanticAnalyzer
        analyzer = L2SemanticAnalyzer()
        
        # 检查方法
        if hasattr(analyzer, 'analyze_modifications'):
            print("   ✅ L2SemanticAnalyzer.analyze_modifications 存在")
        else:
            print("   ❌ L2SemanticAnalyzer.analyze_modifications 不存在")
        
        if hasattr(analyzer, 'analyze_changes'):
            print("   ⚠️ L2SemanticAnalyzer.analyze_changes 存在（不应该存在）")
        else:
            print("   ✅ L2SemanticAnalyzer.analyze_changes 不存在（正确）")
        
        # 测试调用
        test_data = [{
            'column_name': 'test',
            'old_value': '1',
            'new_value': '2',
            'row': 1,
            'cell': 'A1'
        }]
        
        try:
            result = analyzer.analyze_modifications(test_data)
            print("   ✅ analyze_modifications 调用成功")
        except Exception as e:
            print(f"   ❌ analyze_modifications 调用失败: {e}")
            
    except Exception as e:
        print(f"   ❌ 无法导入L2SemanticAnalyzer: {e}")
    
    # 测试打分生成器
    try:
        from intelligent_excel_marker import DetailedScoreGenerator
        print("   ✅ DetailedScoreGenerator 导入成功")
        
        # 检查CSV支持
        import inspect
        source = inspect.getsource(DetailedScoreGenerator.generate_score_json)
        if 'pandas' in source:
            print("   ⚠️ 打分生成器依赖pandas")
        elif 'csv' in source:
            print("   ✅ 打分生成器使用csv模块")
        else:
            print("   ❓ 打分生成器CSV处理方式未知")
            
    except Exception as e:
        print(f"   ❌ 无法导入DetailedScoreGenerator: {e}")

if __name__ == "__main__":
    check_file_content()
    test_modules()