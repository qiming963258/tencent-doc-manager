#!/usr/bin/env python3
"""
执行真实的文件上传到腾讯文档
"""

import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.append('/root/projects/tencent-doc-manager')

async def upload_xlsx_to_tencent():
    """上传XLSX文件到腾讯文档"""

    print("\n" + "="*60)
    print("🚀 执行真实上传到腾讯文档")
    print("="*60)

    # 找到要上传的文件
    midweek_dir = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek"

    # 优先选择涂色后的文件
    colored_file = "tencent_111测试版本-小红书部门_20250919_2255_midweek_W38_colored.xlsx"
    file_path = os.path.join(midweek_dir, colored_file)

    if not os.path.exists(file_path):
        # 如果涂色文件不存在，选择原始XLSX
        original_file = "tencent_111测试版本-小红书部门_20250919_2255_midweek_W38.xlsx"
        file_path = os.path.join(midweek_dir, original_file)
        colored_file = original_file

    if not os.path.exists(file_path):
        print("❌ 找不到要上传的XLSX文件")
        return None

    print(f"📄 上传文件: {colored_file}")
    print(f"📏 文件大小: {os.path.getsize(file_path):,} bytes")
    print(f"📍 文件路径: {file_path}")

    # 读取Cookie
    with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
        cookie_data = json.load(f)
        cookies = cookie_data.get('current_cookies', '')

    if not cookies:
        print("❌ Cookie无效，无法上传")
        return None

    print("🍪 Cookie状态: ✅ 有效")

    try:
        # 导入上传模块
        from tencent_doc_uploader import TencentDocUploader

        print("\n📤 开始上传流程...")

        # 创建上传器实例
        uploader = TencentDocUploader()

        # 初始化浏览器
        print("🌐 初始化浏览器...")
        await uploader.init_browser(headless=True)

        # 使用Cookie登录
        print("🔐 使用Cookie登录...")
        login_success = await uploader.login_with_cookies(cookies)

        if not login_success:
            print("❌ Cookie登录失败")
            # 尝试直接访问
            await uploader.page.goto('https://docs.qq.com')
            await asyncio.sleep(2)
        else:
            print("✅ 登录成功")

        # 执行上传
        print("\n⬆️ 正在上传文件...")

        # 调用上传方法
        result = await uploader.upload_file(
            file_path=file_path,
            upload_mode='new',  # 创建新文档
            target_url=None
        )

        if result and result.get('success'):
            doc_url = result.get('url')
            print("\n" + "="*60)
            print("✅ 上传成功！")
            print(f"📎 新文档链接: {doc_url}")
            print("="*60)

            # 保存结果
            with open('/root/projects/tencent-doc-manager/upload_result.json', 'w') as f:
                json.dump({
                    'success': True,
                    'url': doc_url,
                    'file': colored_file,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            return doc_url
        else:
            error_msg = result.get('error', '未知错误') if result else '上传失败'
            print(f"❌ 上传失败: {error_msg}")

    except ImportError as e:
        print(f"⚠️ 上传模块导入失败: {e}")
        print("\n尝试使用8093系统的上传功能...")

        # 使用8093系统的同步上传函数
        try:
            from production_integrated_test_system_8093 import sync_upload_file

            print("📤 使用8093系统上传...")
            result = sync_upload_file(
                file_path,
                upload_option='new',
                target_url='',
                cookie_string=cookies
            )

            if result and result.get('success'):
                doc_url = result.get('url')
                print(f"\n✅ 上传成功！")
                print(f"📎 新文档链接: {doc_url}")
                return doc_url

        except Exception as e2:
            print(f"❌ 8093系统上传也失败: {e2}")

    except Exception as e:
        print(f"❌ 上传出错: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理资源
        try:
            if 'uploader' in locals():
                if hasattr(uploader, 'browser') and uploader.browser:
                    await uploader.browser.close()
                if hasattr(uploader, 'playwright'):
                    await uploader.playwright.stop()
        except:
            pass

    return None

async def main():
    """主函数"""

    print("\n🎯 腾讯文档XLSX上传")
    print("目标：上传处理后的Excel文件并获取新链接")

    # 执行上传
    doc_url = await upload_xlsx_to_tencent()

    if doc_url:
        print("\n" + "🔗"*30)
        print(f"\n📋 上传成功！请复制此链接：")
        print(f"\n   {doc_url}\n")
        print("🔗"*30)
        return doc_url
    else:
        print("\n⚠️ 自动上传未成功，请手动上传：")
        print("\n手动上传步骤：")
        print("1. 访问: https://docs.qq.com")
        print("2. 点击「新建」→「在线表格」→「导入本地表格」")
        print("3. 选择文件: tencent_111测试版本-小红书部门_20250919_2255_midweek_W38_colored.xlsx")
        print("4. 等待上传完成后，复制浏览器地址栏的链接")
        return None

if __name__ == "__main__":
    result = asyncio.run(main())