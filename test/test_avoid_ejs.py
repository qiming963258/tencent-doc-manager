#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试避免EJS格式的方法 - 修复Cookie认证
"""

import requests
import json
import time
from datetime import datetime

def load_cookie():
    """加载Cookie"""
    with open('/root/projects/tencent-doc-manager/config/cookies_new.json', 'r') as f:
        cookie_data = json.load(f)
    return cookie_data['current_cookies']

def test_avoid_ejs():
    """测试避免EJS格式的方法"""
    doc_id = "DWEVjZndkR2xVSWJN"
    cookie_str = load_cookie()
    
    # 基础headers，所有请求都需要
    base_headers = {
        'Cookie': cookie_str,
        'Referer': f'https://docs.qq.com/sheet/{doc_id}',
        'Origin': 'https://docs.qq.com'
    }
    
    test_cases = [
        {
            "name": "标准下载(对照组)",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx",
            "headers": {
                **base_headers,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
            }
        },
        {
            "name": "强制二进制流",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx&download=1",
            "headers": {
                **base_headers,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/octet-stream',
                'Accept-Encoding': 'identity',
            }
        },
        {
            "name": "附件下载模式",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx",
            "headers": {
                **base_headers,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'Content-Disposition': 'attachment',
            }
        },
        {
            "name": "CSV纯文本模式",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_csv&format=plain",
            "headers": {
                **base_headers,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/plain,text/csv',
                'Accept-Charset': 'utf-8',
            }
        },
        {
            "name": "跳过EJS包装",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx&raw=true",
            "headers": {
                **base_headers,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'X-Skip-EJS': 'true',
                'X-Raw-Export': 'true',
            }
        },
        {
            "name": "移动端简化格式",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_csv",
            "headers": {
                **base_headers,
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'Accept': 'text/csv',
                'X-Mobile-Export': 'true',
            }
        },
        {
            "name": "直接获取数据API",
            "url": f"https://docs.qq.com/dop-api/get/sheet?id={doc_id}&tab=BB08J2",
            "headers": {
                **base_headers,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            }
        },
        {
            "name": "分片下载模式",
            "url": f"https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx&range=bytes=0-",
            "headers": {
                **base_headers,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Range': 'bytes=0-',
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            }
        },
        {
            "name": "获取下载链接",
            "url": f"https://docs.qq.com/dop-api/export/generate?id={doc_id}&type=xlsx",
            "headers": {
                **base_headers,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
        },
        {
            "name": "腾讯云COS直链",
            "url": f"https://docs.qq.com/dop-api/file/download?id={doc_id}&format=xlsx",
            "headers": {
                **base_headers,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'X-COS-Request': 'true',
            }
        }
    ]
    
    print("="*60)
    print("测试避免EJS格式的下载方法")
    print("="*60)
    
    results = []
    
    for test in test_cases:
        print(f"\n测试: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            response = requests.get(test['url'], headers=test['headers'], timeout=15)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', 'unknown')
                content_length = len(response.content)
                
                print(f"Content-Type: {content_type}")
                print(f"大小: {content_length} bytes")
                
                # 分析返回内容
                header = response.content[:200] if len(response.content) > 200 else response.content
                
                # 检查各种格式
                if header[:4] == b'PK\x03\x04':
                    print("🎉 成功！真正的Excel文件 (ZIP/XLSX)")
                    # 保存文件
                    timestamp = datetime.now().strftime("%H%M%S")
                    filename = f"success_{timestamp}_{test['name'].replace(' ', '_')}.xlsx"
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"已保存: {filename}")
                    
                    results.append({
                        'method': test['name'],
                        'success': True,
                        'format': 'real_xlsx',
                        'file': filename
                    })
                    
                elif b'head' in header[:50] and b'json' in header[:50]:
                    print("❌ EJS格式")
                    results.append({
                        'method': test['name'],
                        'success': False,
                        'format': 'ejs'
                    })
                    
                elif content_type == 'text/ejs-data':
                    print("❌ 明确的EJS格式 (Content-Type)")
                    results.append({
                        'method': test['name'],
                        'success': False,
                        'format': 'ejs'
                    })
                    
                elif b'<html' in header.lower() or b'<!doctype' in header.lower():
                    print("❌ HTML错误页面")
                    results.append({
                        'method': test['name'],
                        'success': False,
                        'format': 'html'
                    })
                    
                elif content_type.startswith('application/json'):
                    print("📊 JSON响应")
                    try:
                        json_data = response.json()
                        print(f"JSON Keys: {list(json_data.keys())[:5]}")
                        
                        # 检查是否包含下载链接
                        if 'download_url' in json_data or 'url' in json_data:
                            print("✅ 可能包含下载链接")
                            results.append({
                                'method': test['name'],
                                'success': 'maybe',
                                'format': 'json_with_url',
                                'data': json_data
                            })
                        else:
                            results.append({
                                'method': test['name'],
                                'success': False,
                                'format': 'json'
                            })
                    except:
                        results.append({
                            'method': test['name'],
                            'success': False,
                            'format': 'invalid_json'
                        })
                        
                else:
                    # 检查是否可能是CSV
                    try:
                        text = response.content[:1000].decode('utf-8', errors='ignore')
                        if ',' in text and '\n' in text and not '<' in text:
                            # 检查是否真的是CSV而不是EJS
                            if 'head' not in text and 'json' not in text:
                                print("✅ 可能是真正的CSV")
                                timestamp = datetime.now().strftime("%H%M%S")
                                filename = f"maybe_csv_{timestamp}_{test['name'].replace(' ', '_')}.csv"
                                with open(filename, 'wb') as f:
                                    f.write(response.content)
                                print(f"已保存: {filename}")
                                
                                results.append({
                                    'method': test['name'],
                                    'success': 'maybe',
                                    'format': 'possible_csv',
                                    'file': filename
                                })
                            else:
                                print("❌ 伪装成CSV的EJS")
                                results.append({
                                    'method': test['name'],
                                    'success': False,
                                    'format': 'ejs_as_csv'
                                })
                        else:
                            print(f"❓ 未知格式")
                            print(f"前100字节: {header[:100]}")
                            results.append({
                                'method': test['name'],
                                'success': False,
                                'format': 'unknown'
                            })
                    except:
                        print("❓ 二进制或未知格式")
                        results.append({
                            'method': test['name'],
                            'success': False,
                            'format': 'binary_unknown'
                        })
                        
            else:
                print(f"❌ HTTP {response.status_code}")
                results.append({
                    'method': test['name'],
                    'success': False,
                    'error': f'HTTP_{response.status_code}'
                })
                
        except Exception as e:
            print(f"❌ 异常: {e}")
            results.append({
                'method': test['name'],
                'success': False,
                'error': str(e)
            })
            
        time.sleep(1)
    
    # 总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    real_success = [r for r in results if r.get('success') == True]
    maybe_success = [r for r in results if r.get('success') == 'maybe']
    ejs_count = len([r for r in results if r.get('format') == 'ejs'])
    
    if real_success:
        print(f"\n🎉 成功避免EJS的方法 ({len(real_success)}个):")
        for r in real_success:
            print(f"  ✅ {r['method']}")
            if 'file' in r:
                print(f"     文件: {r['file']}")
    
    if maybe_success:
        print(f"\n🤔 可能成功的方法 ({len(maybe_success)}个):")
        for r in maybe_success:
            print(f"  ⚠️  {r['method']} ({r['format']})")
    
    if not real_success and not maybe_success:
        print(f"\n❌ 所有方法都失败了")
        print(f"   EJS格式: {ejs_count}个")
        print(f"   其他错误: {len(results) - ejs_count}个")
    
    # 保存结果
    result_file = f"avoid_ejs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存: {result_file}")
    
    return results

if __name__ == "__main__":
    results = test_avoid_ejs()
    
    print("\n" + "="*60)
    print("分析与建议")
    print("="*60)
    
    if any(r.get('success') == True for r in results):
        print("✅ 找到了避免EJS的方法！可以获取真实的Excel文件")
    else:
        print("腾讯文档服务器强制使用EJS格式封装数据")
        print("\n原因分析:")
        print("1. EJS格式包含权限、版本等元数据")
        print("2. 数据经过protobuf编码，需要前端JavaScript解密")
        print("3. 这是腾讯的数据保护机制")
        print("\n解决方案:")
        print("1. 使用Playwright/Selenium自动化浏览器下载")
        print("2. 继续研究protobuf解码（已部分成功）")
        print("3. 申请官方API接口")