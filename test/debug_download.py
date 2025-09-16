#!/usr/bin/env python3
"""
调试下载功能 - 找出为什么仍然返回测试内容
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

def test_import():
    """测试模块导入"""
    print("="*60)
    print("1. 测试模块导入")
    print("="*60)
    
    try:
        from auto_download_ui_system import download_file_from_url
        print("✅ download_file_from_url 函数导入成功")
        print(f"   函数位置: {download_file_from_url.__module__}")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_config():
    """测试配置文件"""
    print("\n" + "="*60)
    print("2. 检查配置文件")
    print("="*60)
    
    config_path = Path('/root/projects/tencent-doc-manager/config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        cookie = config.get('cookie', '')
        print(f"✅ config.json 存在")
        print(f"   Cookie长度: {len(cookie)} 字符")
        print(f"   Cookie开头: {cookie[:50]}...")
        print(f"   最后更新: {config.get('last_updated', '未知')}")
        
        # 检查Cookie内容
        if 'test_cookie' in cookie or len(cookie) < 100:
            print("⚠️ Cookie可能是测试数据")
        else:
            print("✅ Cookie看起来是真实的")
        
        return config
    else:
        print("❌ config.json 不存在")
        return None

def test_download_function():
    """测试下载函数"""
    print("\n" + "="*60)
    print("3. 测试下载函数")
    print("="*60)
    
    try:
        from auto_download_ui_system import download_file_from_url
        
        # 测试URL
        test_url = "https://docs.qq.com/sheet/DVkVGZHdHVmVHaW1w"
        print(f"测试URL: {test_url}")
        
        print("\n调用 download_file_from_url()...")
        print("-"*40)
        
        # 调用函数
        result = download_file_from_url(test_url, 'csv')
        
        print("-"*40)
        print("\n返回结果:")
        print(f"成功: {result.get('success')}")
        print(f"消息: {result.get('message', result.get('error', '无消息'))}")
        
        if result.get('files'):
            print(f"文件数: {len(result['files'])}")
            for file_info in result['files']:
                print(f"  - {file_info.get('name', '未知')}: {file_info.get('size', '未知大小')}")
                
                # 检查内容
                file_path = file_info.get('path')
                if file_path and Path(file_path).exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(200)
                    print(f"    内容预览: {content[:100]}...")
                    
                    # 检查是否是测试数据
                    if '张三' in content or 'test' in content.lower():
                        print("    ⚠️ 检测到测试数据特征")
                    else:
                        print("    ✅ 可能是真实数据")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_playwright():
    """检查Playwright安装状态"""
    print("\n" + "="*60)
    print("4. 检查Playwright状态")
    print("="*60)
    
    try:
        import playwright
        print("✅ playwright 模块已安装")
        
        from playwright.async_api import async_playwright
        print("✅ async_playwright 可以导入")
        
        # 检查浏览器是否安装
        import subprocess
        result = subprocess.run(['playwright', 'install', '--dry-run'], 
                              capture_output=True, text=True)
        if 'chromium' in result.stdout.lower():
            print("✅ Chromium 浏览器已安装")
        else:
            print("⚠️ Chromium 浏览器可能未安装")
            print("   运行: playwright install chromium")
        
        return True
        
    except ImportError:
        print("❌ playwright 未安装")
        print("   运行: pip install playwright")
        print("   然后: playwright install chromium")
        return False
    except Exception as e:
        print(f"⚠️ 检查出错: {e}")
        return False

def check_tencent_exporter():
    """检查TencentDocAutoExporter类"""
    print("\n" + "="*60)
    print("5. 检查TencentDocAutoExporter")
    print("="*60)
    
    try:
        # 查找类定义
        import os
        for root, dirs, files in os.walk('/root/projects/tencent-doc-manager'):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if 'class TencentDocAutoExporter' in content:
                            print(f"✅ 找到TencentDocAutoExporter类")
                            print(f"   位置: {file_path}")
                            
                            # 检查关键方法
                            if 'async def export_document' in content:
                                print("   ✅ export_document 方法存在")
                            if 'async def login_with_cookies' in content:
                                print("   ✅ login_with_cookies 方法存在")
                            
                            return file_path
                    except:
                        pass
        
        print("❌ 未找到TencentDocAutoExporter类")
        return None
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return None

def analyze_failure():
    """分析失败原因"""
    print("\n" + "="*60)
    print("6. 失败原因分析")
    print("="*60)
    
    # 检查complete_workflow_ui.py中的逻辑
    workflow_path = Path('/root/projects/tencent-doc-manager/complete_workflow_ui.py')
    if workflow_path.exists():
        with open(workflow_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找关键代码
        if 'except ImportError:' in content:
            print("⚠️ complete_workflow_ui.py 中存在ImportError处理")
            print("   这可能导致fallback到模拟下载")
        
        if '模拟下载' in content or '张三' in content:
            print("⚠️ 代码中包含模拟下载逻辑")
            
            # 找到具体位置
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '模拟下载' in line:
                    print(f"   第{i+1}行: 发现'模拟下载'")
                if '张三' in line:
                    print(f"   第{i+1}行: 发现测试数据'张三'")
    
    print("\n可能的原因:")
    print("1. ImportError导致使用fallback模拟下载")
    print("2. download_file_from_url函数执行失败")
    print("3. Playwright浏览器自动化失败")
    print("4. Cookie认证失败")
    print("5. 腾讯文档反爬虫机制")

def main():
    """主调试函数"""
    print("🔍 腾讯文档下载功能调试")
    print("="*60)
    
    # 1. 测试导入
    if not test_import():
        print("\n❌ 模块导入失败，这是根本原因！")
        return
    
    # 2. 检查配置
    config = test_config()
    if not config:
        print("\n❌ 配置文件问题")
        return
    
    # 3. 检查Playwright
    playwright_ok = check_playwright()
    if not playwright_ok:
        print("\n⚠️ Playwright未正确安装，可能影响下载")
    
    # 4. 检查TencentDocAutoExporter
    exporter_path = check_tencent_exporter()
    if not exporter_path:
        print("\n❌ TencentDocAutoExporter类缺失")
    
    # 5. 测试下载
    download_result = test_download_function()
    
    # 6. 分析失败原因
    analyze_failure()
    
    print("\n" + "="*60)
    print("诊断完成")
    print("="*60)

if __name__ == "__main__":
    main()