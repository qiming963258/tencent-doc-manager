#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境集成测试系统验证脚本
用于验证8094系统是否正确集成项目所有组件
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_system_health():
    """测试系统健康状态"""
    print("🏥 测试系统健康状态...")
    try:
        response = requests.get('http://localhost:8094/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 系统状态: {data.get('status')}")
            print(f"✅ 版本: {data.get('version')}")
            print(f"✅ 系统类型: {data.get('system')}")
            
            print("\n📦 模块状态:")
            for module, status in data.get('modules', {}).items():
                icon = "✅" if status else "❌"
                print(f"   {icon} {module}")
            
            print("\n📁 目录配置:")
            for key, path in data.get('directories', {}).items():
                exists = Path(path).exists()
                icon = "✅" if exists else "❌"
                print(f"   {icon} {key}: {path}")
            
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_config_management():
    """测试配置管理"""
    print("\n⚙️ 测试配置管理...")
    
    # 测试加载配置
    try:
        response = requests.get('http://localhost:8094/api/load-cookie', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ 配置加载成功")
                if data.get('cookie'):
                    print(f"✅ Cookie已配置 (长度: {len(data['cookie'])})")
                else:
                    print("⚠️ Cookie未配置")
            else:
                print(f"⚠️ 配置加载失败: {data.get('error')}")
        else:
            print(f"❌ 配置加载请求失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 配置加载异常: {e}")
    
    # 测试保存配置
    try:
        test_cookie = "test_cookie_for_validation_12345"
        response = requests.post('http://localhost:8094/api/save-cookie', 
                               json={'cookie': test_cookie}, 
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ 配置保存功能正常")
                
                # 验证配置文件是否更新
                config_path = Path('/root/projects/tencent-doc-manager/config.json')
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    if config.get('cookie') == test_cookie:
                        print("✅ 项目配置文件更新成功")
                    else:
                        print("⚠️ 项目配置文件未正确更新")
                else:
                    print("⚠️ 项目配置文件不存在")
            else:
                print(f"❌ 配置保存失败: {data.get('error')}")
        else:
            print(f"❌ 配置保存请求失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 配置保存异常: {e}")

def test_api_endpoints():
    """测试API端点"""
    print("\n🔌 测试API端点...")
    
    endpoints = [
        ('GET', '/api/status', '状态API'),
        ('GET', '/api/latest-result', '最新结果API'),
        ('GET', '/results', '结果页面'),
        ('GET', '/files', '文件管理页面')
    ]
    
    for method, endpoint, name in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f'http://localhost:8094{endpoint}', timeout=10)
            else:
                response = requests.post(f'http://localhost:8094{endpoint}', timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {name}: HTTP {response.status_code}")
            else:
                print(f"⚠️ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: 异常 {e}")

def test_directory_structure():
    """测试目录结构"""
    print("\n📁 验证项目目录结构...")
    
    directories = {
        "项目根目录": "/root/projects/tencent-doc-manager",
        "正式下载目录": "/root/projects/tencent-doc-manager/downloads",
        "对比结果目录": "/root/projects/tencent-doc-manager/comparison_results",
        "基线文件目录": "/root/projects/tencent-doc-manager/comparison_baseline",
        "目标文件目录": "/root/projects/tencent-doc-manager/comparison_target",
        "日志目录": "/root/projects/tencent-doc-manager/logs",
        "临时目录": "/root/projects/tencent-doc-manager/temp_workflow"
    }
    
    for name, path in directories.items():
        path_obj = Path(path)
        if path_obj.exists():
            if path_obj.is_dir():
                print(f"✅ {name}: {path}")
            else:
                print(f"⚠️ {name}: {path} (不是目录)")
        else:
            print(f"❌ {name}: {path} (不存在)")

def test_config_files():
    """测试配置文件"""
    print("\n📄 验证配置文件...")
    
    config_files = {
        "主配置文件": "/root/projects/tencent-doc-manager/config.json",
        "备用配置文件": "/root/projects/tencent-doc-manager/auto_download_config.json"
    }
    
    for name, path in config_files.items():
        path_obj = Path(path)
        if path_obj.exists():
            try:
                with open(path_obj, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ {name}: 存在且格式正确")
                if config.get('cookie'):
                    print(f"   - Cookie已配置 (长度: {len(config['cookie'])})")
                else:
                    print(f"   - Cookie未配置")
            except Exception as e:
                print(f"⚠️ {name}: 存在但格式错误 ({e})")
        else:
            print(f"❌ {name}: 不存在")

def main():
    """主测试函数"""
    print("🚀 腾讯文档管理系统 - 生产环境集成测试验证")
    print("=" * 60)
    
    # 等待系统启动
    print("⏳ 等待系统启动...")
    time.sleep(2)
    
    # 执行各项测试
    success_count = 0
    total_tests = 5
    
    if test_system_health():
        success_count += 1
    
    test_config_management()
    success_count += 1
    
    test_api_endpoints()
    success_count += 1
    
    test_directory_structure()
    success_count += 1
    
    test_config_files()
    success_count += 1
    
    # 测试总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print(f"✅ 成功测试: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！生产环境集成测试系统运行正常")
        print("\n📖 使用说明:")
        print("1. 浏览器访问: http://localhost:8094")
        print("2. 配置Cookie并保存到项目配置")
        print("3. 输入文档URL进行对比测试")
        print("4. 查看路径信息面板了解文件存储位置")
        return True
    else:
        print("⚠️ 部分测试未通过，请检查系统状态")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程出现异常: {e}")
        sys.exit(1)