#!/usr/bin/env python3
"""
调试Cookie解析问题
"""

import json

# 读取Cookie
with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
    cookies = json.load(f)

cookie_str = cookies.get('current_cookies', '')

print(f"📝 Cookie字符串长度: {len(cookie_str)}")
print(f"\n📋 Cookie字符串前200字符:")
print(cookie_str[:200])

# 模拟parse_cookie_string方法
def parse_cookie_string(cookie_string: str) -> list:
    """解析Cookie字符串"""
    cookies = []

    for cookie_pair in cookie_string.split('; '):
        if '=' in cookie_pair:
            name, value = cookie_pair.strip().split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.docs.qq.com',
                'path': '/'
            })

    return cookies

# 解析Cookie
parsed_cookies = parse_cookie_string(cookie_str)

print(f"\n📊 解析结果:")
print(f"解析出的Cookie数量: {len(parsed_cookies)}")

if len(parsed_cookies) > 0:
    print(f"\n前3个Cookie:")
    for i, cookie in enumerate(parsed_cookies[:3]):
        print(f"{i+1}. {cookie['name']}: {cookie['value'][:30]}...")
else:
    print("\n❌ 没有解析出任何Cookie")

    # 检查分隔符
    print("\n🔍 检查Cookie字符串格式:")
    if '; ' in cookie_str:
        print("✅ 包含'; '分隔符")
    else:
        print("❌ 不包含'; '分隔符")

    if '=' in cookie_str:
        print("✅ 包含'='")
    else:
        print("❌ 不包含'='")

    # 尝试其他分隔符
    if ';' in cookie_str:
        print("\n尝试使用';'分隔（无空格）:")
        test_cookies = []
        for cookie_pair in cookie_str.split(';'):
            if '=' in cookie_pair:
                test_cookies.append(cookie_pair.strip())
        print(f"分割出{len(test_cookies)}个部分")
        if test_cookies:
            print(f"第一个部分: {test_cookies[0]}")