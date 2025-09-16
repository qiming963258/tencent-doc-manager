#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同的下载方法，尝试避免EJS格式
"""

import requests
import json
import time
from pathlib import Path

def load_cookie():
    """加载Cookie"""
    with open('/root/projects/tencent-doc-manager/config/cookies_new.json', 'r') as f:
        cookie_data = json.load(f)
    return cookie_data['current_cookies']

def test_download_methods():
    """测试多种下载方法"""
    doc_id = "DWEVjZndkR2xVSWJN"
    cookie_str = load_cookie()
    
    test_cases = [
        {
            "name": "1. 移动端User-Agent + CSV",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_csv",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15A372',
                'Cookie': cookie_str,
                'Accept': 'application/vnd.ms-excel,application/csv,text/csv,*/*',
                'Accept-Encoding': 'gzip, deflate, br',
            }
        },
        {
            "name": "2. 微信小程序User-Agent",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.1; MP1602 Build/NMF26O; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 MicroMessenger/8.0.16.2040(0x28001053) Process/appbrand0 WeChat/arm32',
                'Cookie': cookie_str,
                'Accept': '*/*',
                'X-Requested-With': 'com.tencent.mm',
                'Referer': 'https://servicewechat.com/'
            }
        },
        {
            "name": "3. QQ浏览器特殊端点",
            "url": f"https://docs.qq.com/v2/export/excel?id={doc_id}",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3883.400 QQBrowser/10.8.4559.400',
                'Cookie': cookie_str,
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            }
        },
        {
            "name": "4. 直接二进制Accept",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': cookie_str,
                'Accept': 'application/octet-stream,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'Accept-Encoding': 'identity',  # 不压缩
            }
        },
        {
            "name": "5. 老版本API端点",
            "url": f"https://docs.qq.com/api/doc/download?id={doc_id}&format=xlsx",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': cookie_str,
            }
        },
        {
            "name": "6. 腾讯文档桌面客户端模拟",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx",
            "headers": {
                'User-Agent': 'TencentDocs/2.4.30 (Windows NT 10.0; Win64; x64)',
                'Cookie': cookie_str,
                'X-Client-Type': 'desktop',
                'X-Client-Version': '2.4.30',
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            }
        },
        {
            "name": "7. AJAX请求模拟",
            "url": f"https://docs.qq.com/dop-api/opendoc",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': cookie_str,
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            },
            "params": {
                "id": doc_id,
                "type": "export_xlsx",
                "download": "true",
                "format": "binary"
            }
        },
        {
            "name": "8. 企业版端点",
            "url": f"https://docs.qq.com/enterprise/export?docId={doc_id}&exportType=xlsx",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': cookie_str,
                'X-Enterprise-Mode': 'true',
            }
        },
        {
            "name": "9. 打印预览转换",
            "url": f"https://docs.qq.com/print/preview?id={doc_id}&format=xlsx",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': cookie_str,
            }
        },
        {
            "name": "10. WebSocket升级请求",
            "url": f"https://docs.qq.com/ws/export?id={doc_id}",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': cookie_str,
                'Upgrade': 'websocket',
                'Connection': 'Upgrade',
                'Sec-WebSocket-Version': '13',
            }
        },
    ]
    
    print("="*60)
    print("测试不同下载方法避免EJS格式")
    print("="*60)
    
    results = []
    
    for test in test_cases:
        print(f"\n测试: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            # 发送请求
            if "params" in test:
                response = requests.get(test['url'], headers=test['headers'], params=test.get('params', {}), timeout=10)
            else:
                response = requests.get(test['url'], headers=test['headers'], timeout=10)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', 'unknown')
                content_length = len(response.content)
                
                print(f"Content-Type: {content_type}")
                print(f"大小: {content_length} bytes")
                
                # 检查文件格式
                header = response.content[:100]
                
                # 检查是否是真正的Excel (ZIP格式)
                if header[:4] == b'PK\x03\x04':
                    print("✅ 成功！获得真正的Excel文件 (ZIP/XLSX格式)")
                    
                    # 保存文件
                    filename = f"success_{test['name'].replace(' ', '_').replace('/', '_')}.xlsx"
                    filepath = f"/root/projects/tencent-doc-manager/{filename}"
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"已保存: {filepath}")
                    
                    results.append({
                        'method': test['name'],
                        'success': True,
                        'format': 'real_xlsx',
                        'file': filepath
                    })
                    
                # 检查是否是CSV
                elif b',' in header or b'\t' in header or header[:3] == b'\xef\xbb\xbf':
                    # 检查是否真的是CSV而不是EJS
                    if b'head' not in header and b'json' not in header:
                        print("✅ 可能是真正的CSV文件")
                        results.append({
                            'method': test['name'],
                            'success': True,
                            'format': 'possible_csv'
                        })
                    else:
                        print("❌ 仍然是EJS格式")
                        results.append({
                            'method': test['name'],
                            'success': False,
                            'format': 'ejs'
                        })
                        
                # 检查是否是EJS
                elif b'head' in header or b'json' in header or content_type == 'text/ejs-data':
                    print("❌ 返回的是EJS格式")
                    results.append({
                        'method': test['name'],
                        'success': False,
                        'format': 'ejs'
                    })
                    
                # 检查是否是HTML错误页
                elif b'<html' in header.lower() or b'<!doctype' in header.lower():
                    print("❌ 返回HTML错误页面")
                    results.append({
                        'method': test['name'],
                        'success': False,
                        'format': 'html_error'
                    })
                    
                else:
                    print(f"❓ 未知格式")
                    print(f"前50字节: {header[:50]}")
                    results.append({
                        'method': test['name'],
                        'success': False,
                        'format': 'unknown'
                    })
                    
            elif response.status_code == 404:
                print("❌ 端点不存在 (404)")
                results.append({
                    'method': test['name'],
                    'success': False,
                    'error': '404'
                })
            else:
                print(f"❌ 请求失败: {response.status_code}")
                results.append({
                    'method': test['name'],
                    'success': False,
                    'error': str(response.status_code)
                })
                
        except Exception as e:
            print(f"❌ 错误: {e}")
            results.append({
                'method': test['name'],
                'success': False,
                'error': str(e)
            })
        
        time.sleep(1)  # 避免请求过快
    
    # 总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    success_methods = [r for r in results if r.get('success')]
    
    if success_methods:
        print(f"\n✅ 成功的方法 ({len(success_methods)}个):")
        for method in success_methods:
            print(f"  - {method['method']}: {method['format']}")
            if 'file' in method:
                print(f"    文件: {method['file']}")
    else:
        print("\n❌ 所有方法都返回EJS格式或失败")
        
    print(f"\n失败统计:")
    for format_type in ['ejs', 'html_error', '404', 'unknown']:
        count = len([r for r in results if r.get('format') == format_type or r.get('error') == format_type])
        if count > 0:
            print(f"  {format_type}: {count}个")
    
    # 保存结果
    result_file = "download_methods_test_results.json"
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n详细结果已保存到: {result_file}")
    
    return results

if __name__ == "__main__":
    results = test_download_methods()
    
    # 提供建议
    print("\n" + "="*60)
    print("建议")
    print("="*60)
    
    if any(r.get('success') for r in results):
        print("✅ 找到了避免EJS格式的方法！")
    else:
        print("看起来腾讯文档的服务器会强制返回EJS格式")
        print("\n可能的解决方案:")
        print("1. 使用浏览器自动化，让浏览器处理EJS解密")
        print("2. 分析浏览器的实际下载请求，可能有隐藏参数")
        print("3. 使用腾讯文档的官方API（需要申请）")
        print("4. 逆向工程protobuf格式")