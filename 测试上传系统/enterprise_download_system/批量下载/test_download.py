#!/usr/bin/env python3
"""
自动测试下载器 - 使用指定Cookie下载10个文档
"""

import asyncio
import sys
from downloader import TencentDocDownloader

async def test_download_10_files():
    """测试下载10个文档"""
    
    # 使用用户提供的Cookie
    test_cookie = "RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; low_login_enable=1; pgv_pvid=2105700616; adtag=tdocs; polish_tooltip=true; backup_cdn_domain=docs.gtimg.com; yyb_muid=3A4651960B836983251B45FD0A5C683E; dark_mode_setting=system; optimal_cdn_domain=docs2.gtimg.com; uid=144115414584628119; utype=qq; DOC_QQ_APPID=101458937; DOC_QQ_OPENID=138EA9B807B6C2DCFE96C5B1A650E932; env_id=gray-pct25; gray_user=true; DOC_SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; SID=89f6e6a637c54775a50b132cf3958837accebd74c8d84e798619bcfb0eee9b64; traceid=25ea7d9ac7; TOK=25ea7d9ac7e65c7d; hashkey=25ea7d9a; fingerprint=cfe08ff9e3d948feb374ee3861bc221f98; language=zh-CN; uid_key=EOP1mMQHGjBEdVk5S0xhL1lLT3ZwaEVRbVE0eVElTWt2cHFzWnRiSjZVczZSSGVyZENaT2Z3PT0igQJleUpoYkdjaU9pSkJRME5CVEVjaUxDSjBlWEFpT2lKS1YxUWlmUS5leUpVYVc1NVNVUWlPaUl4TkRReE1UVTBNVFExT0RRMk1qZ3hNVGtpTENKV1pYSWlPaUl4SWl3aVJHOXRZV2x1SWpvaWMyRmhjMTkwYjJNaUxDSlNaaUk2SWtab1VsUnhkU0lzSW1WNGNDSTZNVGMxT0RJMU1EQTRPQ3dpYVdGMElqb3hOelUxTmpVNU1EZzRMQ0pwYzNNaU9pSlVaVzVqWlc1MElFUnZZM01pZlEuSzV6Rlk3X0FJYi1fUzY3ekRpdTBsNEtXV2RkMGN0SUFVZy1DR0VLZmJ6TSjQkLPGBjABOPnHsDBCIDEzOEVBOUI4MDdCNkMyRENGRTk2QzVCMUE2NTBFOTMySMHYw8QG; loginTime=1755664608597; adtag=tdocs"
    
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                  测试下载10个文档 - 自动化测试                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # 创建修改版的下载器，限制为10个文档
    class TestDownloader(TencentDocDownloader):
        async def download_limited_files(self, limit=10):
            """下载限制数量的文档"""
            print("🎯 开始下载前10个文档...")
            
            try:
                # 查找所有文件行
                file_selectors = [
                    '.desktop-file-list-item',
                    '.file-item',
                    '.document-item',
                    '[data-testid*="file"]',
                    '.desktop-list-view-item'
                ]
                
                file_elements = []
                for selector in file_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if elements:
                            file_elements = elements
                            print(f"✅ 使用选择器 {selector}，找到 {len(elements)} 个文件")
                            break
                    except:
                        continue
                
                if not file_elements:
                    print("❌ 未找到文件元素，可能页面结构已变化")
                    return
                
                # 限制下载数量
                files_to_download = file_elements[:limit]
                print(f"🚀 准备下载前 {len(files_to_download)} 个文件...")
                
                successful_downloads = 0
                skipped_files = 0
                
                for i, file_element in enumerate(files_to_download):
                    try:
                        print(f"\n📄 处理第 {i + 1}/{len(files_to_download)} 个文件...")
                        
                        # 获取文件名（用于日志）
                        try:
                            file_name = await file_element.inner_text()
                            if file_name:
                                file_name = file_name.replace('\n', ' ')[:50]
                                print(f"📝 文件: {file_name}...")
                        except:
                            print(f"📝 文件: [第{i + 1}个]")
                        
                        # 滚动到元素位置
                        await file_element.scroll_into_view_if_needed()
                        await self.page.wait_for_timeout(500)
                        
                        # 右键点击元素
                        await file_element.click(button='right')
                        print("🖱️  已右键点击")
                        
                        # 等待菜单出现
                        await self.page.wait_for_timeout(1500)
                        
                        # 查找下载选项
                        download_selectors = [
                            'text=下载',
                            '.desktop-menu-item-content:has-text("下载")',
                            '[data-testid*="download"]',
                            '.menu-item:has-text("下载")',
                            '.context-menu-item:has-text("下载")'
                        ]
                        
                        download_clicked = False
                        for selector in download_selectors:
                            try:
                                download_element = await self.page.wait_for_selector(selector, timeout=3000)
                                if download_element:
                                    await download_element.click()
                                    print("✅ 已点击下载")
                                    download_clicked = True
                                    successful_downloads += 1
                                    break
                            except:
                                continue
                        
                        if not download_clicked:
                            print("⚠️  未找到下载选项（可能是智能表格等不支持下载的类型）")
                            skipped_files += 1
                            # 点击其他地方关闭菜单
                            try:
                                await self.page.click('body')
                            except:
                                pass
                        
                        # 等待下载开始或菜单消失
                        await self.page.wait_for_timeout(2000)
                        
                        # 处理可能的浏览器下载确认对话框
                        try:
                            # 如果出现"此网站想要下载多个文件"的提示，点击允许
                            await self.page.click('text=允许', timeout=1000)
                            print("✅ 已允许下载")
                        except:
                            pass  # 没有对话框，继续
                        
                    except Exception as e:
                        print(f"❌ 下载第 {i + 1} 个文件失败: {e}")
                        skipped_files += 1
                        continue
                
                print(f"\n🎉 测试下载完成！")
                print(f"✅ 成功处理: {successful_downloads} 个文件")
                print(f"⚠️  跳过文件: {skipped_files} 个文件（无下载按钮或错误）")
                print(f"📁 文件保存在: {self.download_dir}")
                        
            except Exception as e:
                print(f"❌ 批量下载过程出错: {e}")

        async def run_test(self):
            """运行测试流程"""
            try:
                # 1. 设置浏览器
                await self.setup_browser()
                
                # 2. 验证Cookie
                if not await self.validate_cookie():
                    print("❌ Cookie验证失败，停止测试")
                    return False
                
                # 3. 设置筛选条件
                await self.setup_filters()
                
                # 4. 滚动加载所有文件
                file_count = await self.load_all_files()
                if file_count == 0:
                    print("⚠️  未找到任何文件")
                    return False
                
                # 5. 下载前10个文件
                await self.download_limited_files(10)
                
                return True
                
            except Exception as e:
                print(f"❌ 测试过程出错: {e}")
                return False
            
            finally:
                if self.browser:
                    await self.browser.close()
                    print("🔚 浏览器已关闭")

    # 创建测试下载器并运行
    downloader = TestDownloader()
    downloader.cookie_string = test_cookie
    
    success = await downloader.run_test()
    
    if success:
        print("\n🎉 测试完成！检查downloads目录查看下载的文件")
    else:
        print("\n❌ 测试失败！")

if __name__ == "__main__":
    try:
        asyncio.run(test_download_10_files())
    except KeyboardInterrupt:
        print("\n\n👋 测试被中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")