#!/usr/bin/env python3
"""
页面结构分析器 - 保存HTML并分析UI元素
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def analyze_page_structure():
    cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZpaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
    
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
    
    analysis_file = Path("/root/projects/tencent-doc-manager/enterprise_download_system/page_analysis.html")
    selector_file = Path("/root/projects/tencent-doc-manager/enterprise_download_system/ui_selectors.txt")
    
    async with async_playwright() as playwright:
        print("🚀 启动分析浏览器...")
        browser = await playwright.chromium.launch(
            headless=True,  # 服务器环境使用无头模式
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
        )
        
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        print("📄 访问腾讯文档桌面页面...")
        await page.goto('https://docs.qq.com/desktop', wait_until='domcontentloaded', timeout=60000)
        print("⏳ 等待页面完全加载...")
        await page.wait_for_timeout(20000)  # 等待20秒确保JS完全执行
        
        # 保存页面HTML
        html_content = await page.content()
        analysis_file.write_text(html_content, encoding='utf-8')
        print(f"✅ 页面HTML已保存: {analysis_file}")
        
        # 分析UI元素
        analysis_results = []
        analysis_results.append("=== 腾讯文档桌面页面UI元素分析 ===\\n")
        analysis_results.append(f"页面标题: {await page.title()}")
        analysis_results.append(f"页面URL: {page.url}")
        analysis_results.append(f"页面HTML长度: {len(html_content):,} 字符\\n")
        
        # 分析导航按钮
        analysis_results.append("=== 导航按钮分析 ===")
        nav_selectors = [
            'text=Cloud Docs', 'text=文档', 'text=我的文档', 'text=My Documents',
            '[class*="nav"]', '[class*="menu"]', '[class*="tab"]',
            'button', 'a[href]', '[role="button"]'
        ]
        
        for selector in nav_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    analysis_results.append(f"✅ {selector}: {len(elements)} 个元素")
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = await elem.inner_text()
                            if text.strip():
                                analysis_results.append(f"   {i+1}. {text.strip()[:50]}")
                        except:
                            pass
                else:
                    analysis_results.append(f"❌ {selector}: 0 个元素")
            except:
                analysis_results.append(f"⚠️  {selector}: 查询错误")
        
        analysis_results.append("\\n=== 文件列表元素分析 ===")
        file_selectors = [
            '.desktop-file-list-item', '.file-item', '.document-item',
            '.desktop-list-view-item', '[data-testid*="file"]', 
            '[class*="file"]', '[class*="doc"]', '[class*="item"]',
            '[class*="row"]', '[class*="list"]', 'tr', 'li'
        ]
        
        for selector in file_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    analysis_results.append(f"✅ {selector}: {len(elements)} 个元素")
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = await elem.inner_text()
                            if text.strip() and len(text.strip()) > 5:
                                analysis_results.append(f"   {i+1}. {text.strip()[:80]}")
                        except:
                            pass
                else:
                    analysis_results.append(f"❌ {selector}: 0 个元素")
            except:
                analysis_results.append(f"⚠️  {selector}: 查询错误")
        
        analysis_results.append("\\n=== 筛选按钮分析 ===")
        filter_selectors = [
            'text=筛选', 'text=Filter', '[class*="filter"]', 
            '.desktop-filter-button', 'button[class*="filter"]'
        ]
        
        for selector in filter_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    analysis_results.append(f"✅ {selector}: {len(elements)} 个元素")
                else:
                    analysis_results.append(f"❌ {selector}: 0 个元素")
            except:
                analysis_results.append(f"⚠️  {selector}: 查询错误")
        
        # 尝试获取页面的所有class名称
        analysis_results.append("\\n=== 页面所有CSS类名 ===")
        try:
            all_classes = await page.evaluate("""
                () => {
                    const classes = new Set();
                    const elements = document.querySelectorAll('*');
                    for (let elem of elements) {
                        if (elem.className && typeof elem.className === 'string') {
                            elem.className.split(' ').forEach(cls => {
                                if (cls.trim()) classes.add(cls.trim());
                            });
                        }
                    }
                    return Array.from(classes).sort();
                }
            """)
            
            # 过滤出可能与文档相关的类名
            doc_related_classes = []
            for cls in all_classes:
                if any(keyword in cls.lower() for keyword in ['file', 'doc', 'item', 'list', 'row', 'menu', 'nav', 'filter']):
                    doc_related_classes.append(cls)
            
            analysis_results.append(f"相关CSS类名 ({len(doc_related_classes)} 个):")
            for cls in doc_related_classes[:20]:  # 显示前20个
                analysis_results.append(f"  .{cls}")
            
        except Exception as e:
            analysis_results.append(f"获取CSS类名失败: {e}")
        
        # 保存分析结果
        selector_file.write_text('\\n'.join(analysis_results), encoding='utf-8')
        print(f"✅ UI分析结果已保存: {selector_file}")
        
        # 尝试点击导航看是否能找到文档
        print("\\n🔍 尝试导航到文档列表...")
        try:
            # 尝试点击所有可能的导航元素
            nav_candidates = await page.query_selector_all('text=Cloud Docs')
            if nav_candidates:
                print("✅ 找到Cloud Docs按钮，尝试点击...")
                await nav_candidates[0].click()
                await page.wait_for_timeout(15000)
                
                # 重新分析页面
                new_html = await page.content()
                analysis_results.append(f"\\n=== 导航后页面分析 ===")
                analysis_results.append(f"新页面URL: {page.url}")
                analysis_results.append(f"新页面标题: {await page.title()}")
                
                # 重新查找文件元素
                for selector in file_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            analysis_results.append(f"导航后 {selector}: {len(elements)} 个元素")
                            break
                    except:
                        continue
                
                # 保存导航后的页面
                nav_file = Path("/root/projects/tencent-doc-manager/enterprise_download_system/page_after_nav.html")
                nav_file.write_text(new_html, encoding='utf-8')
                print(f"✅ 导航后页面已保存: {nav_file}")
        except Exception as e:
            analysis_results.append(f"导航测试失败: {e}")
        
        # 最终保存完整分析
        selector_file.write_text('\\n'.join(analysis_results), encoding='utf-8')
        
        await browser.close()
        print("🎉 页面分析完成！")
        
        return len(analysis_results)

if __name__ == "__main__":
    try:
        result = asyncio.run(analyze_page_structure())
        print(f"\\n✅ 分析完成，共生成 {result} 行分析结果")
        print("📁 查看以下文件获取详细信息:")
        print("   - page_analysis.html (完整页面HTML)")
        print("   - ui_selectors.txt (UI元素分析)")
        print("   - page_after_nav.html (导航后页面HTML)")
    except Exception as e:
        print(f"❌ 分析失败: {e}")