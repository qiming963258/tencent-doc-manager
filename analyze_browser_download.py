#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析浏览器真实下载请求的参数和方式
"""

import requests
import json
import time
from urllib.parse import parse_qs, urlparse

def load_cookie():
    """加载Cookie"""
    with open('/root/projects/tencent-doc-manager/config/cookies_new.json', 'r') as f:
        cookie_data = json.load(f)
    return cookie_data['current_cookies']

def test_browser_like_requests():
    """测试更接近浏览器行为的请求"""
    doc_id = "DWEVjZndkR2xVSWJN"
    cookie_str = load_cookie()
    
    print("="*60)
    print("分析浏览器真实下载行为")
    print("="*60)
    
    # 首先访问文档页面获取可能的token/参数
    print("\n1. 访问文档页面获取上下文...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cookie': cookie_str,
    })
    
    try:
        # 访问文档页面
        doc_url = f"https://docs.qq.com/sheet/{doc_id}"
        page_response = session.get(doc_url, timeout=10)
        
        if page_response.status_code == 200:
            print("✅ 成功访问文档页面")
            
            # 查找可能的导出相关参数
            page_content = page_response.text
            
            # 查找可能的token或参数
            import re
            
            # 查找CSRF token
            csrf_matches = re.findall(r'csrf["\']?\s*[:=]\s*["\']([^"\']+)', page_content, re.IGNORECASE)
            if csrf_matches:
                print(f"发现CSRF token: {csrf_matches[0][:20]}...")
            
            # 查找export相关的URL
            export_matches = re.findall(r'["\']([^"\']*export[^"\']*)["\']', page_content)
            if export_matches:
                print("发现可能的导出URL:")
                for url in export_matches[:5]:
                    print(f"  {url}")
            
            # 查找JavaScript中的配置
            config_matches = re.findall(r'window\.__[A-Z_]+__\s*=\s*({.*?});', page_content, re.DOTALL)
            if config_matches:
                print("发现窗口配置对象")
                for config in config_matches[:2]:
                    try:
                        config_data = json.loads(config)
                        print(f"  配置keys: {list(config_data.keys())[:5]}")
                    except:
                        print(f"  配置预览: {config[:100]}...")
        
        # 2. 尝试模拟浏览器的完整导出流程
        print("\n2. 测试完整的导出流程...")
        
        test_scenarios = [
            {
                "name": "标准浏览器请求 + Referer",
                "method": "GET",
                "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx",
                "headers": {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Referer': f'https://docs.qq.com/sheet/{doc_id}',
                    'Upgrade-Insecure-Requests': '1',
                }
            },
            {
                "name": "XHR请求模拟",
                "method": "GET", 
                "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx",
                "headers": {
                    'Accept': '*/*',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'Referer': f'https://docs.qq.com/sheet/{doc_id}',
                }
            },
            {
                "name": "直接下载触发",
                "method": "GET",
                "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx&download=1",
                "headers": {
                    'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Referer': f'https://docs.qq.com/sheet/{doc_id}',
                    'Cache-Control': 'no-cache',
                }
            },
            {
                "name": "POST请求导出",
                "method": "POST",
                "url": "https://docs.qq.com/dop-api/opendoc",
                "headers": {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': f'https://docs.qq.com/sheet/{doc_id}',
                },
                "data": f"id={doc_id}&type=export_xlsx&format=binary"
            }
        ]
        
        results = []
        
        for scenario in test_scenarios:
            print(f"\n测试: {scenario['name']}")
            
            try:
                session.headers.update(scenario['headers'])
                
                if scenario['method'] == 'POST':
                    response = session.post(scenario['url'], data=scenario.get('data', ''), timeout=15)
                else:
                    response = session.get(scenario['url'], timeout=15)
                
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', 'unknown')
                    content_length = len(response.content)
                    
                    print(f"Content-Type: {content_type}")
                    print(f"大小: {content_length} bytes")
                    
                    # 检查Content-Disposition
                    content_disposition = response.headers.get('Content-Disposition')
                    if content_disposition:
                        print(f"Content-Disposition: {content_disposition}")
                    
                    # 检查文件头
                    header = response.content[:20]
                    
                    if header[:4] == b'PK\x03\x04':
                        print("🎉 成功！获得真正的Excel文件!")
                        
                        filename = f"browser_method_{scenario['name'].replace(' ', '_')}.xlsx"
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        print(f"已保存: {filename}")
                        
                        results.append({
                            'method': scenario['name'],
                            'success': True,
                            'format': 'real_xlsx',
                            'file': filename
                        })
                        
                    elif content_type == 'text/ejs-data' or b'head' in header:
                        print("❌ 仍然返回EJS格式")
                        results.append({
                            'method': scenario['name'],
                            'success': False,
                            'format': 'ejs'
                        })
                        
                    else:
                        print(f"❓ 其他格式: {header}")
                        results.append({
                            'method': scenario['name'],
                            'success': False,
                            'format': 'unknown'
                        })
                else:
                    print(f"❌ 请求失败: {response.status_code}")
                    if response.status_code == 401:
                        print("认证失败 - 可能需要刷新Cookie")
                    
                    results.append({
                        'method': scenario['name'],
                        'success': False,
                        'status_code': response.status_code
                    })
                    
            except Exception as e:
                print(f"❌ 错误: {e}")
                results.append({
                    'method': scenario['name'],
                    'success': False,
                    'error': str(e)
                })
            
            time.sleep(1)
        
        # 总结
        print("\n" + "="*60)
        print("浏览器模拟测试总结")
        print("="*60)
        
        success_count = sum(1 for r in results if r.get('success'))
        
        if success_count > 0:
            print(f"✅ 成功方法数: {success_count}")
            for r in results:
                if r.get('success'):
                    print(f"  - {r['method']}: {r.get('file', 'N/A')}")
        else:
            print("❌ 所有浏览器模拟方法都失败")
            print("\n失败原因分析:")
            for r in results:
                if not r.get('success'):
                    reason = r.get('format', r.get('error', r.get('status_code', 'unknown')))
                    print(f"  - {r['method']}: {reason}")
        
        return results
            
    except Exception as e:
        print(f"访问文档页面失败: {e}")
        return []

def main():
    """主函数"""
    results = test_browser_like_requests()
    
    print("\n" + "="*60)
    print("结论和建议")
    print("="*60)
    
    if any(r.get('success') for r in results):
        print("🎉 找到了获取真实Excel文件的方法！")
    else:
        print("腾讯文档确实强制所有API请求返回EJS格式")
        print("\n最终建议:")
        print("1. 使用我们已经成功的Node.js zlib解压 + protobuf分析")
        print("2. 开发完整的EJS->Excel转换器")
        print("3. 或使用浏览器自动化点击下载按钮")
        print("4. 研究官方API的可能性")

if __name__ == "__main__":
    main()