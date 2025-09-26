#!/usr/bin/env python3
"""
真实上传流程测试脚本
严格按照用户提供的手动上传步骤执行
验证上传是否真正成功
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Response
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealUploadTester:
    """真实上传流程测试器"""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.captured_urls = []
        self.upload_response = None

    async def __aenter__(self):
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    async def setup(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        )
        self.page = await self.context.new_page()

        # 监听网络响应
        self.page.on('response', self.handle_response)

        logger.info("✅ 浏览器已启动")

    async def handle_response(self, response: Response):
        """捕获上传相关的网络响应"""
        url = response.url

        # 捕获上传API响应
        if any(keyword in url for keyword in ['/import/', '/upload/', '/sheet/', '/doc/']):
            try:
                if response.status == 200:
                    # 尝试获取响应内容
                    if 'json' in response.headers.get('content-type', ''):
                        json_data = await response.json()
                        if 'url' in str(json_data) or 'docUrl' in str(json_data):
                            self.upload_response = json_data
                            logger.info(f"📡 捕获上传响应: {json_data}")

                    # 捕获新文档URL
                    if '/sheet/' in url or '/doc/' in url:
                        self.captured_urls.append(url)
                        logger.info(f"📡 捕获文档URL: {url}")
            except:
                pass

    def parse_cookie_string(self, cookie_string: str) -> list:
        """解析Cookie字符串 - 使用正确的分隔符"""
        cookies = []

        # 重要：使用 '; ' 分隔（分号后有空格）
        for cookie_pair in cookie_string.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.strip().split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.qq.com',  # 注意：使用.qq.com而非.docs.qq.com
                    'path': '/'
                })

        logger.info(f"✅ 解析了 {len(cookies)} 个Cookie项")
        return cookies

    async def login_with_cookies(self, cookie_string: str) -> bool:
        """使用Cookie登录"""
        logger.info("🔐 开始Cookie登录...")

        try:
            # 解析并添加Cookie
            cookies = self.parse_cookie_string(cookie_string)
            await self.context.add_cookies(cookies)
            logger.info(f"✅ 已添加 {len(cookies)} 个Cookies")

            # 步骤1：使用cookie打开账户首页
            logger.info("📄 访问腾讯文档首页...")
            await self.page.goto('https://docs.qq.com/', wait_until='networkidle')
            await self.page.wait_for_timeout(3000)

            # 然后访问desktop页面
            logger.info("📄 访问desktop页面...")
            await self.page.goto('https://docs.qq.com/desktop/', wait_until='networkidle')
            await self.page.wait_for_timeout(3000)

            # 验证登录状态
            login_btn = await self.page.query_selector('button:has-text("登录")')
            import_btn = await self.page.query_selector('button.desktop-import-button-pc')

            if login_btn:
                logger.error("❌ 发现登录按钮，Cookie可能已失效")
                return False

            if import_btn:
                logger.info("✅ 找到导入按钮，登录成功")
                return True
            else:
                logger.warning("⚠️ 未找到导入按钮，尝试等待...")
                await self.page.wait_for_timeout(2000)
                import_btn = await self.page.query_selector('button.desktop-import-button-pc')
                return import_btn is not None

        except Exception as e:
            logger.error(f"❌ 登录失败: {e}")
            return False

    async def upload_file_real_process(self, file_path: str) -> dict:
        """按照真实步骤上传文件"""
        result = {
            'success': False,
            'url': None,
            'method': None,
            'captured_urls': [],
            'message': ''
        }

        try:
            file_name = Path(file_path).name
            logger.info(f"📤 开始上传: {file_name}")

            # 步骤2：点击导入按钮
            logger.info("🔍 查找导入按钮...")

            # 使用多个选择器尝试
            import_selectors = [
                'button.desktop-import-button-pc',  # 用户提供的选择器
                '#root > div.desktop-layout-pc.desktop-dropdown-container.desktop-skin-default > div.desktop-layout-inner-pc > div > nav > button.desktop-import-button-pc',  # 完整路径
                'nav button:has(i.desktop-icon-import)',  # 图标选择器
            ]

            import_btn = None
            for selector in import_selectors:
                import_btn = await self.page.query_selector(selector)
                if import_btn:
                    logger.info(f"✅ 找到导入按钮: {selector}")
                    break

            if not import_btn:
                result['message'] = "找不到导入按钮"
                logger.error("❌ 找不到导入按钮")
                return result

            # 准备文件选择
            logger.info("📁 准备文件选择...")

            # 方法1：使用filechooser（推荐）
            try:
                async with self.page.expect_file_chooser(timeout=5000) as fc_info:
                    await import_btn.click()
                    logger.info("✅ 点击导入按钮")
                file_chooser = await fc_info.value
                await file_chooser.set_files(file_path)
                logger.info(f"✅ 已选择文件: {file_path}")
                result['method'] = 'filechooser'
            except:
                # 方法2：直接设置input
                logger.info("尝试直接设置input元素...")
                await import_btn.click()
                await self.page.wait_for_timeout(1000)

                file_inputs = await self.page.query_selector_all('input[type="file"]')
                if file_inputs:
                    await file_inputs[-1].set_input_files(file_path)
                    logger.info("✅ 通过input设置文件")
                    result['method'] = 'input'
                else:
                    result['message'] = "无法设置文件"
                    return result

            # 等待弹窗出现
            await self.page.wait_for_timeout(2000)

            # 步骤3：查找并点击确定按钮
            logger.info("🔍 查找确定按钮...")

            # 确定按钮的多个选择器
            confirm_selectors = [
                'button.dui-button-type-primary:has-text("确定")',
                '.import-kit-import-file-footer button.dui-button-type-primary',
                'div.dui-button-container:has-text("确定")',
                # 用户提供的选择器
                'body > div.dui-modal-mask.dui-modal-mask-visible.dui-modal-mask-display > div > div.dui-modal-content > div > div.import-kit-import-file-footer > div:nth-child(2) > button.dui-button.dui-button-type-primary.dui-button-size-default > div'
            ]

            confirm_btn = None
            for selector in confirm_selectors:
                try:
                    confirm_btn = await self.page.wait_for_selector(selector, timeout=3000)
                    if confirm_btn:
                        logger.info(f"✅ 找到确定按钮: {selector}")
                        break
                except:
                    continue

            if confirm_btn:
                await confirm_btn.click()
                logger.info("✅ 点击确定按钮")
            else:
                # 尝试按Enter键
                await self.page.keyboard.press('Enter')
                logger.info("⌨️ 发送Enter键")

            # 步骤4：等待上传完成
            logger.info("⏳ 等待上传完成...")

            # 监控上传状态
            upload_complete = False
            start_time = time.time()
            timeout = 60  # 60秒超时

            while time.time() - start_time < timeout:
                await self.page.wait_for_timeout(2000)

                # 检查导入对话框是否关闭
                import_dialog = await self.page.query_selector('.import-kit-import-file')
                if not import_dialog:
                    logger.info("✅ 导入对话框已关闭")
                    upload_complete = True
                    break

                # 检查进度提示
                progress = await self.page.query_selector('.import-kit-import-progress')
                if progress:
                    progress_text = await progress.inner_text()
                    logger.info(f"📊 上传进度: {progress_text}")

                # 检查成功消息
                success_msg = await self.page.query_selector('.dui-message-success')
                if success_msg:
                    logger.info("✅ 检测到成功消息")
                    upload_complete = True
                    break

            if not upload_complete:
                logger.warning("⚠️ 上传超时")
                result['message'] = "上传超时"
                return result

            # 获取新文档URL
            await self.page.wait_for_timeout(3000)

            # 策略1：从捕获的网络响应获取
            if self.upload_response:
                logger.info(f"📡 从网络响应获取: {self.upload_response}")
                if 'url' in self.upload_response:
                    result['url'] = self.upload_response['url']
                    result['success'] = True
                    result['method'] = 'network_response'

            # 策略2：从DOM中查找新文档
            if not result['url']:
                logger.info("🔍 从DOM查找新文档...")

                # 查找所有文档链接
                doc_links = await self.page.query_selector_all('a[href*="/sheet/"], a[href*="/doc/"]')

                if doc_links:
                    # 查找包含文件名的链接
                    file_name_base = Path(file_path).stem

                    for link in doc_links:
                        link_text = await link.inner_text()
                        href = await link.get_attribute('href')

                        # 检查文件名匹配
                        if file_name_base in link_text or '测试版本' in link_text:
                            full_url = f"https://docs.qq.com{href}" if href.startswith('/') else href
                            logger.info(f"✅ 找到匹配文档: {link_text} -> {full_url}")
                            result['url'] = full_url
                            result['success'] = True
                            result['method'] = 'dom_match'
                            break

                    # 如果没有匹配，取最后一个（可能是新上传的）
                    if not result['url'] and doc_links:
                        last_link = doc_links[-1]
                        href = await last_link.get_attribute('href')
                        full_url = f"https://docs.qq.com{href}" if href.startswith('/') else href
                        logger.warning(f"⚠️ 使用最后一个链接（可能不准确）: {full_url}")
                        result['url'] = full_url
                        result['success'] = False  # 标记为不确定
                        result['method'] = 'last_link_guess'

            # 记录所有捕获的URL
            result['captured_urls'] = self.captured_urls

            if result['success']:
                logger.info(f"✅ 上传成功: {result['url']}")
                result['message'] = f"上传成功（{result['method']}）"
            else:
                logger.warning(f"⚠️ 上传可能失败或URL不确定")
                result['message'] = "上传完成但URL不确定"

        except Exception as e:
            logger.error(f"❌ 上传过程出错: {e}")
            result['message'] = f"上传失败: {str(e)}"

        return result

    async def verify_upload_real(self, doc_url: str, file_name: str) -> bool:
        """验证上传是否真实成功"""
        try:
            logger.info(f"🔍 验证文档URL: {doc_url}")

            # 访问文档URL
            await self.page.goto(doc_url, wait_until='networkidle')
            await self.page.wait_for_timeout(3000)

            # 检查页面标题
            title = await self.page.title()
            logger.info(f"📄 页面标题: {title}")

            # 检查是否包含文件名相关内容
            file_name_base = Path(file_name).stem

            # 检查文档名
            doc_name_elem = await self.page.query_selector('.doc-title, .sheet-name, h1')
            if doc_name_elem:
                doc_name = await doc_name_elem.inner_text()
                logger.info(f"📄 文档名: {doc_name}")

                if file_name_base in doc_name or '测试版本' in doc_name:
                    logger.info("✅ 文档名匹配，上传真实成功")
                    return True

            # 检查是否是空文档
            cells = await self.page.query_selector_all('.cell-content, .luckysheet-cell')
            if len(cells) > 0:
                logger.info(f"📊 文档包含 {len(cells)} 个单元格")
                return True
            else:
                logger.warning("⚠️ 文档可能为空")
                return False

        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("🔚 资源已清理")


async def main():
    """主测试流程"""

    print("="*60)
    print("📋 真实上传流程测试")
    print("="*60)

    # 读取Cookie
    cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
    with open(cookie_file) as f:
        cookie_data = json.load(f)

    cookie_string = cookie_data.get('current_cookies', '')
    last_update = cookie_data.get('last_update', 'Unknown')

    print(f"📅 Cookie最后更新: {last_update}")

    # 计算Cookie年龄
    if last_update != 'Unknown':
        update_time = datetime.fromisoformat(last_update)
        age_days = (datetime.now() - update_time).days
        print(f"⏰ Cookie年龄: {age_days}天")

        if age_days > 7:
            print("⚠️ 警告: Cookie已超过7天，可能需要更新")

    # 查找最新的涂色Excel文件
    excel_files = list(Path('/root/projects/tencent-doc-manager/excel_outputs/marked').glob('*.xlsx'))

    if not excel_files:
        print("❌ 没有找到可上传的Excel文件")
        return

    # 选择最新的文件
    latest_file = max(excel_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 选择文件: {latest_file.name}")
    print(f"📏 文件大小: {latest_file.stat().st_size:,} bytes")

    # 执行测试
    async with RealUploadTester(headless=True) as tester:
        # 登录
        login_success = await tester.login_with_cookies(cookie_string)

        if not login_success:
            print("❌ 登录失败，请更新Cookie")
            return

        # 上传文件
        print("\n" + "="*60)
        print("🚀 开始上传测试...")
        print("="*60)

        result = await tester.upload_file_real_process(str(latest_file))

        # 显示结果
        print("\n" + "="*60)
        print("📊 上传结果")
        print("="*60)
        print(f"成功: {result['success']}")
        print(f"URL: {result['url']}")
        print(f"方法: {result['method']}")
        print(f"消息: {result['message']}")

        if result['captured_urls']:
            print(f"捕获的URL: {result['captured_urls']}")

        # 验证上传
        if result['url']:
            print("\n" + "="*60)
            print("🔍 验证上传真实性...")
            print("="*60)

            is_real = await tester.verify_upload_real(result['url'], latest_file.name)

            if is_real:
                print("✅ 验证通过：上传是真实的！")
            else:
                print("❌ 验证失败：上传可能不是真实的")

        # 最终结论
        print("\n" + "="*60)
        print("🎯 最终结论")
        print("="*60)

        if result['success'] and result['method'] in ['network_response', 'dom_match']:
            print("✅ 上传真实成功")
            print(f"📄 文档URL: {result['url']}")
        elif result['url'] and result['method'] == 'last_link_guess':
            print("⚠️ 上传可能成功，但URL不确定")
            print("建议：手动检查腾讯文档确认")
        else:
            print("❌ 上传失败")
            print("可能原因：")
            print("1. Cookie权限不足")
            print("2. 文件格式问题")
            print("3. 网络问题")


if __name__ == "__main__":
    asyncio.run(main())