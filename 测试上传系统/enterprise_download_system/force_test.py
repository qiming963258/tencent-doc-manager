#!/usr/bin/env python3
"""
强制下载测试 - 尝试下载2个文档
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def force_download_test():
    download_dir = Path("/root/projects/tencent-doc-manager/enterprise_download_system/downloads").resolve()
    download_dir.mkdir(exist_ok=True)
    
    cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZvaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJOaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
    
    # 解析Cookie
    cookies = []
    for cookie_pair in cookie_string.split('; '):
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.docs.qq.com',
                'path': '/'
            })
    
    downloaded_files = []
    
    async def handle_download(download):
        try:
            filename = download.suggested_filename
            download_path = download_dir / filename
            print(f"⬇️  开始下载: {filename}")
            await download.save_as(download_path)
            downloaded_files.append(str(download_path))
            file_size = download_path.stat().st_size if download_path.exists() else 0
            print(f"✅ 下载完成: {filename} ({file_size:,} 字节)")
        except Exception as e:
            print(f"❌ 下载处理失败: {e}")
    
    async with async_playwright() as playwright:
        print("🚀 启动浏览器...")
        browser = await playwright.chromium.launch(
            headless=True, 
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True,
            extra_http_headers={
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
        )
        
        await context.add_cookies(cookies)
        page = await context.new_page()
        page.on('download', handle_download)
        
        print("🏠 访问桌面页面...")
        await page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(15000)  # 等待15秒
        
        print(f"📄 标题: {await page.title()}")
        print(f"📍 URL: {page.url}")
        
        # 尝试多种导航方式
        navigation_success = False
        
        # 方式1: 点击Cloud Docs
        try:
            print("🔍 方式1: 查找并点击Cloud Docs...")
            cloud_button = await page.wait_for_selector('text=Cloud Docs', timeout=10000)
            if cloud_button:
                await cloud_button.click()
                await page.wait_for_timeout(12000)
                print(f"✅ Cloud Docs点击后URL: {page.url}")
                navigation_success = True
        except Exception as e:
            print(f"⚠️  方式1失败: {e}")
        
        # 方式2: 直接访问不同的URL
        if not navigation_success:
            urls_to_try = [
                'https://docs.qq.com/desktop/mydocs',
                'https://docs.qq.com/desktop/file/recent',
                'https://docs.qq.com/desktop/recent',
                'https://docs.qq.com/folder'
            ]
            
            for url in urls_to_try:
                try:
                    print(f"🔍 方式2: 尝试直接访问 {url}")
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(10000)
                    print(f"✅ 访问成功: {page.url}")
                    navigation_success = True
                    break
                except Exception as e:
                    print(f"⚠️  访问失败: {e}")
                    continue
        
        # 尝试查找任何可能的文档元素并下载
        print("🔍 开始暴力搜索所有可能的文档元素...")
        
        # 扩大搜索范围
        all_selectors = [
            'a', 'div', 'span', 'li', 'tr', 'td', 'button',
            '[class*="file"]', '[class*="doc"]', '[class*="item"]',
            '[class*="row"]', '[class*="list"]', '[data-*]',
            '.desktop-file-list-item', '.file-item', '.document-item'
        ]
        
        potential_docs = []
        
        for selector in all_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    try:
                        text = await elem.inner_text()
                        if text and len(text.strip()) > 10 and len(text.strip()) < 200:
                            # 检查是否包含文档相关关键词
                            text_lower = text.lower().strip()
                            if any(keyword in text_lower for keyword in ['doc', 'sheet', 'slide', 'excel', 'word', 'ppt', '文档', '表格', '演示', '.doc', '.xls', '.ppt']):
                                potential_docs.append((elem, text.strip()))
                    except:
                        continue
                
                if len(potential_docs) >= 10:  # 收集足够的候选元素
                    break
            except:
                continue
        
        print(f"🎯 找到 {len(potential_docs)} 个潜在文档元素")
        
        if potential_docs:
            download_attempts = 0
            target_downloads = min(2, len(potential_docs))  # 尝试下载2个
            
            for i, (elem, text) in enumerate(potential_docs[:10]):  # 最多尝试前10个
                if download_attempts >= target_downloads:
                    break
                    
                try:
                    print(f"\\n📄 尝试下载元素 {i+1}: {text[:50]}...")
                    
                    # 滚动到元素
                    await elem.scroll_into_view_if_needed()
                    await page.wait_for_timeout(2000)
                    
                    # 右键点击
                    try:
                        await elem.click(button='right', timeout=10000)
                        print("🖱️  右键点击成功")
                        await page.wait_for_timeout(3000)
                        
                        # 查找下载选项
                        download_selectors = [
                            'text=下载', 'text=Download', 'text=导出', 'text=Export',
                            '[class*="download"]', '[data-testid*="download"]'
                        ]
                        
                        download_success = False
                        for download_selector in download_selectors:
                            try:
                                download_btn = await page.wait_for_selector(download_selector, timeout=3000)
                                if download_btn:
                                    await download_btn.click()
                                    print(f"✅ 点击下载按钮: {download_selector}")
                                    download_attempts += 1
                                    download_success = True
                                    
                                    # 等待下载开始
                                    await page.wait_for_timeout(5000)
                                    
                                    # 处理下载确认
                                    try:
                                        await page.click('text=允许', timeout=2000)
                                    except:
                                        pass
                                    
                                    break
                            except:
                                continue
                        
                        if not download_success:
                            print("⚠️  未找到下载选项")
                            # 点击其他地方关闭菜单
                            await page.click('body')
                        
                    except Exception as e:
                        print(f"⚠️  右键点击失败: {e}")
                        continue
                        
                except Exception as e:
                    print(f"❌ 处理元素失败: {e}")
                    continue
        
        # 等待所有下载完成
        print("⏳ 等待下载完成...")
        await page.wait_for_timeout(20000)
        
        await browser.close()
        
        return downloaded_files

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                     强制下载测试 - 尝试下载2个文档                         ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    try:
        files = asyncio.run(force_download_test())
        
        print("\\n" + "=" * 60)
        print("📊 下载测试结果:")
        print(f"📄 成功下载文件数: {len(files)}")
        
        if files:
            print("\\n📋 下载的文件:")
            for i, file_path in enumerate(files, 1):
                print(f"{i}. {file_path}")
                try:
                    size = Path(file_path).stat().st_size
                    print(f"   大小: {size:,} 字节")
                except:
                    print("   大小: 未知")
        else:
            print("⚠️  未成功下载任何文件")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")