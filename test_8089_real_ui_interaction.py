#!/usr/bin/env python3
"""
真实的8089监控UI完整交互测试
必须通过UI操作，观察完整工作流
严禁任何虚拟或欺诈内容
"""

import asyncio
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Real8089UITest:
    """真实的8089 UI交互测试"""

    def __init__(self):
        self.base_dir = Path('/root/projects/tencent-doc-manager')
        self.ui_url = 'http://localhost:8089'
        self.results = {}

    async def run_test(self):
        """执行完整的UI交互测试"""
        logger.info("=" * 70)
        logger.info("🚀 开始真实的8089监控UI交互测试")
        logger.info("📍 目标：点击监控设置的立即刷新按钮，观察全链路执行")
        logger.info("=" * 70)

        async with async_playwright() as p:
            # 启动浏览器（headless=True用于服务器环境）
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            # 监听网络请求，观察真实的API调用
            api_calls = []
            async def log_request(request):
                if 'api' in request.url:
                    api_calls.append({
                        'url': request.url,
                        'method': request.method,
                        'time': datetime.now().isoformat()
                    })
                    logger.info(f"🔍 API调用: {request.method} {request.url}")

            page.on('request', log_request)

            try:
                # Step 1: 访问8089监控页面
                logger.info("📍 Step 1: 访问8089监控页面")
                await page.goto(self.ui_url)
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                logger.info("✅ 页面加载完成")

                # 截图记录初始状态
                await page.screenshot(path=f"{self.base_dir}/test_results/8089_initial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

                # Step 2: 点击监控设置标签
                logger.info("📍 Step 2: 查找并点击监控设置标签")
                monitor_tab_selectors = [
                    'text="监控设置"',
                    '//button[contains(text(), "监控设置")]',
                    '//div[contains(text(), "监控设置")]',
                    '[role="tab"]:has-text("监控设置")',
                    '.tab-monitor-settings'
                ]

                monitor_tab_clicked = False
                for selector in monitor_tab_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible():
                            await element.click()
                            monitor_tab_clicked = True
                            logger.info(f"✅ 成功点击监控设置标签: {selector}")
                            await asyncio.sleep(2)
                            break
                    except:
                        continue

                if not monitor_tab_clicked:
                    logger.error("❌ 未找到监控设置标签")
                    # 尝试直接访问监控设置页面
                    logger.info("尝试直接访问监控设置URL")
                    await page.goto(f"{self.ui_url}/#monitor-settings")
                    await asyncio.sleep(2)

                # Step 3: 检查页面上现有的URL配置
                logger.info("📍 Step 3: 检查页面上的URL和Cookie配置")

                # 查找URL输入框
                url_input_selectors = [
                    'input[placeholder*="腾讯文档"]',
                    'input[placeholder*="URL"]',
                    'input[placeholder*="链接"]',
                    'input.url-input',
                    '#url-input'
                ]

                url_value = None
                for selector in url_input_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible():
                            url_value = await element.input_value()
                            if url_value:
                                logger.info(f"✅ 发现URL配置: {url_value}")
                                break
                    except:
                        continue

                # 如果没有URL，输入一个测试URL
                if not url_value:
                    logger.info("⚠️ 未发现URL配置，输入测试URL")
                    test_url = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"
                    for selector in url_input_selectors:
                        try:
                            element = page.locator(selector).first
                            if await element.is_visible():
                                await element.fill(test_url)
                                url_value = test_url
                                logger.info(f"✅ 输入测试URL: {test_url}")
                                break
                        except:
                            continue

                # Step 4: 查找并点击立即刷新按钮
                logger.info("📍 Step 4: 查找并点击立即刷新按钮")

                refresh_button_selectors = [
                    'button:text-is("立即刷新")',
                    'button:has-text("立即刷新")',
                    '//button[text()="立即刷新"]',
                    '//button[contains(., "立即刷新")]',
                    'button.refresh-btn',
                    'button[class*="refresh"]',
                    '#refresh-button',
                    '[data-action="refresh"]'
                ]

                refresh_clicked = False
                for selector in refresh_button_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible():
                            # 记录按钮位置
                            box = await element.bounding_box()
                            logger.info(f"📍 找到按钮位置: x={box['x']}, y={box['y']}")

                            # 截图按钮
                            await page.screenshot(
                                path=f"{self.base_dir}/test_results/8089_before_click_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            )

                            # 点击按钮
                            await element.click()
                            refresh_clicked = True
                            logger.info(f"✅ 成功点击立即刷新按钮: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"选择器 {selector} 失败: {e}")
                        continue

                if not refresh_clicked:
                    logger.error("❌ 未找到立即刷新按钮")
                    # 列出页面上所有按钮
                    all_buttons = await page.locator('button').all()
                    logger.info(f"页面上共有 {len(all_buttons)} 个按钮:")
                    for i, btn in enumerate(all_buttons[:10]):
                        try:
                            text = await btn.text_content()
                            if text:
                                logger.info(f"  按钮{i+1}: {text.strip()}")
                        except:
                            pass
                    return None

                # Step 5: 观察全链路执行过程
                logger.info("📍 Step 5: 观察全链路执行过程")
                logger.info("⏳ 等待系统处理...")

                # 监控页面变化和状态更新
                start_time = time.time()
                max_wait = 120  # 最多等待2分钟

                # 查找可能的进度指示器
                progress_selectors = [
                    'text="正在下载"',
                    'text="正在处理"',
                    'text="正在对比"',
                    'text="正在打分"',
                    'text="正在上传"',
                    'text="处理中"',
                    '.progress',
                    '.loading',
                    '[class*="spinner"]'
                ]

                processing_observed = False
                while time.time() - start_time < max_wait:
                    # 检查进度状态
                    for selector in progress_selectors:
                        try:
                            element = page.locator(selector).first
                            if await element.is_visible():
                                text = await element.text_content()
                                logger.info(f"🔄 处理状态: {text}")
                                processing_observed = True
                                break
                        except:
                            pass

                    # 检查是否完成
                    completion_selectors = [
                        'text="处理完成"',
                        'text="上传成功"',
                        'a[href*="docs.qq.com"]',
                        '.success-message',
                        '.result-url'
                    ]

                    for selector in completion_selectors:
                        try:
                            element = page.locator(selector).first
                            if await element.is_visible():
                                logger.info(f"✅ 发现完成标志: {selector}")

                                # 查找返回的URL
                                url_element = page.locator('a[href*="docs.qq.com"]').first
                                if await url_element.is_visible():
                                    final_url = await url_element.get_attribute('href')
                                    logger.info(f"🔗 发现最终URL: {final_url}")
                                    self.results['final_url'] = final_url

                                    # 截图最终状态
                                    await page.screenshot(
                                        path=f"{self.base_dir}/test_results/8089_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                    )
                                    return final_url
                        except:
                            pass

                    await asyncio.sleep(2)

                # Step 6: 检查API调用记录
                logger.info("📍 Step 6: 检查API调用记录")
                if api_calls:
                    logger.info(f"共记录到 {len(api_calls)} 个API调用:")
                    for call in api_calls:
                        logger.info(f"  - {call['method']} {call['url']}")

                # Step 7: 检查是否有综合打分文件生成
                logger.info("📍 Step 7: 检查综合打分文件")
                scoring_dir = self.base_dir / 'scoring_results/comprehensive'
                latest_scoring_files = sorted(
                    scoring_dir.glob('comprehensive_*.json'),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )

                if latest_scoring_files:
                    latest_file = latest_scoring_files[0]
                    # 检查是否是最近5分钟内生成的
                    if time.time() - latest_file.stat().st_mtime < 300:
                        logger.info(f"✅ 发现新生成的综合打分文件: {latest_file.name}")
                        with open(latest_file) as f:
                            scoring_data = json.load(f)
                            logger.info(f"   参数总数: {scoring_data.get('metadata', {}).get('total_params', 0)}")
                            logger.info(f"   表格数: {len(scoring_data.get('table_details', []))}")

                # 最终截图
                await page.screenshot(
                    path=f"{self.base_dir}/test_results/8089_timeout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )

                if processing_observed:
                    logger.warning("⚠️ 观察到处理过程，但未获取到最终URL")
                else:
                    logger.error("❌ 未观察到任何处理过程")

            except TimeoutError as e:
                logger.error(f"❌ 超时错误: {e}")
            except Exception as e:
                logger.error(f"❌ 测试错误: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()

        logger.info("=" * 70)
        logger.info("测试完成")
        return self.results.get('final_url')

async def main():
    """主函数"""
    tester = Real8089UITest()
    final_url = await tester.run_test()

    if final_url:
        logger.info("=" * 70)
        logger.info("🎯 测试成功完成!")
        logger.info(f"📊 最终返回的URL: {final_url}")
        logger.info("=" * 70)
        logger.info("请访问以下URL验证结果:")
        logger.info(f"  1. 8089监控UI: http://202.140.143.88:8089/")
        logger.info(f"  2. 生成的文档: {final_url}")
    else:
        logger.info("=" * 70)
        logger.info("⚠️ 测试未能获取到最终URL")
        logger.info("可能原因:")
        logger.info("  1. 页面元素选择器需要更新")
        logger.info("  2. 处理时间超过预期")
        logger.info("  3. 8089服务未正确配置")
        logger.info("=" * 70)

    return final_url

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print(f"\n🔗 最终URL: {result}")
    else:
        print("\n❌ 未获取到最终URL")