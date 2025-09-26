#!/usr/bin/env python3
"""真实点击快速刷新按钮并监控全链路"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright
import requests

async def click_refresh_and_monitor():
    """点击快速刷新按钮并监控执行过程"""

    print("="*60)
    print(f"📅 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    async with async_playwright() as p:
        # 启动浏览器（有头模式方便观察）
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1. 访问8089页面
            print("\n1️⃣ 访问8089热力图页面...")
            await page.goto("http://localhost:8089")
            await page.wait_for_load_state("networkidle")

            # 2. 等待页面加载完成
            await asyncio.sleep(2)

            # 3. 打开监控设置（如果没有打开）
            print("2️⃣ 打开监控设置面板...")
            settings_visible = await page.is_visible("#monitoring-settings")
            if not settings_visible:
                toggle = await page.query_selector("text=监控设置")
                if toggle:
                    await toggle.click()
                    await asyncio.sleep(1)

            # 4. 点击快速刷新按钮
            print("3️⃣ 点击快速刷新按钮...")
            refresh_button = await page.query_selector("button:has-text('快速刷新')")
            if refresh_button:
                await refresh_button.click()
                print("✅ 已点击快速刷新按钮")
            else:
                print("❌ 未找到快速刷新按钮")
                return None

            # 5. 监控工作流执行状态
            print("\n4️⃣ 开始监控工作流执行状态...")
            print("-"*50)

            start_time = time.time()
            last_status = None
            last_progress = 0
            upload_url = None

            while True:
                # 获取后端状态
                try:
                    response = requests.get("http://localhost:8093/api/status", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get('status', 'unknown')
                        progress = data.get('progress', 0)
                        current_step = data.get('current_step', '未知')
                        results = data.get('results', {})

                        # 打印状态变化
                        if status != last_status or progress != last_progress:
                            elapsed = int(time.time() - start_time)
                            print(f"[{elapsed:3d}秒] 状态:{status:10} 进度:{progress:3}% 步骤:{current_step}")
                            last_status = status
                            last_progress = progress

                        # 检查是否完成
                        if status == "completed":
                            upload_url = results.get('upload_url')
                            print("\n" + "="*50)
                            print("✅ 工作流执行完成！")
                            print(f"⏱️  总耗时: {int(time.time() - start_time)}秒")

                            # 打印关键结果
                            print("\n📊 执行结果:")
                            print(f"  基线文件: {results.get('baseline_file', 'N/A')}")
                            print(f"  目标文件: {results.get('target_file', 'N/A')}")
                            print(f"  涂色文件: {results.get('marked_file', 'N/A')}")
                            print(f"  上传URL: {upload_url if upload_url else '❌ 上传失败'}")
                            break

                        # 检查是否失败
                        if status == "error":
                            print("\n" + "="*50)
                            print("❌ 工作流执行失败!")
                            # 打印最后几条日志
                            logs = data.get('logs', [])
                            if logs:
                                print("\n最后的日志:")
                                for log in logs[-5:]:
                                    print(f"  [{log.get('level')}] {log.get('message')}")
                            break

                except Exception as e:
                    print(f"⚠️ 获取状态失败: {e}")

                # 超时检查（10分钟）
                if time.time() - start_time > 600:
                    print("\n⏰ 执行超时（10分钟）")
                    break

                await asyncio.sleep(2)

            # 6. 获取详细日志
            print("\n5️⃣ 获取详细执行日志...")
            try:
                response = requests.get("http://localhost:8093/api/workflow-logs", timeout=5)
                if response.status_code == 200:
                    logs = response.json().get('logs', [])

                    # 查找关键日志
                    for log in logs:
                        msg = log.get('message', '')
                        if '上传' in msg or 'upload' in msg.lower():
                            print(f"  📤 {msg}")
                        elif '失败' in msg or '错误' in msg:
                            print(f"  ❌ {msg}")
            except:
                pass

            return upload_url

        finally:
            await browser.close()

def check_upload_result(upload_url):
    """检查上传结果"""
    print("\n" + "="*60)
    print("📋 上传结果检查")
    print("="*60)

    if upload_url:
        print(f"✅ 成功获取上传URL: {upload_url}")
        print(f"🔗 请访问URL验证文档: {upload_url}")

        # 尝试验证URL是否可访问
        try:
            response = requests.head(upload_url, allow_redirects=True, timeout=5)
            if response.status_code < 400:
                print(f"✅ URL可访问 (状态码: {response.status_code})")
            else:
                print(f"⚠️ URL返回错误 (状态码: {response.status_code})")
        except Exception as e:
            print(f"⚠️ 无法验证URL: {e}")
    else:
        print("❌ 未获取到上传URL")
        print("\n可能的原因:")
        print("  1. 存储空间不足（检查是否仍有95%限制）")
        print("  2. Cookie已过期")
        print("  3. 网络连接问题")
        print("  4. 上传模块错误")

    return upload_url

async def main():
    """主函数"""
    print("🚀 开始真实全链路测试")
    print("📌 测试步骤:")
    print("  1. 点击快速刷新按钮")
    print("  2. 监控工作流执行")
    print("  3. 获取上传URL")
    print("  4. 验证结果")

    # 执行测试
    upload_url = await click_refresh_and_monitor()

    # 检查结果
    final_url = check_upload_result(upload_url)

    # 返回结果
    print("\n" + "="*60)
    print("🏁 测试完成")
    print("="*60)

    return final_url

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print(f"\n✅ 最终上传URL: {result}")
    else:
        print(f"\n❌ 测试失败，未获取到上传URL")