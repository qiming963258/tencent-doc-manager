#!/usr/bin/env python3
"""
🎯 一键成功上传脚本 - 经过验证的完整解决方案
成功时间: 2025-09-29 03:03
成功URL: https://docs.qq.com/sheet/DWHRicFFiRXNqWUtz

使用方法:
python3 03-一键成功脚本.py <excel文件路径>
"""

import sys
import asyncio
import json
from pathlib import Path

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')

# 导入成功的上传函数
from production.core_modules.tencent_doc_upload_production_v3 import quick_upload_v3

async def upload_excel_with_colors(excel_file_path: str):
    """
    使用经过验证的方法上传Excel文件到腾讯文档

    重要: 这是唯一成功的方法，不要修改！
    """

    print("="*70)
    print("🚀 开始执行一键上传（使用成功验证的方法）")
    print("="*70)

    # 第1步：验证文件存在
    excel_file = Path(excel_file_path).resolve()
    if not excel_file.exists():
        print(f"❌ 文件不存在: {excel_file}")
        return None

    print(f"✅ 文件存在: {excel_file.name}")
    print(f"   大小: {excel_file.stat().st_size} bytes")

    # 第2步：读取Cookie（关键！）
    cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')

    try:
        with open(cookie_file, 'r') as f:
            cookie_data = json.load(f)

        cookie_string = cookie_data.get('current_cookies', '')
        last_update = cookie_data.get('last_update', '未知')

        print(f"✅ Cookie读取成功")
        print(f"   最后更新: {last_update}")

        # 检查Cookie年龄
        from datetime import datetime
        if 'last_update' in cookie_data:
            update_date = datetime.fromisoformat(cookie_data['last_update'].replace('T', ' ').split('.')[0])
            age_days = (datetime.now() - update_date).days
            if age_days > 7:
                print(f"⚠️ Cookie已{age_days}天未更新，可能需要刷新")

    except Exception as e:
        print(f"❌ Cookie读取失败: {e}")
        return None

    # 第3步：调用成功的上传函数（核心！）
    print("\n📤 开始上传...")
    print("   使用方法: quick_upload_v3（经验证成功）")

    try:
        # 这是唯一正确的方法！
        result = await quick_upload_v3(
            cookie_string=cookie_string,
            file_path=str(excel_file),
            headless=True
        )

        if result and result.get('success'):
            url = result.get('url')
            print("\n" + "="*70)
            print("🎉 上传成功！")
            print(f"📌 腾讯文档URL: {url}")
            print("="*70)

            # 验证提醒
            print("\n📊 验证清单:")
            print("1. 访问上述URL")
            print("2. 检查颜色是否显示:")
            print("   - L1级别: 红色 #FF6666")
            print("   - L2级别: 橙色 #FFB366")
            print("   - L3级别: 绿色 #66FF66")

            return url
        else:
            print(f"\n❌ 上传失败: {result}")
            print("\n可能的原因:")
            print("1. Cookie过期（最常见）")
            print("2. 网络问题")
            print("3. 文件格式问题")

            return None

    except Exception as e:
        print(f"\n❌ 上传异常: {e}")
        print("\n排查步骤:")
        print("1. 检查Cookie是否有效")
        print("2. 确认网络连接")
        print("3. 验证文件格式为.xlsx")

        return None

def check_color_config():
    """检查颜色配置是否正确"""

    print("\n🔍 检查颜色配置...")

    marker_file = Path('/root/projects/tencent-doc-manager/intelligent_excel_marker.py')

    if marker_file.exists():
        content = marker_file.read_text()

        # 检查是否使用了正确的深色
        if 'FF6666' in content and 'FFB366' in content and '66FF66' in content:
            print("✅ 颜色配置正确（使用深色）")
            return True
        else:
            print("⚠️ 颜色配置可能太浅")
            print("   应该使用:")
            print("   L1: FF6666")
            print("   L2: FFB366")
            print("   L3: 66FF66")
            return False
    else:
        print("❌ 找不到intelligent_excel_marker.py")
        return False

def main():
    """主函数"""

    print("🎯 腾讯文档上传涂色 - 一键成功脚本")
    print("基于成功案例: 2025-09-29")
    print("")

    # 检查命令行参数
    if len(sys.argv) < 2:
        # 使用默认的成功文件
        excel_file = '/root/projects/tencent-doc-manager/excel_outputs/marked/new_colors_20250929_021336.xlsx'
        print(f"使用默认文件: {excel_file}")
    else:
        excel_file = sys.argv[1]

    # 先检查颜色配置
    check_color_config()

    # 执行上传
    result_url = asyncio.run(upload_excel_with_colors(excel_file))

    if result_url:
        print("\n✨ 任务完成！")
        print(f"最终URL: {result_url}")

        # 保存成功记录
        success_log = Path('/root/projects/tencent-doc-manager/docs/成功备份/上传涂色成功/success_log.txt')
        with open(success_log, 'a') as f:
            from datetime import datetime
            f.write(f"{datetime.now().isoformat()} - 成功上传: {result_url}\n")
    else:
        print("\n❌ 上传失败，请参考以下文档:")
        print("1. /docs/成功备份/上传涂色成功/01-问题解决完整记录.md")
        print("2. /docs/成功备份/上传涂色成功/02-AI助手必读指南.md")

if __name__ == "__main__":
    main()