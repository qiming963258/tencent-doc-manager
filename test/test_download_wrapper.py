#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试下载包装器 - 带超时控制
"""

import signal
import time
from pathlib import Path
from datetime import datetime

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("下载超时")

def download_with_timeout(url, cookie=None, timeout=30):
    """
    带超时的下载测试
    """
    # 设置超时
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        print(f"[测试] 开始下载: {url}")
        print(f"[测试] Cookie长度: {len(cookie) if cookie else 0}")
        
        # 检查Cookie有效性
        if not cookie or len(cookie) < 100:
            return {
                'success': False,
                'error': 'Cookie无效或未提供（有效Cookie通常超过100字符）'
            }
        
        # 尝试导入下载函数
        try:
            from auto_download_ui_system import download_file_from_url
        except ImportError as e:
            return {
                'success': False,
                'error': f'无法导入下载函数: {e}'
            }
        
        # 保存Cookie到配置
        import json
        config_file = Path('/root/projects/tencent-doc-manager/config.json')
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({'cookie': cookie}, f, ensure_ascii=False, indent=2)
            print(f"[测试] Cookie已保存到配置文件")
        except Exception as e:
            return {
                'success': False,
                'error': f'保存Cookie失败: {e}'
            }
        
        # 执行下载
        result = download_file_from_url(url, format_type='csv')
        
        # 取消超时
        signal.alarm(0)
        
        return result
        
    except TimeoutError:
        signal.alarm(0)
        return {
            'success': False,
            'error': f'下载超时（{timeout}秒）- 可能是Cookie无效或网络问题'
        }
    except Exception as e:
        signal.alarm(0)
        return {
            'success': False,
            'error': f'下载失败: {str(e)}'
        }

if __name__ == "__main__":
    # 测试用例
    test_url = "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R"
    test_cookie = "test_cookie_123"  # 这是个无效的测试Cookie
    
    result = download_with_timeout(test_url, test_cookie, timeout=10)
    print(f"\n测试结果: {result}")