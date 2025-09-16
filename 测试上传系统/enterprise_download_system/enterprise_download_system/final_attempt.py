#!/usr/bin/env python3
"""
完全模拟用户操作的下载器 - 最终版本
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def final_attempt_download():
    print("🚀 最终尝试：完全模拟真实用户操作...")
    
    download_dir = Path("/root/projects/tencent-doc-manager/enterprise_download_system/downloads").resolve()
    download_dir.mkdir(exist_ok=True)
    
    cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZpaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
    
    downloaded_files = []
    
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
    
    async def handle_download(download):
        try:
            filename = download.suggested_filename
            download_path = download_dir / filename
            print(f"⬇️  下载开始: {filename}")
            await download.save_as(download_path)
            downloaded_files.append(str(download_path))
            file_size = download_path.stat().st_size if download_path.exists() else 0
            print(f"✅ 下载成功: {filename} ({file_size:,} 字节)")
            return True
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return False
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',  # 隐藏自动化特征
                '--disable-extensions', '--no-first-run', '--disable-default-apps'
            ]
        )
        
        # 创建更真实的浏览器环境
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True,
            java_script_enabled=True,
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'max-age=0',
                'Sec-Ch-Ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        await context.add_cookies(cookies)
        page = await context.new_page()
        page.on('download', handle_download)
        
        # 完全模拟真实用户的访问流程
        print("📄 第1步: 访问腾讯文档主页...")
        await page.goto('https://docs.qq.com/', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)
        print(f"   主页标题: {await page.title()}")
        
        print("📄 第2步: 访问桌面版...")
        await page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(15000)  # 等待足够长时间让JS执行
        print(f"   桌面版标题: {await page.title()}")
        print(f"   当前URL: {page.url}")
        
        # 第3步：尝试各种方式进入文档列表
        success = False
        
        # 方式A: 模拟鼠标移动和点击Cloud Docs
        print("📄 第3A步: 尝试点击Cloud Docs...")
        try:
            # 先移动鼠标到按钮
            cloud_docs_element = await page.wait_for_selector('text=Cloud Docs', timeout=10000)
            if cloud_docs_element:
                # 模拟真实用户的鼠标移动
                box = await cloud_docs_element.bounding_box()
                if box:
                    await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    await page.wait_for_timeout(1000)
                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    await page.wait_for_timeout(10000)
                    
                    if page.url != 'https://docs.qq.com/desktop':
                        print(f"   ✅ 成功跳转到: {page.url}")
                        success = True
        except Exception as e:
            print(f"   ❌ Cloud Docs点击失败: {e}")
        
        # 方式B: 直接尝试几个可能的文档URL
        if not success:
            urls_to_try = [
                'https://docs.qq.com/desktop/file/recent?tab=recent',
                'https://docs.qq.com/desktop/mydocs?tab=mydocs', 
                'https://docs.qq.com/folder/DdkF0QmdHdXpu',
                'https://docs.qq.com/desktop/file',
                'https://docs.qq.com/desktop?tab=recent'
            ]
            
            for url in urls_to_try:
                try:
                    print(f"📄 第3B步: 尝试直接访问 {url}")
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(10000)
                    
                    if page.url != 'https://docs.qq.com/desktop':
                        print(f"   ✅ 成功访问: {page.url}")
                        success = True
                        break
                except Exception as e:
                    print(f"   ❌ 访问失败: {e}")
                    continue
        
        # 第4步：在当前页面暴力搜索所有可能是文档的内容
        print("📄 第4步: 暴力搜索潜在文档...")
        
        # 创建一个包含所有可能文档关键词的超级搜索
        document_keywords = [
            'doc', 'docx', 'sheet', 'xlsx', 'slide', 'pptx', 'pdf', 
            '文档', '表格', '演示', '幻灯片', '电子表格', '文稿'
        ]
        
        # 搜索页面中所有包含文档关键词的元素
        potential_docs = []
        try:
            # 使用JS在页面中搜索
            results = await page.evaluate(f"""
                () => {{
                    const keywords = {document_keywords};
                    const results = [];
                    
                    // 搜索所有文本节点
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let node;
                    while (node = walker.nextNode()) {{
                        const text = node.textContent.trim();
                        if (text.length > 5 && text.length < 100) {{
                            for (const keyword of keywords) {{
                                if (text.toLowerCase().includes(keyword)) {{
                                    const element = node.parentElement;
                                    if (element && element.tagName) {{
                                        results.push({{
                                            text: text,
                                            tagName: element.tagName,
                                            className: element.className,
                                            href: element.href || ''
                                        }});
                                        break;
                                    }}
                                }}
                            }}
                        }}
                    }}
                    
                    return results.slice(0, 20);  // 返回前20个结果
                }}
            """)
            
            print(f"   🔍 找到 {len(results)} 个潜在文档关键词")
            
            # 根据JS搜索结果，尝试查找对应元素
            for i, result in enumerate(results[:5]):  # 只处理前5个
                try:
                    print(f"   📋 尝试文档 {i+1}: {result['text'][:50]}")
                    
                    # 尝试通过文本找到元素
                    elements = await page.query_selector_all(f'text="{result["text"]}"')
                    if not elements:
                        # 尝试部分匹配
                        elements = await page.query_selector_all(f'text=/{result["text"][:20]}/')
                    
                    if elements:
                        element = elements[0]
                        potential_docs.append((element, result['text']))
                        print(f"   ✅ 找到对应元素")
                    
                except Exception as e:
                    print(f"   ⚠️  处理文档 {i+1} 失败: {e}")
                    continue
            
        except Exception as e:
            print(f"   ❌ JS搜索失败: {e}")
        
        # 如果还是没找到，尝试最后的手段：模拟键盘搜索
        if not potential_docs:
            print("📄 第5步: 尝试键盘快捷键搜索...")
            try:
                # 按Ctrl+F打开搜索框
                await page.keyboard.press('Control+f')
                await page.wait_for_timeout(2000)
                
                # 搜索常见文档扩展名
                search_terms = ['.doc', '.xls', '.ppt', '文档']
                for term in search_terms:
                    try:
                        await page.keyboard.type(term)
                        await page.keyboard.press('Enter')
                        await page.wait_for_timeout(3000)
                        
                        # 检查是否有搜索结果高亮
                        highlighted = await page.query_selector_all('[class*="highlight"], [class*="search"], [class*="match"]')
                        if highlighted:
                            print(f"   ✅ 找到搜索结果: {term}")
                            potential_docs.extend([(elem, term) for elem in highlighted[:3]])
                            break
                        
                        # 清空搜索框
                        await page.keyboard.press('Control+a')
                        await page.keyboard.press('Backspace')
                        await page.wait_for_timeout(1000)
                        
                    except:
                        continue
                
                # 关闭搜索框
                await page.keyboard.press('Escape')
                
            except Exception as e:
                print(f"   ❌ 键盘搜索失败: {e}")
        
        # 第6步：尝试下载找到的文档
        if potential_docs:
            print(f"📄 第6步: 尝试下载 {len(potential_docs)} 个潜在文档...")
            
            for i, (element, text) in enumerate(potential_docs[:3]):  # 最多下载3个
                try:
                    print(f"\\n   📄 处理文档 {i+1}: {text[:40]}")
                    
                    # 滚动到元素
                    await element.scroll_into_view_if_needed()
                    await page.wait_for_timeout(2000)
                    
                    # 尝试各种下载方式
                    
                    # 方式1: 右键菜单
                    try:
                        await element.click(button='right', timeout=10000)
                        await page.wait_for_timeout(3000)
                        
                        download_options = await page.query_selector_all('text=下载')
                        if not download_options:
                            download_options = await page.query_selector_all('text=Download')
                        if not download_options:
                            download_options = await page.query_selector_all('text=导出')
                        
                        if download_options:
                            await download_options[0].click()
                            print(f"   ✅ 右键下载成功")
                            await page.wait_for_timeout(5000)
                        else:
                            print(f"   ❌ 未找到右键下载选项")
                            await page.click('body')  # 关闭菜单
                            
                    except Exception as e:
                        print(f"   ❌ 右键下载失败: {e}")
                    
                    # 方式2: 双击
                    try:
                        await element.dblclick(timeout=5000)
                        await page.wait_for_timeout(3000)
                        print(f"   ✅ 双击尝试完成")
                    except:
                        pass
                    
                    # 方式3: 单击然后查找下载按钮
                    try:
                        await element.click(timeout=5000)
                        await page.wait_for_timeout(2000)
                        
                        # 查找页面上的下载按钮
                        download_buttons = await page.query_selector_all('button:has-text("下载"), button:has-text("Download"), [class*="download"]')
                        if download_buttons:
                            await download_buttons[0].click()
                            print(f"   ✅ 单击后下载按钮点击成功")
                            await page.wait_for_timeout(5000)
                            
                    except:
                        pass
                    
                except Exception as e:
                    print(f"   ❌ 处理文档 {i+1} 完全失败: {e}")
                    continue
        else:
            print("❌ 未找到任何潜在的文档元素")
        
        # 最后等待所有下载完成
        print("⏳ 等待所有下载任务完成...")
        await page.wait_for_timeout(30000)
        
        await browser.close()
    
    return downloaded_files

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║              最终尝试：完全模拟真实用户操作流程                             ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    try:
        files = asyncio.run(final_attempt_download())
        
        # 检查结果
        download_dir = Path("/root/projects/tencent-doc-manager/enterprise_download_system/downloads")
        actual_files = list(download_dir.glob("*"))
        
        print("\\n" + "=" * 60)
        print("📊 最终下载结果:")
        print(f"📁 下载目录: {download_dir}")
        print(f"📄 程序记录下载: {len(files)} 个文件")
        print(f"📄 实际目录文件: {len(actual_files)} 个文件")
        
        if actual_files:
            print("\\n📋 实际下载的文件:")
            for i, file_path in enumerate(actual_files, 1):
                try:
                    size = file_path.stat().st_size
                    print(f"{i:2d}. {file_path.name}")
                    print(f"     大小: {size:,} 字节")
                    print(f"     完整路径: {file_path}")
                except Exception as e:
                    print(f"{i:2d}. {file_path.name} (大小获取失败: {e})")
            
            print("\\n🎉 成功下载了文件！上述路径即为您要验证的文件位置。")
        else:
            print("\\n⚠️  下载目录仍为空")
            print("\\n💡 可能的原因:")
            print("   1. 腾讯文档有防自动化保护")
            print("   2. 需要在真实浏览器环境中进行")
            print("   3. 页面结构与预期不同")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 最终尝试异常: {e}")