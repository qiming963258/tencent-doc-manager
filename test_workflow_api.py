#!/usr/bin/env python3
"""通过API启动工作流并监控执行"""

import json
import time
import requests
from datetime import datetime

def start_workflow():
    """启动工作流"""

    # 读取cookie
    with open('/root/projects/tencent-doc-manager/config/cookies.json', 'r') as f:
        cookie_data = json.load(f)
        cookie = cookie_data['current_cookies']

    # 准备请求数据
    data = {
        "baseline_url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",  # 出国销售计划表
        "target_url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",     # 同一个文档做测试
        "cookie": cookie,
        "advanced_settings": {
            "force_download": True,           # 强制下载最新版本
            "use_cached_target": False,       # 不使用缓存
            "enable_ai_analysis": True,       # 启用AI分析
            "upload_to_tencent": True,        # 上传到腾讯文档
            "generate_excel": True            # 生成Excel文件
        }
    }

    # 发送启动请求
    print("="*60)
    print(f"🚀 启动工作流 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    response = requests.post('http://localhost:8093/api/start', json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 工作流已启动: {result.get('message')}")
        print(f"📝 执行ID: {result.get('execution_id')}")
        return True
    else:
        print(f"❌ 启动失败: {response.text}")
        return False

def monitor_workflow():
    """监控工作流执行状态"""

    print("\n📊 开始监控工作流执行...")
    print("-"*50)

    start_time = time.time()
    last_status = None
    last_progress = 0
    upload_url = None
    error_logs = []

    while True:
        try:
            # 获取状态
            response = requests.get('http://localhost:8093/api/status', timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                progress = data.get('progress', 0)
                current_step = data.get('current_step', '未知')
                results = data.get('results', {})
                logs = data.get('logs', [])

                # 打印状态变化
                if status != last_status or abs(progress - last_progress) >= 5:
                    elapsed = int(time.time() - start_time)
                    print(f"[{elapsed:3d}秒] 状态:{status:10} 进度:{progress:3}% 步骤:{current_step}")
                    last_status = status
                    last_progress = progress

                # 收集错误日志
                for log in logs:
                    if log.get('level') == 'ERROR' or '失败' in log.get('message', ''):
                        error_logs.append(log)

                # 检查完成状态
                if status == "completed":
                    upload_url = results.get('upload_url')
                    print("\n" + "="*50)
                    print("✅ 工作流执行完成!")
                    print(f"⏱️  总耗时: {int(time.time() - start_time)}秒")
                    print("="*50)

                    # 打印结果详情
                    print("\n📋 执行结果:")
                    print(f"  基线文件: {results.get('baseline_file', 'N/A')}")
                    print(f"  目标文件: {results.get('target_file', 'N/A')}")
                    print(f"  涂色文件: {results.get('marked_file', 'N/A')}")
                    print(f"  打分文件: {results.get('score_file', 'N/A')}")
                    print(f"  综合文件: {results.get('comprehensive_file', 'N/A')}")

                    if upload_url:
                        print(f"\n🔗 上传URL: {upload_url}")
                    else:
                        print(f"\n❌ 上传失败（URL为空）")

                    # 打印错误日志
                    if error_logs:
                        print("\n⚠️ 发现以下错误:")
                        for log in error_logs[-5:]:  # 只显示最后5个错误
                            print(f"  [{log.get('timestamp')}] {log.get('message')}")

                    break

                # 检查错误状态
                elif status == "error":
                    print("\n" + "="*50)
                    print("❌ 工作流执行失败!")
                    print("="*50)

                    # 打印错误信息
                    if logs:
                        print("\n最后的日志:")
                        for log in logs[-10:]:
                            level = log.get('level', 'INFO')
                            msg = log.get('message', '')
                            print(f"  [{level}] {msg}")
                    break

        except Exception as e:
            print(f"⚠️ 获取状态失败: {e}")

        # 超时检查（10分钟）
        if time.time() - start_time > 600:
            print("\n⏰ 执行超时（10分钟）")
            break

        time.sleep(2)

    return upload_url

def check_upload_result(upload_url):
    """检查上传结果"""

    print("\n" + "="*60)
    print("📊 上传结果分析")
    print("="*60)

    if upload_url:
        print(f"✅ 成功获取上传URL:")
        print(f"   {upload_url}")
        print("\n验证步骤:")
        print("  1. 点击上面的URL访问腾讯文档")
        print("  2. 检查是否有涂色标记")
        print("  3. 查看文档名称是否包含'marked'")

        # 尝试验证URL
        try:
            response = requests.head(upload_url, allow_redirects=True, timeout=5)
            if response.status_code < 400:
                print(f"\n✅ URL可访问 (HTTP {response.status_code})")
            else:
                print(f"\n⚠️ URL返回错误 (HTTP {response.status_code})")
        except Exception as e:
            print(f"\n⚠️ 无法自动验证URL: {e}")
    else:
        print("❌ 未获取到上传URL")
        print("\n可能的原因:")
        print("  1. 存储空间检查仍然阻止上传")
        print("  2. Cookie已过期（上次更新: 2025-09-19）")
        print("  3. 上传模块未正确初始化")
        print("  4. 网络连接问题")

        # 检查日志文件
        print("\n建议检查:")
        print("  - /tmp/8093_new.log - 查看详细错误")
        print("  - 存储空间是否仍有95%限制")
        print("  - Cookie是否需要更新")

    return upload_url

def main():
    """主函数"""

    print("🔧 腾讯文档智能监控系统 - 全链路测试")
    print("📅 " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("\n测试步骤:")
    print("  1. 启动工作流（通过API）")
    print("  2. 实时监控执行状态")
    print("  3. 获取上传结果")
    print("  4. 验证URL有效性")

    # 启动工作流
    if not start_workflow():
        print("❌ 无法启动工作流")
        return None

    # 监控执行
    upload_url = monitor_workflow()

    # 检查结果
    final_url = check_upload_result(upload_url)

    # 最终报告
    print("\n" + "="*60)
    print("🏁 测试完成报告")
    print("="*60)

    if final_url:
        print(f"✅ 测试成功!")
        print(f"📎 最终上传URL: {final_url}")
    else:
        print(f"❌ 测试失败，未获取到有效的上传URL")

    return final_url

if __name__ == "__main__":
    result = main()

    # 返回码
    import sys
    sys.exit(0 if result else 1)