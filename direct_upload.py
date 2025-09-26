#!/usr/bin/env python3
"""直接上传Excel到腾讯文档"""

import sys
sys.path.append('/root/projects/tencent-doc-manager')

import requests
import json
import os
from pathlib import Path

def upload_with_api():
    """使用requests直接调用腾讯文档API"""

    # 读取cookies
    cookie_file = Path('/root/projects/tencent-doc-manager/config/cookies.json')
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookies_data = json.load(f)
        cookies = cookies_data.get('cookies', [])

    # 转换cookies格式
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))

    # 准备文件
    excel_file = '/root/projects/tencent-doc-manager/excel_outputs/marked/new_colors_20250929_021336.xlsx'

    # 构建表单数据
    with open(excel_file, 'rb') as f:
        files = {
            'file': (os.path.basename(excel_file), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }

        # 上传URL (这是腾讯文档的导入接口)
        url = 'https://docs.qq.com/api/upload/import'

        # 设置headers
        headers = {
            'Accept': 'application/json',
            'Origin': 'https://docs.qq.com',
            'Referer': 'https://docs.qq.com/'
        }

        print(f"📤 开始上传: {os.path.basename(excel_file)}")

        # 发送请求
        response = session.post(url, files=files, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            if result.get('ret') == 0:
                doc_url = result.get('url', '')
                doc_id = result.get('doc_id', '')
                print(f"✅ 上传成功!")
                print(f"🔗 文档URL: {doc_url}")
                print(f"📊 文档ID: {doc_id}")
                return {'success': True, 'url': doc_url, 'doc_id': doc_id}
            else:
                print(f"❌ 上传失败: {result}")
                return {'success': False, 'message': str(result)}
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return {'success': False, 'message': f'HTTP {response.status_code}'}

if __name__ == "__main__":
    result = upload_with_api()

    if result.get('success'):
        print("\n" + "="*60)
        print("🎉 请访问以下URL验证新颜色显示效果:")
        print(f"   {result['url']}")
        print("="*60)