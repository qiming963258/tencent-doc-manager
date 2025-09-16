#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接使用浏览器上下文获取真实文件
不通过页面点击，而是直接访问下载URL
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
import time

async def direct_download():
    """直接下载方法"""
    print("="*60)
    print("直接浏览器下载测试")
    print("="*60)
    
    # 加载cookie
    with open('/root/projects/tencent-doc-manager/config/cookies_new.json', 'r') as f:
        cookie_data = json.load(f)
    cookie_str = cookie_data['current_cookies']
    
    # 转换cookie格式
    cookies = []
    for item in cookie_str.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies.append({
                'name': key,
                'value': value,
                'domain': '.docs.qq.com',
                'path': '/'
            })
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        # 创建上下文
        context = await browser.new_context(
            accept_downloads=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 添加cookies
        await context.add_cookies(cookies)
        print(f"✅ 设置了 {len(cookies)} 个Cookie")
        
        # 创建页面
        page = await context.new_page()
        
        # 关键：先访问主页面建立会话
        doc_id = 'DWEVjZndkR2xVSWJN'
        print(f"\n1. 先访问文档页面建立会话")
        await page.goto(f'https://docs.qq.com/sheet/{doc_id}', wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)
        
        # 方法1：使用page.goto直接下载
        print(f"\n2. 尝试直接导航到下载URL")
        download_url = f'https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx'
        
        try:
            # 监听响应
            async def handle_response(response):
                if 'opendoc' in response.url:
                    print(f"  捕获响应: {response.status}")
                    print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
                    
                    # 获取响应内容
                    body = await response.body()
                    print(f"  响应大小: {len(body)} bytes")
                    
                    # 保存响应
                    output_file = Path('browser_response.data')
                    with open(output_file, 'wb') as f:
                        f.write(body)
                    
                    # 检查格式
                    if body[:4] == b'PK\x03\x04':
                        print("  🎉 是真实的Excel文件!")
                        output_file.rename('browser_download.xlsx')
                        return True
                    elif b'head' in body[:50] and b'json' in body[:50]:
                        print("  ❌ 仍然是EJS格式")
                        # 但我们可以用浏览器解析它！
                        return await try_browser_decode(page, body)
                    else:
                        print(f"  ❓ 未知格式: {body[:50]}")
            
            page.on('response', handle_response)
            
            # 访问下载URL
            response = await page.goto(download_url, wait_until='networkidle')
            
        except Exception as e:
            print(f"方法1失败: {e}")
        
        # 方法2：使用fetch API
        print(f"\n3. 使用浏览器的fetch API")
        result = await page.evaluate(f'''
            async () => {{
                const response = await fetch('https://docs.qq.com/dop-api/opendoc?id={doc_id}&type=export_xlsx', {{
                    credentials: 'include',
                    headers: {{
                        'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    }}
                }});
                
                const contentType = response.headers.get('content-type');
                const buffer = await response.arrayBuffer();
                const bytes = new Uint8Array(buffer);
                
                // 检查文件头
                const header = Array.from(bytes.slice(0, 4));
                
                return {{
                    status: response.status,
                    contentType: contentType,
                    size: bytes.length,
                    headerBytes: header,
                    isPK: header[0] === 0x50 && header[1] === 0x4B,
                    isEJS: contentType && contentType.includes('ejs')
                }};
            }}
        ''')
        
        print(f"Fetch结果: {json.dumps(result, indent=2)}")
        
        if result.get('isPK'):
            print("🎉 浏览器获取到真实Excel文件！")
            # 需要额外步骤保存文件
        elif result.get('isEJS'):
            print("浏览器也收到EJS格式，但可以在浏览器中解密")
            
            # 方法3：让浏览器解密EJS
            print(f"\n4. 尝试在浏览器中解密EJS")
            decrypt_result = await page.evaluate('''
                () => {
                    // 查找腾讯文档的解密函数
                    if (typeof window.decodeEJS === 'function') {
                        return "Found decodeEJS function";
                    }
                    
                    // 查找可能的解密相关对象
                    const possibleDecrypt = [
                        window.TencentDoc,
                        window.docApp,
                        window.sheet,
                        window.exportManager
                    ];
                    
                    for (let obj of possibleDecrypt) {
                        if (obj && typeof obj === 'object') {
                            return `Found object: ${obj.constructor.name}`;
                        }
                    }
                    
                    return "No decrypt function found";
                }
            ''')
            print(f"解密函数搜索结果: {decrypt_result}")
        
        await browser.close()

async def try_browser_decode(page, ejs_data):
    """尝试用浏览器解码EJS数据"""
    print("\n  尝试浏览器端解码...")
    
    # 将EJS数据传给浏览器
    # 由于数据可能很大，使用base64传输
    import base64
    ejs_b64 = base64.b64encode(ejs_data).decode('ascii')
    
    decode_result = await page.evaluate(f'''
        (ejsBase64) => {{
            try {{
                // 解码base64
                const ejsData = atob(ejsBase64);
                
                // 尝试解析EJS格式
                // 腾讯文档的页面应该有相关函数
                if (window.parseEJS) {{
                    return window.parseEJS(ejsData);
                }}
                
                // 手动解析
                const lines = ejsData.split('\\n');
                if (lines[0] === 'head' && lines[1] === 'json') {{
                    // 这确实是EJS格式
                    const jsonLength = parseInt(lines[2]);
                    const jsonData = lines[3];
                    
                    return {{
                        format: 'ejs',
                        hasJson: true,
                        jsonLength: jsonLength
                    }};
                }}
                
                return {{ error: 'Not EJS format' }};
                
            }} catch (e) {{
                return {{ error: e.toString() }};
            }}
        }}
    ''', ejs_b64)
    
    print(f"  浏览器解码结果: {decode_result}")
    return decode_result

async def main():
    """主函数"""
    try:
        await direct_download()
        
        # 检查结果
        files = list(Path('.').glob('browser_*.xlsx'))
        if files:
            print(f"\n✅ 成功！找到下载的文件: {files[0]}")
            
            # 验证文件
            with open(files[0], 'rb') as f:
                header = f.read(4)
                if header == b'PK\x03\x04':
                    print("✅ 确认是真实的Excel文件（ZIP格式）")
                    print("\n🎉 短期方案可行！浏览器自动化成功获取真实Excel文件")
        else:
            print("\n当前方法未能直接获取Excel，但证明了浏览器可以访问")
            print("需要进一步优化下载策略")
            
    except Exception as e:
        print(f"\n错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())