#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import json
from datetime import datetime

def analyze_export_deep():
    print('=== 🔍 腾讯文档导出机制深度分析 ===')
    
    cookie_str = 'fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; backup_cdn_domain=docs2.gtimg.com; traceid=a473487816; TOK=a473487816963a48; hashkey=a4734878; dark_mode_setting=system; optimal_cdn_domain=docs.qq.com; ES2=f88c0411768984b9; _qpsvr_localtk=0.5895351222297797; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiME1pTENKU1ppSTZJbEZPVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; language=zh-CN'
    
    cookies = {}
    for item in cookie_str.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value
    
    doc_id = 'DWEVjZndkR2xVSWJN'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json,text/html,*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update(cookies)
    
    print(f'文档ID: {doc_id}')
    
    # 尝试常见的腾讯文档API模式
    api_endpoints = [
        # 导出相关API
        f'/dop-api/sheet/export',
        f'/api/sheet/{doc_id}/export',
        f'/dop-api/export/sheet',
        f'/cgi-bin/doc_export',
        f'/api/v1/sheet/export',
        
        # 数据获取API  
        f'/dop-api/sheet/data',
        f'/api/sheet/{doc_id}/data',
        f'/dop-api/sheet/content',
        f'/api/sheet/{doc_id}/cells'
    ]
    
    base_url = 'https://docs.qq.com'
    
    # 测试不同的请求方法和参数
    test_params = [
        {'docId': doc_id, 'format': 'csv'},
        {'padId': doc_id, 'format': 'csv'},
        {'sheetId': doc_id, 'exportType': 'csv'},
        {'docId': doc_id, 'type': 'export', 'format': 'csv'},
        {'pad_id': doc_id, 'output_format': 'csv'}
    ]
    
    print(f'\\n测试 {len(api_endpoints)} 个API端点...')
    
    for endpoint in api_endpoints:
        full_url = base_url + endpoint
        print(f'\\n测试端点: {endpoint}')
        
        for i, params in enumerate(test_params):
            try:
                # GET请求
                response = session.get(full_url, params=params, timeout=10)
                print(f'  GET {i+1}: {response.status_code} ({len(response.text)} 字符)')
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'csv' in content_type.lower():
                        print(f'    ✅ 发现CSV响应！')
                        print(f'    Content-Type: {content_type}')
                        
                        # 保存CSV文件
                        filename = f'found_csv_{doc_id}_{endpoint.replace(\"/\", \"_\")}_{i}.csv'
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        print(f'    💾 已保存: {filename}')
                        return True
                        
                    elif response.status_code == 200 and len(response.text) > 100:
                        # 检查内容是否可能是CSV格式
                        content = response.text[:1000]
                        if ',' in content and '\\n' in content and not '<html' in content.lower():
                            print(f'    💡 可能的CSV内容')
                            lines = response.text.strip().split('\\n')[:3]
                            for line in lines:
                                print(f'      {line[:100]}')
                
                # POST请求
                response = session.post(full_url, json=params, timeout=10)
                print(f'  POST {i+1}: {response.status_code} ({len(response.text)} 字符)')
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'json' in content_type.lower():
                        try:
                            data = json.loads(response.text)
                            print(f'    JSON键: {list(data.keys())[:3]}')
                            
                            # 检查是否有下载链接
                            if 'download_url' in str(data) or 'export_url' in str(data):
                                print(f'    💡 可能包含下载链接')
                                
                        except:
                            pass
                            
            except Exception as e:
                continue  # 静默失败，继续下一个
    
    print('\\n尝试分析页面中的导出按钮和JavaScript...')
    
    try:
        # 获取主页面
        page_url = f'https://docs.qq.com/sheet/{doc_id}'
        response = session.get(page_url, timeout=15)
        
        if response.status_code == 200:
            content = response.text
            
            # 查找导出相关的JavaScript函数
            export_functions = re.findall(r'function\\s+\\w*export\\w*\\([^)]*\\)\\s*\\{[^}]*\\}', content, re.IGNORECASE)
            if export_functions:
                print(f'发现导出函数: {len(export_functions)} 个')
                for func in export_functions[:2]:
                    print(f'  {func[:100]}...')
            
            # 查找API调用
            api_calls = re.findall(r'[\"\\\']/[^\"\\\']*api[^\"\\\']*export[^\"\\\']*[\"\\']', content, re.IGNORECASE)
            if api_calls:
                print(f'发现API调用: {len(api_calls)} 个')
                for call in set(api_calls[:5]):
                    print(f'  {call}')
                    
                    # 尝试访问找到的API
                    clean_url = call.strip('\"\\\'')
                    if clean_url.startswith('/'):
                        test_url = f'https://docs.qq.com{clean_url}'
                        try:
                            test_resp = session.get(test_url, params={'docId': doc_id, 'format': 'csv'}, timeout=5)
                            print(f'    测试结果: {test_resp.status_code}')
                        except:
                            pass
    
    except Exception as e:
        print(f'页面分析失败: {str(e)}')
    
    return False

if __name__ == '__main__':
    success = analyze_export_deep()
    if success:
        print('\\n🎉 成功找到CSV导出方法！')
    else:
        print('\\n❌ 未找到直接的CSV导出方法')
        print('\\n💡 建议：')
        print('1. 使用官方腾讯文档API (需要申请开发者权限)')
        print('2. 使用浏览器自动化完成导出操作')
        print('3. 手动导出CSV文件后使用系统处理')