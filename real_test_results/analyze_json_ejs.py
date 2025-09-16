#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析JSON格式的EJS数据
URL3和URL4返回的是JSON开头的EJS，可能包含可解析数据
"""

import json
import requests
from datetime import datetime
from pathlib import Path

def load_cookies():
    """加载cookies"""
    cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
    with open(cookie_file, 'r', encoding='utf-8') as f:
        return json.load(f)["current_cookies"]

def parse_json_ejs(content):
    """解析JSON格式的EJS"""
    lines = content.split('\n')
    
    if len(lines) >= 3 and lines[0] == 'head' and lines[1] == 'json':
        try:
            json_length = int(lines[2])
            json_content = '\n'.join(lines[3:])
            
            # 提取指定长度的JSON
            json_str = json_content[:json_length]
            
            # 解析JSON
            data = json.loads(json_str)
            return data
            
        except (ValueError, json.JSONDecodeError) as e:
            print(f"JSON解析失败: {e}")
            return None
    
    return None

def extract_spreadsheet_data(json_data):
    """从JSON数据中提取表格数据"""
    extracted_data = {}
    
    # 查找可能的数据字段
    def search_data(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                
                # 寻找可能的表格数据字段
                if key in ['workbook', 'sheet', 'cells', 'data', 'rows', 'content']:
                    extracted_data[new_path] = value
                
                # 递归搜索
                if isinstance(value, (dict, list)) and len(str(value)) < 10000:  # 避免过大数据
                    search_data(value, new_path)
                    
        elif isinstance(obj, list) and len(obj) > 0:
            # 检查列表中的数据
            for i, item in enumerate(obj[:5]):  # 只检查前5个
                search_data(item, f"{path}[{i}]")
    
    search_data(json_data)
    return extracted_data

def test_json_ejs_parsing():
    """测试JSON EJS解析"""
    cookie_str = load_cookies()
    doc_id = "DWEVjZndkR2xVSWJN"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://docs.qq.com/sheet/{doc_id}',
        'Cookie': cookie_str
    }
    
    # 测试两个JSON格式的URL
    test_urls = [
        f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=csv",
        f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=xlsx",
    ]
    
    results = []
    
    for i, url in enumerate(test_urls):
        print(f"\n分析URL {i+1}: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # 解析JSON EJS
                json_data = parse_json_ejs(response.text)
                
                if json_data:
                    print("  ✅ JSON解析成功")
                    
                    # 提取表格数据
                    extracted = extract_spreadsheet_data(json_data)
                    
                    result = {
                        'url': url,
                        'json_keys': list(json_data.keys())[:20],  # 前20个键
                        'extracted_fields': list(extracted.keys()),
                        'has_workbook': 'workbook' in str(json_data),
                        'has_cells': 'cells' in str(json_data),
                        'has_rows': 'rows' in str(json_data)
                    }
                    
                    # 保存原始数据
                    timestamp = datetime.now().strftime('%H%M%S')
                    json_file = f"/root/projects/tencent-doc-manager/real_test_results/json_data_{i+1}_{timestamp}.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"  📁 JSON数据已保存: {Path(json_file).name}")
                    print(f"  🔑 主要字段: {result['json_keys'][:5]}")
                    
                    if extracted:
                        print(f"  📊 找到数据字段: {list(extracted.keys())[:3]}")
                    
                    results.append(result)
                else:
                    print("  ❌ 不是有效的JSON EJS格式")
            else:
                print(f"  ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    return results

def main():
    print("🔍 分析JSON格式的EJS数据")
    print("="*50)
    
    results = test_json_ejs_parsing()
    
    if results:
        print(f"\n✅ 成功解析 {len(results)} 个JSON EJS文件")
        print("这可能是获取真实数据的新路径！")
    else:
        print("\n😞 未能解析JSON EJS数据")

if __name__ == "__main__":
    main()