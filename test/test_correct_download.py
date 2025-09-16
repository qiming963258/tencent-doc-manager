#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试正确的下载方式 - 不使用export_csv参数
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path

def load_cookies():
    """加载cookies"""
    cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
    with open(cookie_file, 'r', encoding='utf-8') as f:
        return json.load(f)["current_cookies"]

def test_different_urls():
    """测试不同的下载URL"""
    cookie_str = load_cookies()
    doc_id = "DWEVjZndkR2xVSWJN"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': f'https://docs.qq.com/sheet/{doc_id}',
        'Cookie': cookie_str
    }
    
    # 测试多种URL
    test_urls = [
        # 标准文档URL
        f"https://docs.qq.com/sheet/{doc_id}",
        # 不同的导出方式
        f"https://docs.qq.com/dop-api/opendoc?id={doc_id}",  # 不带type参数
        f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=csv",  # 不是export_csv
        f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=xlsx",  # 不是export_xlsx
        # API方式
        f"https://docs.qq.com/api/v2/export?id={doc_id}&format=csv",
        f"https://docs.qq.com/api/export?id={doc_id}&format=csv",
    ]
    
    results = {}
    
    for i, url in enumerate(test_urls):
        print(f"\n测试URL {i+1}: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # 分析响应
            result = {
                'status_code': response.status_code,
                'content_type': response.headers.get('Content-Type', ''),
                'content_length': len(response.content),
                'is_csv': False,
                'is_ejs': False,
                'first_100_chars': ''
            }
            
            # 检查内容类型
            content_text = response.text[:500]
            result['first_100_chars'] = content_text[:100]
            
            if content_text.startswith('"') and ',' in content_text:
                result['is_csv'] = True
                print("  ✅ 看起来是CSV格式")
            elif 'attribs' in content_text or 'workbook' in content_text:
                result['is_ejs'] = True
                print("  ❌ 是EJS格式")
            elif response.status_code == 200:
                print("  ⚠️ 未知格式，但状态正常")
            else:
                print(f"  ❌ HTTP {response.status_code}")
            
            results[f'url_{i+1}'] = result
            
            # 如果找到CSV格式，保存文件
            if result['is_csv']:
                timestamp = datetime.now().strftime('%H%M%S')
                output_file = f"/root/projects/tencent-doc-manager/real_test_results/correct_download_{timestamp}.csv"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"  💾 已保存: {Path(output_file).name}")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            results[f'url_{i+1}'] = {'error': str(e)}
        
        time.sleep(1)  # 避免请求过快
    
    return results

def main():
    print("🧪 测试正确的腾讯文档下载方式")
    print("="*60)
    
    results = test_different_urls()
    
    # 保存测试结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f"/root/projects/tencent-doc-manager/real_test_results/download_test_{timestamp}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 测试结果已保存: {Path(result_file).name}")
    
    # 总结
    csv_found = any(r.get('is_csv', False) for r in results.values() if isinstance(r, dict))
    if csv_found:
        print("\n🎉 找到了正确的下载方式！")
    else:
        print("\n😞 未找到直接的CSV下载方式")

if __name__ == "__main__":
    main()