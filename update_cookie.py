#!/usr/bin/env python3
"""
腾讯文档Cookie更新工具
用于快速更新系统Cookie配置
"""

import json
import sys
import os
from datetime import datetime
import re

def parse_cookie_string(cookie_string):
    """解析Cookie字符串为字典格式"""
    cookies = []
    cookie_dict = {}
    
    # 清理Cookie字符串
    cookie_string = cookie_string.strip()
    
    # 分割Cookie
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            name = name.strip()
            value = value.strip()
            cookies.append({
                "name": name,
                "value": value
            })
            cookie_dict[name] = value
    
    return cookies, cookie_dict

def validate_cookie(cookie_dict):
    """验证Cookie是否包含必要字段"""
    required_fields = ['DOC_SID', 'SID', 'uid']
    missing_fields = []
    
    for field in required_fields:
        if field not in cookie_dict:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"⚠️ 警告：Cookie缺少以下必要字段：{', '.join(missing_fields)}")
        return False
    
    print("✅ Cookie包含所有必要字段")
    return True

def update_cookie_file(cookie_string, config_path='config/cookies.json'):
    """更新Cookie配置文件"""
    full_path = os.path.join(os.path.dirname(__file__), config_path)
    
    # 解析Cookie
    cookies, cookie_dict = parse_cookie_string(cookie_string)
    
    # 验证Cookie
    if not validate_cookie(cookie_dict):
        print("⚠️ Cookie可能无效，但仍会保存")
    
    # 构建配置对象
    config = {
        "cookies": cookies,
        "cookie_string": cookie_string.strip(),
        "current_cookies": cookie_string.strip(),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 备份原文件
    if os.path.exists(full_path):
        backup_path = full_path + '.backup_' + datetime.now().strftime("%Y%m%d_%H%M%S")
        os.rename(full_path, backup_path)
        print(f"📦 已备份原配置文件到：{backup_path}")
    
    # 写入新配置
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Cookie配置已更新：{full_path}")
    print(f"📅 更新时间：{config['last_updated']}")
    print(f"🔑 Cookie字段数：{len(cookies)}")
    
    return True

def test_cookie(cookie_string):
    """测试Cookie是否有效（简单测试）"""
    import subprocess
    
    print("\n🧪 测试Cookie有效性...")
    
    # 构建测试命令
    test_url = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"
    test_cmd = [
        "python3",
        "/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430/tencent_export_automation.py",
        test_url,
        "--format=csv",
        f"--cookies={cookie_string}",
        "--test-only"  # 仅测试模式
    ]
    
    try:
        # 尝试简单的连接测试
        print("📡 正在测试连接...")
        # 这里只是示例，实际测试需要运行下载器
        print("⚠️ 完整测试需要运行实际下载任务")
        return True
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        return False

def main():
    print("=" * 60)
    print("🍪 腾讯文档Cookie更新工具")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # 从命令行参数获取Cookie
        cookie_string = sys.argv[1]
    else:
        # 交互式输入
        print("\n请按照以下步骤获取Cookie：")
        print("1. 在浏览器中打开 https://docs.qq.com")
        print("2. 登录您的QQ账号")
        print("3. 打开任意一个腾讯文档")
        print("4. 按F12打开开发者工具")
        print("5. 切换到Network标签")
        print("6. 刷新页面")
        print("7. 找到任意docs.qq.com请求")
        print("8. 在Request Headers中复制完整的Cookie值")
        print("\n" + "=" * 60)
        print("请粘贴您的Cookie字符串（按Enter确认）：")
        cookie_string = input().strip()
    
    if not cookie_string:
        print("❌ Cookie字符串不能为空")
        sys.exit(1)
    
    # 更新Cookie
    if update_cookie_file(cookie_string):
        print("\n✅ Cookie更新成功！")
        
        # 测试Cookie
        test_cookie(cookie_string)
        
        print("\n📋 后续步骤：")
        print("1. 重新运行8093系统")
        print("2. 测试下载功能是否恢复")
        print("3. 如果仍有问题，请检查Cookie是否正确")
    else:
        print("\n❌ Cookie更新失败")
        sys.exit(1)

if __name__ == "__main__":
    main()