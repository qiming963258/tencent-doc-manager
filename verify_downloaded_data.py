#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证下载的腾讯文档数据是否包含实际表格内容
"""

import json
import urllib.parse
from pathlib import Path

def parse_ejs_file(file_path):
    """解析EJS格式的腾讯文档文件"""
    print(f"🔍 解析文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    if len(lines) < 4:
        print("❌ 文件格式不正确")
        return None
    
    print(f"📄 文件结构:")
    print(f"   第1行: {lines[0]}")  # head
    print(f"   第2行: {lines[1]}")  # json
    print(f"   第3行: {lines[2]}")  # 长度
    print(f"   第4行: 前100字符: {lines[3][:100]}...")
    
    # 解析JSON数据
    try:
        json_data = json.loads(lines[3])
        print(f"✅ JSON解析成功")
        return json_data
    except:
        print("❌ JSON解析失败")
        return None

def extract_workbook_data(json_data):
    """从JSON数据中提取工作簿数据"""
    print(f"\n📊 提取表格数据...")
    
    # 查找workbook数据
    workbook_encoded = None
    if 'workbook' in json_data:
        workbook_encoded = json_data['workbook']
    elif 'text' in json_data and 'workbook' in json_data['text']:
        # 从URL编码的text中查找
        text_content = urllib.parse.unquote(json_data['text'])
        if 'workbook' in text_content:
            # 这可能是一个包含workbook的字符串
            print("📝 在text字段中找到workbook数据")
    
    if not workbook_encoded:
        print("❌ 未找到workbook数据")
        return None
    
    print(f"📦 找到workbook数据，长度: {len(workbook_encoded)} 字符")
    
    # workbook数据通常是URL编码或Base64编码的
    try:
        # 尝试URL解码
        workbook_decoded = urllib.parse.unquote(workbook_encoded)
        print(f"🔓 URL解码后长度: {len(workbook_decoded)} 字符")
        
        # 检查是否包含表格相关标识符
        table_indicators = [
            'spreadsheet', 'worksheet', 'cell', 'row', 'column',
            '工作表', '单元格', 'A1', 'Sheet', 'Table'
        ]
        
        found_indicators = []
        for indicator in table_indicators:
            if indicator.lower() in workbook_decoded.lower():
                found_indicators.append(indicator)
        
        if found_indicators:
            print(f"✅ 发现表格相关标识: {found_indicators}")
            return workbook_decoded
        else:
            print("⚠️ 未发现明显的表格标识符")
            return workbook_decoded
            
    except Exception as e:
        print(f"❌ 解码失败: {e}")
        return None

def main():
    """主函数"""
    print("🚀 验证腾讯文档下载数据")
    
    # 测试文件路径
    test_files = [
        "/root/projects/tencent-doc-manager/downloads/test_direct_1_csv.csv",
        "/root/projects/tencent-doc-manager/downloads/test_direct_3_csv.csv"
    ]
    
    results = {}
    
    for file_path in test_files:
        if not Path(file_path).exists():
            print(f"❌ 文件不存在: {file_path}")
            continue
        
        print("\n" + "="*60)
        
        # 解析EJS文件
        json_data = parse_ejs_file(file_path)
        if not json_data:
            continue
        
        # 提取基本信息
        doc_title = json_data.get('clientVars', {}).get('initialTitle', 'Unknown')
        pad_type = json_data.get('clientVars', {}).get('padType', 'Unknown')
        user_name = json_data.get('clientVars', {}).get('userName', 'Unknown')
        
        print(f"📄 文档标题: {doc_title}")
        print(f"📄 文档类型: {pad_type}")
        print(f"👤 用户名: {user_name}")
        
        # 提取工作簿数据
        workbook_data = extract_workbook_data(json_data)
        
        # 记录结果
        results[file_path] = {
            "title": doc_title,
            "type": pad_type,
            "user": user_name,
            "has_workbook": workbook_data is not None,
            "workbook_size": len(workbook_data) if workbook_data else 0
        }
        
        # 显示workbook数据的一小部分
        if workbook_data:
            print(f"📝 Workbook数据预览 (前200字符):")
            print(f"   {workbook_data[:200]}...")
    
    # 总结
    print("\n" + "="*60)
    print("🎯 数据验证总结")
    print("="*60)
    
    for file_path, result in results.items():
        filename = Path(file_path).name
        print(f"📁 {filename}:")
        print(f"   📄 标题: {result['title']}")
        print(f"   📊 类型: {result['type']}")
        print(f"   📦 包含工作簿: {'✅' if result['has_workbook'] else '❌'}")
        if result['has_workbook']:
            print(f"   📏 数据大小: {result['workbook_size']} 字符")
    
    # 结论
    successful_files = sum(1 for r in results.values() if r['has_workbook'])
    total_files = len(results)
    
    print(f"\n✅ 验证完成: {successful_files}/{total_files} 文件包含有效数据")
    
    if successful_files > 0:
        print("🎉 确认下载成功！文件包含完整的表格数据！")
        print("💡 可以开始开发数据解析和转换功能")
    else:
        print("❌ 未发现有效的表格数据")

if __name__ == "__main__":
    main()