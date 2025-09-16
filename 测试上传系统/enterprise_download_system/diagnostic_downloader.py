#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断版下载器 - 查看程序关闭原因
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import traceback
import sys

class DiagnosticDownloader:
    def __init__(self):
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        
        # 使用验证有效的Cookie
        self.cookie_string = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZwaEVRbVE0eVFlTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1UQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; dark_mode_setting=system"
        
        print("[SETUP] 诊断版下载器")
        print("[SETUP] 查看程序关闭原因")

    def parse_cookies(self):
        cookies = []
        for cookie_pair in self.cookie_string.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.docs.qq.com',
                    'path': '/'
                })
        return cookies

    async def check_login_status(self):
        """检查登录状态"""
        try:
            print("\n[CHECK] 检查登录状态...")
            
            # 检查页面标题
            title = await self.page.title()
            url = self.page.url
            print(f"[INFO] 页面标题: {title}")
            print(f"[INFO] 当前URL: {url}")
            
            # 检查是否有登录提示
            login_indicators = [
                'text=登录',
                'text=立即登录',
                '.login-button'
            ]
            
            login_found = False
            for indicator in login_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=2000)
                    if element:
                        login_found = True
                        print(f"[WARNING] 发现登录元素: {indicator}")
                        break
                except:
                    continue
            
            if not login_found:
                print("[OK] 登录状态正常")
                return True
            else:
                print("[ERROR] 需要重新登录")
                return False
                
        except Exception as e:
            print(f"[ERROR] 登录状态检查失败: {e}")
            return False

    async def simple_document_scan(self):
        """简单的文档扫描，不做复杂操作"""
        try:
            print("\n[SCAN] 开始简单文档扫描...")
            
            doc_selectors = [
                'a[href*="/doc/"]',
                'a[href*="/sheet/"]'
            ]
            
            all_docs = []
            
            for selector in doc_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    print(f"[SCAN] {selector}: 找到 {len(elements)} 个")
                    
                    for i, element in enumerate(elements[:5]):  # 只处理前5个
                        try:
                            href = await element.get_attribute('href')
                            if href:
                                title = await element.evaluate('el => (el.textContent || el.innerText || "").slice(0, 30)')
                                all_docs.append({
                                    'href': href,
                                    'title': title.strip(),
                                    'type': '文档' if '/doc/' in href else '表格'
                                })
                        except Exception as e:
                            print(f"[DEBUG] 元素处理异常: {e}")
                            continue
                            
                except Exception as e:
                    print(f"[DEBUG] 选择器异常: {e}")
                    continue
            
            print(f"\n[SCAN] 扫描完成，找到 {len(all_docs)} 个文档:")
            for i, doc in enumerate(all_docs, 1):
                print(f"  [{i}] {doc['type']} - {doc['title']}")
            
            return all_docs
            
        except Exception as e:
            print(f"[ERROR] 文档扫描失败: {e}")
            print(f"[ERROR] 详细错误: {traceback.format_exc()}")
            return []

    async def run_diagnostic(self):
        """运行诊断程序"""
        print("\n" + "="*50)
        print("        诊断版下载器")
        print("="*50)
        
        browser = None
        
        try:
            async with async_playwright() as playwright:
                print("[STEP 1] 启动浏览器...")
                browser = await playwright.chromium.launch(
                    headless=False,
                    args=['--start-maximized']
                )
                
                print("[STEP 2] 创建上下文...")
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    accept_downloads=True
                )
                
                print("[STEP 3] 创建页面...")
                self.page = await context.new_page()
                
                print("[STEP 4] 设置Cookie...")
                await context.add_cookies(self.parse_cookies())
                
                print("[STEP 5] 访问页面...")
                await self.page.goto('https://docs.qq.com/desktop/', 
                                    wait_until='domcontentloaded', timeout=30000)
                
                print("[SUCCESS] 页面访问成功")
                await asyncio.sleep(5)
                
                print("[STEP 6] 检查登录状态...")
                if not await self.check_login_status():
                    print("[ERROR] 登录状态异常，程序停止")
                    return False
                
                print("[STEP 7] 简单文档扫描...")
                documents = await self.simple_document_scan()
                
                if documents:
                    print(f"[SUCCESS] 找到 {len(documents)} 个文档")
                else:
                    print("[WARNING] 未找到文档")
                
                print("[STEP 8] 保持浏览器60秒...")
                await asyncio.sleep(60)
                
                return True
                
        except Exception as e:
            print(f"\n[CRITICAL ERROR] 程序执行失败:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误消息: {str(e)}")
            print(f"详细堆栈:")
            print(traceback.format_exc())
            return False
            
        finally:
            try:
                if browser:
                    print("[CLEANUP] 关闭浏览器...")
                    await browser.close()
            except Exception as e:
                print(f"[CLEANUP ERROR] 关闭浏览器失败: {e}")

async def main():
    try:
        downloader = DiagnosticDownloader()
        success = await downloader.run_diagnostic()
        
        if success:
            print("\n[SUCCESS] 诊断完成")
        else:
            print("\n[FAILED] 诊断失败")
            
    except Exception as e:
        print(f"\n[MAIN ERROR] 主程序异常: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断程序")
    except Exception as e:
        print(f"\n[FATAL ERROR] 程序崩溃: {e}")
        print(traceback.format_exc())