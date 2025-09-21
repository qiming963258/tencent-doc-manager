#!/usr/bin/env python3
"""
简化版真实上传脚本
使用sync_upload_v3函数直接上传
"""

import json
import sys
from pathlib import Path

sys.path.append('/root/projects/tencent-doc-manager')


def upload_to_tencent():
    """执行真实上传"""

    print("="*70)
    print("🚀 执行真实上传到腾讯文档")
    print("="*70)

    # 读取Cookie
    cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
    if not cookie_file.exists():
        print("❌ Cookie文件不存在!")
        return None

    with open(cookie_file) as f:
        cookie_data = json.load(f)

    cookie_string = cookie_data.get('current_cookies', '')
    if not cookie_string:
        print("❌ Cookie为空!")
        return None

    print(f"✅ Cookie已加载")
    print(f"   最后更新: {cookie_data.get('last_update', 'Unknown')}")

    # 要上传的文件
    excel_file = '/root/projects/tencent-doc-manager/excel_outputs/marked/colored_test_REAL_20250921_193215.xlsx'

    if not Path(excel_file).exists():
        print(f"❌ Excel文件不存在: {excel_file}")
        return None

    print(f"✅ 准备上传文件: {Path(excel_file).name}")
    print(f"   文件大小: {Path(excel_file).stat().st_size:,} bytes")

    try:
        # 使用同步上传函数
        from production.core_modules.tencent_doc_upload_production_v3 import sync_upload_v3

        print("\n🔄 正在连接腾讯文档...")
        print("⏳ 这可能需要几秒钟...")

        # 执行上传
        result = sync_upload_v3(
            cookie_string=cookie_string,
            file_path=excel_file,
            headless=True  # 无头模式
        )

        if result and result.get('success'):
            print("\n✅ 上传成功!")
            print(f"🔗 文档URL: {result.get('url')}")
            print(f"📄 文档名称: {result.get('doc_name')}")
            return result.get('url')
        else:
            print(f"\n❌ 上传失败: {result.get('message', 'Unknown error')}")
            return None

    except ImportError as e:
        print(f"❌ 无法导入上传模块: {e}")
        print("\n请确保已安装必要的依赖:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return None

    except Exception as e:
        print(f"❌ 上传出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""

    # 执行上传
    url = upload_to_tencent()

    print("\n" + "="*70)

    if url:
        print("🎉 上传成功!")
        print(f"\n📋 请访问以下链接查看涂色效果:")
        print(f"   {url}")
        print("\n🔍 验证要点:")
        print("   1. 检查是否有浅红、浅黄、浅绿色背景")
        print("   2. 检查批注是否显示（鼠标悬停）")
        print("   3. 检查边框是否正常")
    else:
        print("❌ 上传失败")
        print("\n可能的原因:")
        print("   1. Cookie已过期（需要重新登录获取）")
        print("   2. 网络连接问题")
        print("   3. 腾讯文档API变更")

        print("\n📋 手动上传步骤:")
        print("1. 下载文件:")
        print("   /root/projects/tencent-doc-manager/excel_outputs/marked/colored_test_REAL_20250921_193215.xlsx")
        print("")
        print("2. 访问腾讯文档网站:")
        print("   https://docs.qq.com")
        print("")
        print("3. 登录后点击'新建' -> '导入' -> '本地文件'")
        print("")
        print("4. 选择下载的Excel文件并上传")
        print("")
        print("5. 上传完成后，分享链接给我验证涂色效果")

    print("="*70)

    return url


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)