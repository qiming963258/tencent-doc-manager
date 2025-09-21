#!/usr/bin/env python3
"""
上传已涂色的Excel文件到腾讯文档
"""

import os
import sys
import json
from datetime import datetime

sys.path.append('/root/projects/tencent-doc-manager')

def upload_colored_excel():
    """上传已涂色的Excel文件"""

    print("\n" + "="*60)
    print("📤 上传涂色Excel文件到腾讯文档")
    print("="*60)

    # 文件路径
    colored_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek/tencent_111测试版本-小红书部门_20250919_2255_midweek_W38_colored.xlsx"

    if not os.path.exists(colored_file):
        print(f"❌ 文件不存在: {colored_file}")
        return None

    print(f"📄 待上传文件: {os.path.basename(colored_file)}")
    print(f"📏 文件大小: {os.path.getsize(colored_file):,} bytes")

    # 使用v3模块上传
    print("\n🔄 使用生产级v3模块上传...")

    try:
        from production.core_modules.tencent_doc_upload_production_v3 import sync_upload_v3

        # 获取Cookie
        with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
            cookies = json.load(f)
        cookie_str = cookies.get('current_cookies', cookies.get('cookies', ''))

        # 上传文件（v3模块参数顺序：cookie_string, file_path）
        result = sync_upload_v3(cookie_str, colored_file)

        # v3模块可能返回dict或string
        if isinstance(result, dict):
            doc_url = result.get('url', result.get('doc_url', ''))
        else:
            doc_url = result

        if doc_url and isinstance(doc_url, str) and doc_url.startswith('https://'):
            print(f"\n✅ 上传成功！")
            print(f"📝 腾讯文档链接: {doc_url}")

            # 保存上传记录
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            upload_record = {
                "file": os.path.basename(colored_file),
                "url": doc_url,
                "upload_time": timestamp,
                "type": "colored_excel",
                "cells_colored": 54
            }

            # 保存记录
            upload_log = "/root/projects/tencent-doc-manager/upload_colored_log.json"

            if os.path.exists(upload_log):
                with open(upload_log, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {"uploads": []}

            log_data["uploads"].append(upload_record)

            with open(upload_log, 'w') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)

            print(f"\n📊 上传记录已保存")

            return doc_url

        else:
            print(f"❌ 上传失败或返回的不是有效链接: {doc_url}")
            return None

    except Exception as e:
        print(f"❌ 上传失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def verify_coloring_preservation():
    """验证说明"""
    print("\n" + "="*60)
    print("🔍 验证涂色效果保留")
    print("="*60)

    print("""
验证步骤：
1. 打开上传后的腾讯文档链接
2. 查看以下区域的背景颜色：
   - A2:C4 区域 - 应显示红色背景（高风险）
   - D2:F4 区域 - 应显示橙色背景（中风险）
   - G2:I4 区域 - 应显示绿色背景（低风险）
   - A6:C8 区域 - 应显示浅红色背景
   - D6:F8 区域 - 应显示浅橙色背景
   - G6:I8 区域 - 应显示黄色背景

共涂色54个单元格，分为6个风险等级区域

注意：
- solid填充模式在腾讯文档中显示效果最好
- 颜色可能会有轻微差异，但应该明显可见
- 如果颜色未显示，可能需要刷新页面
""")

if __name__ == "__main__":
    # 上传文件
    doc_url = upload_colored_excel()

    if doc_url:
        print("\n" + "="*60)
        print("🎉 上传完成！")
        print(f"🔗 请访问链接查看涂色效果: {doc_url}")
        print("="*60)

        # 显示验证说明
        verify_coloring_preservation()