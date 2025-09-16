#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用最新有效Cookie的下载器
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

class UpdatedDownloader:
    def __init__(self):
        self.download_dir = Path("./downloads").resolve()
        self.download_dir.mkdir(exist_ok=True)
        
        # 🔥 使用你提供的最新有效Cookie
        self.cookie_string = "fingerprint=e979148633684123810b8625c5e988b082; low_login_enable=1; RK=MA/9rNDTsw; ptcz=af0b3d4029bba7dffa892366ad18dd8f4ff5aa12bc499e7dd00e3247fed6cbba; DOC_QQ_APPID=101458937; polish_tooltip=true; pgv_pvid=1277470832102926; _qimei_uuid42=1960c092216100a0a13d2af50c259fa2bbe9316a3d; _qimei_h38=8213826aa13d2af50c259fa202000009a1960c; _qimei_fingerprint=cb237a82a78862fdd0ebd18db76ab2f8; adtag=s_pcqq_liaotianjilu; _clck=3990794656|1|fwy|0; loginTime=1754640043257; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; traceid=a473487816; TOK=a473487816963a48; hashkey=a4734878; dark_mode_setting=system; optimal_cdn_domain=docs.qq.com; ES2=f88c0411768984b9; _qpsvr_localtk=0.5895351222297797; uid=144115414584628119; uid_key=EOP1mMQHGiwvK2JLYUhONDRwZGVVWllDbjI4SzdDQnE0TW8vWGRIaWlmalV3SlorUDZJPSKBAmV5SmhiR2NpT2lKQlEwTkJURWNpTENKMGVYQWlPaUpLVjFRaWZRLmV5SlVhVzU1U1VRaU9pSXhORFF4TVRVME1UUTFPRFEyTWpneE1Ua2lMQ0pXWlhJaU9pSXhJaXdpUkc5dFlXbHVJam9pYzJGaGMxOTBiMk1pTENKU1ppSTZJbEZLVWtoWFp5SXNJbVY0Y0NJNk1UYzFPREU1TXprMk9Td2lhV0YwSWpveE56VTFOakF4T1RZNUxDSnBjM01pT2lKVVpXNWpaVzUwSUVSdlkzTWlmUS55Wjg2RzlDaTczekRGeUZuZUlLSkhIUjZBaktQQVFocTZOUm9WdFRfWWJzKLHSr8YGMAE4%2BcewMEIgMTM4RUE5QjgwN0I2QzJEQ0ZFOTZDNUIxQTY1MEU5MzI%3D; utype=qq; env_id=gray-pct25; gray_user=true; DOC_SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; SID=ec95c29d7ca948298ae4869ccdf3d6ac7946c1ae31ef4454b25c723572b0051b; language=zh-CN; backup_cdn_domain=docs.gtimg.com"
        
        self.downloaded_files = []
        print("[SETUP] 使用最新有效Cookie - uid: 144115414584628119")
        print("[SETUP] 下载目录:", str(self.download_dir))

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

    async def handle_download(self, download):
        try:
            filename = download.suggested_filename
            download_path = self.download_dir / filename
            print(f"[DOWN] 下载: {filename}")
            await download.save_as(download_path)
            self.downloaded_files.append(str(download_path))
            file_size = download_path.stat().st_size if download_path.exists() else 0
            print(f"[OK] 完成: {filename} ({file_size:,} 字节)")
        except Exception as e:
            print(f"[ERROR] 下载失败: {e}")

    async def verify_cookie_works(self):
        """验证新Cookie是否有效"""
        print("\n[VERIFY] 验证Cookie有效性...")
        
        try:
            # 测试用户信息接口
            response = await self.page.goto(
                'https://docs.qq.com/cgi-bin/online_docs/user_info?xsrf=a473487816963a48&get_vip_info=1&u=',
                wait_until='domcontentloaded',
                timeout=15000
            )
            
            print(f"[API] user_info状态码: {response.status}")
            
            if response.status == 200:
                content = await self.page.content()
                if 'login' not in content.lower() and '登录' not in content:
                    print("[SUCCESS] Cookie验证成功！用户已认证")
                    return True
                else:
                    print("[ERROR] Cookie无效，仍需登录")
                    return False
            else:
                print(f"[ERROR] API调用失败: {response.status}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Cookie验证异常: {e}")
            return False

    async def navigate_to_documents(self):
        """导航到文档页面"""
        print("\n[STEP] 访问腾讯文档桌面...")
        
        try:
            # 访问桌面页面
            await self.page.goto('https://docs.qq.com/desktop/', 
                                wait_until='domcontentloaded', timeout=30000)
            
            print("[PAGE] 桌面页面加载完成")
            await asyncio.sleep(5)  # 等待页面完全加载
            
            # 检查页面状态
            title = await self.page.title()
            print(f"[PAGE] 标题: {title}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 页面导航失败: {e}")
            return False

    async def find_and_download_documents(self, max_count=10):
        """查找并下载文档"""
        print(f"\n[STEP] 查找并下载最多{max_count}个文档...")
        
        # 等待页面元素加载
        await asyncio.sleep(8)
        
        # 多种文档选择器策略
        document_selectors = [
            'a[href*="/doc/"]',           # 文档链接
            '[class*="file-item"]',        # 文件项
            '[class*="document-item"]',    # 文档项
            '.file-name',                  # 文件名
            '[data-test*="file"]',         # 测试属性
            'tr[class*="file"]',           # 表格行
            '[role="listitem"]',           # 列表项
            '[class*="item"]:has(a[href*="/doc/"])'  # 包含文档链接的项目
        ]
        
        found_docs = []
        
        for selector in document_selectors:
            try:
                print(f"[SEARCH] 尝试选择器: {selector}")
                elements = await self.page.query_selector_all(selector)
                
                if elements:
                    print(f"[FOUND] {selector}: 找到{len(elements)}个元素")
                    
                    for i, element in enumerate(elements[:max_count]):
                        try:
                            # 获取文本内容
                            text = await element.inner_text()
                            if text and len(text.strip()) > 0:
                                found_docs.append((element, text.strip()))
                                print(f"  [DOC {len(found_docs)}] {text[:50]}...")
                                
                        except Exception as e:
                            print(f"  [SKIP] 元素{i}获取文本失败: {e}")
                    
                    if found_docs:
                        break  # 找到文档就停止搜索其他选择器
                        
            except Exception as e:
                print(f"[SKIP] {selector} 搜索失败: {e}")
        
        if not found_docs:
            print("[ERROR] 未找到任何文档元素")
            return []
        
        print(f"\n[START] 开始下载{len(found_docs)}个文档...")
        downloaded_count = 0
        
        for i, (element, doc_name) in enumerate(found_docs):
            try:
                print(f"\n[DOC {i+1}/{len(found_docs)}] 下载: {doc_name[:30]}...")
                
                # 滚动到元素可见位置
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # 右键点击
                await element.click(button='right')
                await asyncio.sleep(2)
                
                # 查找下载选项
                download_options = ['text=下载', 'text=导出', 'text=Download', 'text=Export']
                
                download_success = False
                for option in download_options:
                    try:
                        download_btn = await self.page.wait_for_selector(option, timeout=3000)
                        if download_btn:
                            await download_btn.click()
                            print(f"[CLICK] 点击: {option}")
                            download_success = True
                            downloaded_count += 1
                            await asyncio.sleep(3)  # 等待下载开始
                            break
                    except:
                        continue
                
                if not download_success:
                    print(f"[MISS] 未找到下载选项")
                
                # 点击空白处关闭右键菜单
                try:
                    await self.page.click('body', position={'x': 100, 'y': 100})
                    await asyncio.sleep(1)
                except:
                    pass
                    
            except Exception as e:
                print(f"[ERROR] 文档{i+1}处理失败: {e}")
        
        return downloaded_count

    async def run_download_task(self):
        """执行下载任务"""
        print("\n" + "="*60)
        print("        腾讯文档自动化下载 - 使用最新有效Cookie")
        print("="*60)
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,  # 可视化模式
                args=['--start-maximized', '--no-sandbox']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                accept_downloads=True
            )
            
            # 监听下载
            context.on('download', self.handle_download)
            
            self.page = await context.new_page()
            
            try:
                # 1. 设置Cookie
                print("[SETUP] 设置Cookie...")
                await context.add_cookies(self.parse_cookies())
                
                # 2. 先导航到文档页面
                if not await self.navigate_to_documents():
                    print("[FAILED] 页面导航失败")
                    return False
                
                # 3. 在文档页面验证登录状态
                print("[INFO] 在桌面页面检查登录状态...")
                
                # 4. 查找并下载文档
                downloaded_count = await self.find_and_download_documents(10)
                
                # 5. 等待下载完成
                print(f"\n[WAIT] 等待所有下载完成...")
                await asyncio.sleep(10)
                
                print(f"\n[RESULT] 任务完成!")
                print(f"[STATS] 尝试下载: {downloaded_count} 个文档")
                print(f"[STATS] 实际下载: {len(self.downloaded_files)} 个文件")
                
                for file_path in self.downloaded_files:
                    print(f"  - {file_path}")
                
                return True
                
            except Exception as e:
                print(f"[ERROR] 执行异常: {e}")
                return False
                
            finally:
                print("\n[WAIT] 保持浏览器10秒供观察...")
                await asyncio.sleep(10)
                await browser.close()

async def main():
    downloader = UpdatedDownloader()
    success = await downloader.run_download_task()
    
    if success:
        print("\n[SUCCESS] 任务执行成功！")
    else:
        print("\n[FAILED] 任务执行失败")

if __name__ == "__main__":
    asyncio.run(main())