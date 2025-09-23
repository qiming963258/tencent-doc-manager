#!/usr/bin/env python3
"""
8089真实UI点击测试 - 点击"立即刷新"按钮
真实测试，无虚拟内容，如实报告问题
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
import json
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class Real8089ClickTest:
    """真实的8089 UI点击测试"""

    def __init__(self):
        self.base_dir = Path('/root/projects/tencent-doc-manager')
        self.ui_url = 'http://localhost:8089'

    def check_baseline(self):
        """检查基线文件状态"""
        logger.info("=" * 70)
        logger.info("📋 检查基线文件")

        baseline_dir = self.base_dir / "csv_versions/2025_W38/baseline"
        baseline_file = baseline_dir / "tencent_出国销售计划表_20250915_0145_baseline_W38.csv"

        if baseline_file.exists():
            logger.info(f"✅ 标准基线文件存在: {baseline_file.name}")
            logger.info(f"   文件大小: {baseline_file.stat().st_size} 字节")

            # 检查文件内容
            with open(baseline_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logger.info(f"   文件行数: {len(lines)}")
            return True
        else:
            logger.error(f"❌ 标准基线文件不存在: {baseline_file}")
            logger.error("这是一个真实问题：系统无法找到标准基线文件")
            logger.error("预期路径: /root/projects/tencent-doc-manager/csv_versions/2025_W38/baseline/")
            logger.error("预期文件: tencent_出国销售计划表_20250915_0145_baseline_W38.csv")
            return False

    async def real_click_test(self):
        """执行真实的UI点击测试"""
        logger.info("=" * 70)
        logger.info("🎯 开始真实8089 UI点击测试")
        logger.info("目标：点击监控设置中的'立即刷新'按钮")

        async with async_playwright() as p:
            # headless=True 因为服务器没有X服务器
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # 访问8089监控页面
                logger.info(f"📍 访问8089监控页面: {self.ui_url}")
                await page.goto(self.ui_url, wait_until='networkidle')
                await asyncio.sleep(2)

                # 先检查是否在监控设置标签页
                logger.info("🔍 切换到监控设置标签")
                monitor_tabs = [
                    'div[role="tab"]:has-text("监控设置")',
                    'div.ant-tabs-tab:has-text("监控设置")',
                    '//div[contains(@class, "ant-tabs-tab") and contains(text(), "监控设置")]',
                    'text="监控设置"'
                ]

                for selector in monitor_tabs:
                    try:
                        tab = page.locator(selector).first
                        if await tab.count() > 0 and await tab.is_visible():
                            await tab.click()
                            logger.info("✅ 切换到监控设置标签")
                            await asyncio.sleep(2)
                            break
                    except:
                        continue

                # 查找并点击"立即刷新"按钮
                logger.info("🔍 查找'立即刷新'按钮")

                # 尝试多种方式定位按钮
                refresh_button_selectors = [
                    'button:has-text("立即刷新")',
                    'button.ant-btn:has-text("立即刷新")',
                    'button.ant-btn-primary:has-text("立即刷新")',
                    '//button[contains(text(), "立即刷新")]',
                    'button[type="button"]:has-text("立即刷新")'
                ]

                button_found = False
                for selector in refresh_button_selectors:
                    try:
                        button = page.locator(selector).first
                        if await button.count() > 0 and await button.is_visible():
                            logger.info(f"✅ 找到按钮: {selector}")

                            # 滚动到按钮位置
                            await button.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)

                            # 点击按钮
                            logger.info("👆 真实点击'立即刷新'按钮")
                            await button.click()
                            button_found = True
                            break
                    except Exception as e:
                        continue

                if not button_found:
                    logger.error("❌ 无法找到'立即刷新'按钮")
                    logger.error("这是一个真实问题：")
                    logger.error("  1. 页面结构可能已变更")
                    logger.error("  2. 按钮选择器需要更新")
                    logger.error("  3. 8089服务可能未正确启动")

                    # 列出页面上所有按钮
                    logger.info("页面上的按钮：")
                    all_buttons = await page.locator('button').all()
                    for i, btn in enumerate(all_buttons[:10]):
                        text = await btn.text_content()
                        if text:
                            logger.info(f"  按钮{i+1}: {text.strip()}")

                    # 截图保存当前页面
                    screenshot_path = self.base_dir / f"8089_page_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await page.screenshot(path=str(screenshot_path))
                    logger.info(f"📸 已保存页面截图: {screenshot_path}")
                    return None

                # 等待工作流开始
                logger.info("⏳ 等待工作流启动...")
                await asyncio.sleep(5)

                # 监控工作流进度
                logger.info("📊 监控工作流进度...")
                start_time = time.time()
                max_wait_time = 180  # 最多等待3分钟

                last_url = None
                while time.time() - start_time < max_wait_time:
                    # 查找日志容器
                    log_container = page.locator('.log-container, .workflow-logs, #logs')
                    if await log_container.count() > 0:
                        log_text = await log_container.text_content()
                        if log_text:
                            # 检查关键日志
                            if '发现变更' in log_text:
                                import re
                                match = re.search(r'发现\s*(\d+)\s*处变更', log_text)
                                if match:
                                    logger.info(f"   ✅ 检测到变更: {match.group(1)}处")

                            if '上传成功' in log_text:
                                logger.info("   ✅ 检测到上传成功")

                    # 检查是否有生成的URL
                    url_elements = page.locator('a[href*="docs.qq.com/sheet"]')
                    if await url_elements.count() > 0:
                        urls = []
                        for i in range(await url_elements.count()):
                            href = await url_elements.nth(i).get_attribute('href')
                            if href and href != last_url:
                                logger.info(f"   🔗 发现URL: {href}")
                                urls.append(href)
                                last_url = href

                        if urls:
                            # 取最新的URL
                            final_url = urls[-1]
                            logger.info(f"✅ 获取最终URL: {final_url}")

                            # 等待几秒确保流程完成
                            await asyncio.sleep(5)

                            # 最后截图
                            screenshot_path = self.base_dir / f"8089_success_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            await page.screenshot(path=str(screenshot_path))
                            logger.info(f"📸 保存成功截图: {screenshot_path}")

                            return final_url

                    await asyncio.sleep(2)

                logger.warning("⏱️ 等待超时，未检测到生成的URL")
                logger.warning("这是一个真实问题：")
                logger.warning("  1. 工作流可能未正常执行")
                logger.warning("  2. 基线匹配可能失败")
                logger.warning("  3. 处理时间超过预期")

                # 最终截图
                screenshot_path = self.base_dir / f"8089_timeout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"📸 保存超时截图: {screenshot_path}")

                return None

            except Exception as e:
                logger.error(f"❌ 测试过程中发生错误: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return None
            finally:
                # 保持浏览器开启几秒以便观察
                logger.info("🔍 保持浏览器5秒以便观察...")
                await asyncio.sleep(5)
                await browser.close()

    async def check_workflow_logs(self):
        """检查工作流日志"""
        logger.info("📋 检查工作流日志")

        # 检查最近的日志文件
        log_dir = self.base_dir / "logs"
        if log_dir.exists():
            log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
            if log_files:
                latest_log = log_files[0]
                if time.time() - latest_log.stat().st_mtime < 300:  # 5分钟内
                    logger.info(f"   最新日志: {latest_log.name}")
                    with open(latest_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-20:]  # 最后20行
                        for line in lines:
                            if '基线' in line or 'baseline' in line.lower():
                                logger.info(f"   日志: {line.strip()}")

    def verify_result(self, url):
        """验证结果"""
        logger.info("=" * 70)
        logger.info("📊 测试结果汇总")

        if url:
            logger.info(f"✅ 成功获取到URL: {url}")
            logger.info("")
            logger.info("请手动验证以下内容：")
            logger.info(f"1. 访问URL查看是否有涂色: {url}")
            logger.info("2. 检查涂色数量是否与实际变更一致")
            logger.info("3. 验证变更位置是否正确")
            logger.info("4. 确认是否为真实的数据对比结果")
        else:
            logger.error("❌ 测试失败：未能获取到最终URL")
            logger.error("")
            logger.error("发现的真实问题：")
            logger.error("1. 工作流可能未正常启动或执行")
            logger.error("2. 基线文件可能未被系统正确识别")
            logger.error("3. 8089服务可能存在配置问题")
            logger.error("")
            logger.error("建议检查：")
            logger.error("1. 确认8089服务是否正常运行: http://localhost:8089")
            logger.error("2. 检查基线文件路径配置")
            logger.error("3. 查看8089服务日志")

    async def run(self):
        """运行完整测试"""
        logger.info("=" * 70)
        logger.info("🚀 8089真实点击测试开始")
        logger.info("=" * 70)

        # 检查基线
        if not self.check_baseline():
            logger.error("=" * 70)
            logger.error("❌ 基线检查失败，这是一个真实问题")
            logger.error("系统需要标准基线文件才能进行对比")
            logger.error("=" * 70)
            return None

        # 执行真实点击
        final_url = await self.real_click_test()

        # 检查工作流日志
        await self.check_workflow_logs()

        # 验证结果
        self.verify_result(final_url)

        logger.info("=" * 70)
        return final_url

async def main():
    """主函数"""
    tester = Real8089ClickTest()
    final_url = await tester.run()

    if final_url:
        print(f"\n{'=' * 70}")
        print(f"🎯 最终URL: {final_url}")
        print(f"{'=' * 70}")
        print(f"请立即检查URL的涂色内容")
    else:
        print(f"\n{'=' * 70}")
        print(f"❌ 真实测试发现问题")
        print(f"已如实报告所有问题，请查看上方日志")
        print(f"{'=' * 70}")

    return final_url

if __name__ == "__main__":
    result = asyncio.run(main())