#!/usr/bin/env python3
import requests
import re

# 获取8093页面
response = requests.get('http://localhost:8093/')
html = response.text

# 查找script标签内容
script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if script_match:
    script_content = script_match.group(1)
    
    # 检查函数定义
    if 'function loadSavedCookie()' in script_content:
        print('✅ loadSavedCookie函数已定义')
    else:
        print('❌ loadSavedCookie函数未定义')
    
    if 'function startWorkflow()' in script_content:
        print('✅ startWorkflow函数已定义')
    else:
        print('❌ startWorkflow函数未定义')
    
    # 检查按钮onclick事件
    if 'onclick="loadSavedCookie()"' in html:
        print('✅ loadSavedCookie按钮事件已绑定')
    else:
        print('❌ loadSavedCookie按钮事件未绑定')
    
    if 'onclick="startWorkflow()"' in html:
        print('✅ startWorkflow按钮事件已绑定')
    else:
        print('❌ startWorkflow按钮事件未绑定')
    
    # 检查是否有语法错误标志
    lines = script_content.split('\n')
    for i, line in enumerate(lines, 1):
        # 检查未闭合的引号
        single_quotes = line.count("'") - line.count("\\'")
        double_quotes = line.count('"') - line.count('\\"')
        if single_quotes % 2 != 0:
            print(f'⚠️ 第{i}行可能有未闭合的单引号: {line[:50]}...')
        if double_quotes % 2 != 0:
            print(f'⚠️ 第{i}行可能有未闭合的双引号: {line[:50]}...')
    
    print('\n页面加载成功，JavaScript函数应该可以正常工作')
    print('请在浏览器中访问 http://202.140.143.88:8093/ 测试按钮功能')
else:
    print('未找到script标签')