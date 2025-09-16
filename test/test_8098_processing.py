#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试8098系统处理新的文件名格式
"""

import requests
import json
import time

def test_8098_processing():
    """测试8098处理新文件名格式"""
    
    print("="*60)
    print("测试8098系统处理新的文件名格式")
    print("="*60)
    
    # 文件路径
    file_path = "/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json"
    
    print(f"\n📁 测试文件: {file_path}")
    
    # 测试1: 读取文件
    print("\n步骤1: 读取文件内容")
    response = requests.post(
        "http://localhost:8098/api/read_file",
        json={"file_path": file_path}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print("✅ 文件读取成功")
            modified_columns = data['content'].get('modified_columns', {})
            print(f"   找到 {len(modified_columns)} 个修改列:")
            for col_code, col_name in modified_columns.items():
                print(f"   - {col_code}: {col_name}")
        else:
            print(f"❌ 文件读取失败: {data.get('error')}")
            return
    else:
        print(f"❌ API调用失败: HTTP {response.status_code}")
        return
    
    # 测试2: 处理标准化
    print("\n步骤2: 执行AI标准化")
    
    # 从文件读取结果中提取需要的数据
    file_content = data['content']
    modified_columns = file_content.get('modified_columns', {})
    
    if not modified_columns:
        print("⚠️ 没有找到修改列，无法进行标准化")
        return
    
    # 调用标准化API (使用analyze端点)
    columns_list = list(modified_columns.values())
    response = requests.post(
        "http://localhost:8098/api/analyze",
        json={
            "columns": columns_list,
            "csv_path": file_path,
            "use_numbering": True,
            "filter_modified": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n调试: 完整响应 = {json.dumps(result, ensure_ascii=False, indent=2)[:500]}...")
        if result.get('success'):
            print("\n✅ AI标准化成功")
            
            # 获取返回的数据
            data = result.get('data', {})
            output_file = data.get('output_file', '未知')
            standardized = data.get('standardized', {})
            
            print(f"   输出文件: {output_file}")
            
            # 显示标准化结果
            if standardized:
                print("\n📊 标准化结果:")
                for i, col_name in enumerate(columns_list):
                    std_name = standardized.get(str(i+1), {}).get('standardized', col_name)
                    confidence = standardized.get(str(i+1), {}).get('confidence', 0)
                    print(f"   {i+1}. {col_name} → {std_name} (置信度: {confidence:.2f})")
            else:
                print("   未返回标准化结果")
        else:
            print(f"❌ 标准化失败: {result.get('error')}")
    else:
        print(f"❌ 标准化API调用失败: HTTP {response.status_code}")
        print(f"   响应: {response.text[:200]}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    test_8098_processing()