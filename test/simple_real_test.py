#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单真实测试 - 验证下载是否真的可用
"""

import os
import json
import requests
import time
from datetime import datetime

def load_cookie():
    """加载Cookie"""
    with open('/root/projects/tencent-doc-manager/config/cookies_new.json', 'r') as f:
        cookie_data = json.load(f)
    return cookie_data['current_cookies']

def test_direct_download():
    """测试直接下载"""
    print("="*60)
    print("腾讯文档下载 - 简单真实测试")
    print("="*60)
    
    # 配置
    doc_id = "DWEVjZndkR2xVSWJN"  # 测试文档
    cookie_str = load_cookie()
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': cookie_str,
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': f'https://docs.qq.com/sheet/{doc_id}'
    }
    
    # 测试不同的下载URL
    test_urls = [
        {
            'name': 'CSV格式',
            'url': f'https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_csv'
        },
        {
            'name': 'Excel格式',  
            'url': f'https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx'
        }
    ]
    
    results = []
    
    for test in test_urls:
        print(f"\n测试: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            # 发送请求
            response = requests.get(test['url'], headers=headers, timeout=30)
            
            print(f"状态码: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"文件大小: {len(response.content)} bytes")
            
            if response.status_code == 200:
                # 检查文件头
                header = response.content[:100]
                
                # 检查是否是真正的Excel
                if header[:4] == b'PK\x03\x04':
                    print("✅ 这是真正的Excel文件！（ZIP格式）")
                    file_type = "real_excel"
                # 检查是否是CSV
                elif b',' in header or b'\t' in header or header[:3] == b'\xef\xbb\xbf':
                    print("✅ 这看起来是CSV文件")
                    file_type = "csv"
                # 检查是否是HTML
                elif b'<html' in header.lower() or b'<!doctype' in header.lower():
                    print("❌ 这是HTML错误页面")
                    file_type = "html_error"
                # 检查是否是JSON
                elif header[0:1] == b'{':
                    print("⚠️ 这是JSON格式（可能是EJS）")
                    file_type = "json_ejs"
                    # 尝试解析
                    try:
                        data = json.loads(response.text)
                        print(f"JSON keys: {list(data.keys())[:5]}")
                    except:
                        pass
                else:
                    print("❓ 未知格式")
                    file_type = "unknown"
                    print(f"前50字节: {header[:50]}")
                
                # 保存文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"test_{doc_id}_{test['name'].replace(' ', '_')}_{timestamp}.{'xlsx' if 'xlsx' in test['url'] else 'csv'}"
                filepath = f"/root/projects/tencent-doc-manager/{filename}"
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                    
                print(f"已保存到: {filepath}")
                
                results.append({
                    'name': test['name'],
                    'success': True,
                    'file_type': file_type,
                    'file_size': len(response.content),
                    'file_path': filepath
                })
                
            else:
                print(f"❌ 下载失败: {response.status_code}")
                results.append({
                    'name': test['name'],
                    'success': False,
                    'status_code': response.status_code
                })
                
        except Exception as e:
            print(f"❌ 错误: {e}")
            results.append({
                'name': test['name'],
                'success': False,
                'error': str(e)
            })
            
        time.sleep(2)  # 请求间隔
    
    # 总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    for result in results:
        if result['success']:
            print(f"✅ {result['name']}: {result['file_type']} ({result['file_size']} bytes)")
            if result.get('file_path'):
                # 尝试用Excel工具打开验证
                if 'real_excel' in result.get('file_type', ''):
                    print(f"   可以用Excel打开: {result['file_path']}")
        else:
            print(f"❌ {result['name']}: 失败")
    
    # 保存结果
    result_file = f"simple_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n结果已保存到: {result_file}")
    
    return results

if __name__ == "__main__":
    results = test_direct_download()
    
    # 判断是否成功
    success_count = sum(1 for r in results if r.get('success'))
    if success_count > 0:
        print(f"\n🎉 测试成功！{success_count}/{len(results)} 个URL可以下载")
    else:
        print(f"\n😞 测试失败！所有URL都无法下载")