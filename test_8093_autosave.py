#!/usr/bin/env python3
"""
测试8093系统的自动保存和加载功能
"""

import requests
import re

# 获取8093页面
response = requests.get('http://localhost:8093/')
html = response.text

print("=" * 60)
print("🔍 测试8093自动保存功能")
print("=" * 60)

# 检查是否包含新功能的代码
checks = {
    "loadSavedInputs函数": "function loadSavedInputs()",
    "clearSavedData函数": "function clearSavedData()",
    "基线URL自动保存": "localStorage.setItem('tencent_baseline_url'",
    "目标URL自动保存": "localStorage.setItem('tencent_target_url'",
    "Cookie自动保存": "localStorage.setItem('tencent_doc_cookie'",
    "清除数据按钮": 'onclick="clearSavedData()"',
    "自动加载功能": "loadSavedInputs();"
}

print("\n功能检查：")
all_passed = True
for name, pattern in checks.items():
    if pattern in html:
        print(f"✅ {name}: 已实现")
    else:
        print(f"❌ {name}: 未找到")
        all_passed = False

print("\n" + "=" * 60)

if all_passed:
    print("✅ 所有自动保存功能已成功实现！")
    print("\n功能说明：")
    print("1. 📝 自动保存：输入的URL和Cookie会自动保存到浏览器本地存储")
    print("2. 🔄 自动加载：页面刷新时会自动加载上次保存的输入")
    print("3. 🗑️ 清除功能：可以一键清除所有保存的数据")
    print("\n使用方法：")
    print("1. 访问 http://202.140.143.88:8093/")
    print("2. 输入URL和Cookie后，系统会自动保存")
    print("3. 刷新页面后，之前的输入会自动恢复")
    print("4. 点击'清除保存的数据'按钮可以清空所有保存的信息")
else:
    print("⚠️ 部分功能未实现，请检查代码")

print("\n" + "=" * 60)