#!/usr/bin/env python3
"""
直接测试真实文档下载功能
验证系统能否真正下载腾讯文档
"""

import json
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

async def test_current_downloader():
    """测试当前的TencentDocAutoExporter"""
    print("=" * 60)
    print("🧪 测试当前下载器 - TencentDocAutoExporter")
    print("=" * 60)

    try:
        from production.core_modules.tencent_export_automation import TencentDocAutoExporter

        # 读取cookie配置
        with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
            cookie_data = json.load(f)
            cookies = cookie_data.get('current_cookies', '')

        print(f"📅 Cookie更新时间: {cookie_data.get('last_update')}")
        print(f"✅ Cookie有效性: {cookie_data.get('is_valid')}")
        print(f"🍪 Cookie长度: {len(cookies)} 字符")

        # 使用第一个文档测试
        test_url = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"  # 出国销售计划表
        print(f"\n🔗 测试URL: {test_url}")
        print("📄 文档名称: 副本-测试版本-出国销售计划表")

        # 创建下载目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_dir = f"/root/projects/tencent-doc-manager/test_downloads_{timestamp}"
        os.makedirs(download_dir, exist_ok=True)

        print(f"📁 下载目录: {download_dir}")

        # 初始化下载器
        print("\n🔧 初始化下载器...")
        exporter = TencentDocAutoExporter(download_dir=download_dir)

        print("🚀 启动浏览器（无头模式）...")
        await exporter.start_browser(headless=True)

        print("🍪 应用Cookie认证...")
        await exporter.login_with_cookies(cookies)

        print("\n⬇️ 开始下载文档...")
        print("⏳ 这可能需要30-60秒，请耐心等待...")
        start_time = datetime.now()

        # 执行下载 - 使用4重备用机制
        result = await exporter.auto_export_document(test_url, "csv")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if result and len(result) > 0:
            print(f"\n✅ 下载成功!")
            print(f"⏱️ 耗时: {duration:.2f}秒")
            print(f"\n📄 下载的文件:")

            for file in result:
                if os.path.exists(file):
                    size = os.path.getsize(file)
                    print(f"   📁 文件: {os.path.basename(file)}")
                    print(f"   📏 大小: {size:,} bytes")

                    # 读取并验证内容
                    with open(file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        print(f"   📊 行数: {len(lines)}")

                        if lines:
                            # 显示前3行
                            print(f"\n   📝 文件内容预览:")
                            for i, line in enumerate(lines[:3], 1):
                                preview = line[:80] + "..." if len(line) > 80 else line.strip()
                                print(f"      行{i}: {preview}")

                            # 检查是否包含实际数据
                            has_data = any(len(line.strip()) > 0 for line in lines)
                            if has_data:
                                print(f"\n   ✅ 文件包含实际数据")
                            else:
                                print(f"\n   ⚠️ 文件可能为空")
                else:
                    print(f"   ❌ 文件不存在: {file}")
        else:
            print(f"\n❌ 下载失败!")
            print(f"⏱️ 耗时: {duration:.2f}秒")
            print("💡 可能的原因:")
            print("   - Cookie已过期")
            print("   - 网络连接问题")
            print("   - 文档权限问题")

        # 清理
        print("\n🧹 清理资源...")
        await exporter.cleanup()

        return result is not None and len(result) > 0

    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_download_methods():
    """测试各种下载方法的可用性"""
    print("\n" + "=" * 60)
    print("🔬 测试下载方法可用性")
    print("=" * 60)

    try:
        from production.core_modules.tencent_export_automation import TencentDocAutoExporter

        # 检查类的方法
        methods = [
            ('_try_menu_export', '菜单导出'),
            ('_try_toolbar_export', '工具栏导出'),
            ('_try_keyboard_shortcut_export', '快捷键导出'),
            ('_try_right_click_export', '右键导出'),
            ('_try_keyboard_combination_export', '键盘组合导出'),
            ('_try_js_injection_export', 'JS注入导出'),
            ('_try_api_download', 'API下载')
        ]

        print("\n📋 检查可用的导出方法:")
        available_count = 0
        for method_name, description in methods:
            if hasattr(TencentDocAutoExporter, method_name):
                print(f"   ✅ {method_name:35} - {description}")
                available_count += 1
            else:
                print(f"   ❌ {method_name:35} - {description} (不存在)")

        print(f"\n📊 可用方法数: {available_count}/{len(methods)}")

        if available_count >= 4:
            print("✅ 满足架构要求的4重备用机制")
        else:
            print("⚠️ 备用方法不足，建议实现更多导出方法")

    except Exception as e:
        print(f"💥 检查失败: {e}")

async def verify_file_authenticity(file_path):
    """验证下载文件的真实性"""
    print("\n" + "=" * 60)
    print("🔍 验证文件真实性")
    print("=" * 60)

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False

    try:
        import csv

        # 尝试解析CSV
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        print(f"📊 CSV解析结果:")
        print(f"   - 总行数: {len(rows)}")

        if rows:
            print(f"   - 列数: {len(rows[0])}")

            # 检查是否有标题行
            if rows[0]:
                print(f"   - 标题行示例: {rows[0][:5]}...")

            # 检查数据行
            data_rows = [row for row in rows[1:] if any(cell.strip() for cell in row)]
            print(f"   - 有效数据行: {len(data_rows)}")

            # 检查是否包含中文（腾讯文档通常包含中文）
            has_chinese = any(
                any('\u4e00' <= char <= '\u9fff' for char in str(row))
                for row in rows[:10]
            )

            if has_chinese:
                print("   ✅ 包含中文内容（符合腾讯文档特征）")
            else:
                print("   ⚠️ 未检测到中文内容")

            return len(data_rows) > 0

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("\n" + "🎯" * 30)
    print("腾讯文档下载功能真实性测试")
    print("🎯" * 30)

    # 1. 测试下载方法可用性
    await test_download_methods()

    # 2. 测试真实下载
    success = await test_current_downloader()

    # 3. 如果下载成功，验证文件
    if success:
        # 查找最新下载的文件
        import glob
        test_dirs = glob.glob('/root/projects/tencent-doc-manager/test_downloads_*')
        if test_dirs:
            latest_dir = max(test_dirs)
            csv_files = glob.glob(f"{latest_dir}/*.csv")
            if csv_files:
                print("\n🔍 验证下载的文件...")
                for csv_file in csv_files:
                    await verify_file_authenticity(csv_file)

    print("\n" + "=" * 60)
    if success:
        print("✅ 总结: 系统能够真实下载腾讯文档")
        print("📝 建议:")
        print("   1. 创建PlaywrightDownloader类以符合架构规格")
        print("   2. 实现4重备用导出机制")
        print("   3. 添加更好的错误处理和重试逻辑")
    else:
        print("❌ 总结: 下载功能需要修复")
        print("🔧 需要:")
        print("   1. 检查Cookie是否有效")
        print("   2. 验证网络连接")
        print("   3. 确认文档访问权限")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())