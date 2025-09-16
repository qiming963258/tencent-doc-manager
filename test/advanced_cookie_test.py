#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re

def test_cookie_advanced():
    print('=== 深度Cookie测试 - 完整浏览器模拟 ===')
    
    cookie_str = 'fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; backup_cdn_domain=docs2.gtimg.com; traceid=a473487816; TOK=a473487816963a48; hashkey=a4734878; dark_mode_setting=system; optimal_cdn_domain=docs.qq.com; ES2=f88c0411768984b9; _qpsvr_localtk=0.5895351222297797; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZKVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU5TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; language=zh-CN'
    
    # 解析Cookie
    cookies = {}
    for item in cookie_str.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value
    
    print(f'Cookie项数: {len(cookies)}')
    
    # 完整Chrome浏览器请求头
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Host': 'docs.qq.com',
        'Pragma': 'no-cache',
        'Referer': 'https://docs.qq.com/',
        'Sec-Ch-Ua': '"Google Chrome";v="120", "Chromium";v="120", "Not_A Brand";v="8"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate', 
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 创建session
    session = requests.Session()
    session.headers.update(headers)
    
    # 测试URL
    target_url = 'https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN?tab=c2p5hs'
    
    try:
        print(f'\n测试URL: {target_url}')
        
        # 首先访问首页
        print('\n1. 建立会话...')
        home_resp = session.get('https://docs.qq.com/', cookies=cookies, timeout=15)
        print(f'   首页状态: {home_resp.status_code}')
        
        # 访问目标文档
        print('\n2. 访问目标文档...')
        response = session.get(target_url, cookies=cookies, timeout=20)
        
        print(f'   状态码: {response.status_code}')
        print(f'   内容大小: {len(response.text):,} 字符')
        print(f'   最终URL: {response.url}')
        
        content = response.text
        
        # 分析页面内容
        print('\n3. 内容分析:')
        
        # 失败指标
        login_keywords = ['请登录', 'Please login', '用户登录', 'Sign in']
        login_found = any(keyword in content for keyword in login_keywords)
        has_login_form = '<form' in content and ('login' in content.lower() or 'password' in content.lower())
        url_redirected = response.url != target_url
        
        print(f'   登录关键词: {"发现" if login_found else "未发现"}')
        print(f'   登录表单: {"发现" if has_login_form else "未发现"}')  
        print(f'   URL重定向: {"是" if url_redirected else "否"}')
        
        # 成功指标
        has_initial_state = 'window.__INITIAL_STATE__' in content
        has_page_data = 'window.PAGE_DATA' in content
        has_vue_app = 'vue' in content.lower() and 'app' in content.lower()
        has_spreadsheet = 'spreadsheet' in content.lower() or 'sheet' in content.lower()
        content_rich = len(content) > 200000
        
        print(f'   初始状态数据: {"发现" if has_initial_state else "未发现"}')
        print(f'   页面数据: {"发现" if has_page_data else "未发现"}')
        print(f'   Vue应用: {"发现" if has_vue_app else "未发现"}')
        print(f'   表格相关: {"发现" if has_spreadsheet else "未发现"}')
        print(f'   内容丰富: {"是" if content_rich else "否"}')
        
        # 提取页面标题
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            print(f'   页面标题: {title}')
            
            title_success = any(word in title for word in ['文档', 'Document', 'Sheet', '测试版本-小红书部门'])
            print(f'   标题匹配: {"是" if title_success else "否"}')
        else:
            title_success = False
            print('   页面标题: 未找到')
        
        # 综合判断
        success_count = sum([
            has_initial_state,
            has_page_data, 
            has_vue_app,
            has_spreadsheet,
            content_rich,
            title_success
        ])
        
        failure_count = sum([
            login_found,
            has_login_form,
            url_redirected
        ])
        
        print(f'\n4. 综合评分:')
        print(f'   成功指标: {success_count}/6')
        print(f'   失败指标: {failure_count}/3')
        
        if success_count >= 4 and failure_count <= 1:
            print('\n✅ Cookie完全有效！文档访问成功')
            print('   之前的检测方法可能过于简单')
            return True
        elif success_count >= 2 and failure_count <= 2:
            print('\n⚠️ Cookie部分有效，可能存在某些限制')
            return True
        else:
            print('\n❌ Cookie无效或存在访问问题')
            
            # 输出调试信息
            print('\n调试信息 - 页面开头500字符:')
            print('-' * 50)
            print(content[:500])
            print('-' * 50)
            
            return False
            
    except Exception as e:
        print(f'\n❌ 请求异常: {str(e)}')
        return False

if __name__ == '__main__':
    result = test_cookie_advanced()
    print(f'\n🎯 最终结论: Cookie {"有效可用" if result else "需要进一步调试"}')