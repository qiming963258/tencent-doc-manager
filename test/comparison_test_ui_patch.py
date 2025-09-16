#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
8094端口并行下载补丁
解决502超时问题 - 将串行下载改为并行下载
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import shutil

def parallel_download_handler(request_data, download_func, base_dir):
    """
    并行下载处理器 - 同时下载基线和目标文件
    
    Args:
        request_data: 包含基线和目标URL及Cookie的字典
        download_func: download_file_from_url函数引用
        base_dir: 基础目录路径
    
    Returns:
        dict: 包含两个文件下载结果的字典
    """
    
    BASELINE_DIR = base_dir / 'comparison_baseline'
    TARGET_DIR = base_dir / 'comparison_target'
    
    # 确保目录存在
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    
    results = {
        'baseline': None,
        'target': None,
        'total_time': 0,
        'parallel': True
    }
    
    start_time = time.time()
    
    # 准备下载任务
    download_tasks = []
    
    # 基线文件任务
    baseline_url = request_data.get('baseline_url')
    baseline_cookie = request_data.get('baseline_cookie', '')
    
    if baseline_url:
        download_tasks.append({
            'type': 'baseline',
            'url': baseline_url,
            'cookie': baseline_cookie,
            'dest_dir': BASELINE_DIR
        })
    
    # 目标文件任务
    target_url = request_data.get('target_url')
    target_cookie = request_data.get('target_cookie', '')
    
    if target_url:
        download_tasks.append({
            'type': 'target',
            'url': target_url,
            'cookie': target_cookie,
            'dest_dir': TARGET_DIR
        })
    
    # 定义下载函数
    def download_file(task):
        """单个文件下载任务"""
        task_type = task['type']
        print(f"\n[并行下载] 开始下载{task_type}文件: {task['url'][:50]}...")
        
        # 保存Cookie到配置文件
        if task['cookie']:
            config_file = base_dir / 'config.json'
            try:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump({'cookie': task['cookie']}, f, ensure_ascii=False, indent=2)
                print(f"[{task_type}] Cookie已保存，长度: {len(task['cookie'])}")
            except Exception as e:
                print(f"[{task_type}] 保存Cookie失败: {e}")
        
        # 执行下载
        task_start = time.time()
        try:
            result = download_func(task['url'], format_type='csv')
            download_time = time.time() - task_start
            print(f"[{task_type}] 下载完成，耗时: {download_time:.2f}秒")
            
            # 处理下载结果
            if result and result.get('success'):
                if result.get('files'):
                    first_file = result['files'][0]
                    source_path = Path(first_file.get('path', ''))
                    if source_path.exists():
                        dest_path = task['dest_dir'] / source_path.name
                        shutil.copy(source_path, dest_path)
                        print(f"[{task_type}] 文件已复制到: {dest_path}")
                        
                        return {
                            'type': task_type,
                            'success': True,
                            'path': str(dest_path),
                            'name': dest_path.name,
                            'size': f"{dest_path.stat().st_size:,} bytes",
                            'download_time': download_time,
                            'result': result
                        }
            
            return {
                'type': task_type,
                'success': False,
                'error': result.get('error', '下载失败'),
                'download_time': download_time
            }
            
        except Exception as e:
            download_time = time.time() - task_start
            print(f"[{task_type}] 下载异常: {e}")
            return {
                'type': task_type,
                'success': False,
                'error': str(e),
                'download_time': download_time
            }
    
    # 使用线程池并行执行下载
    print(f"[并行下载] 启动{len(download_tasks)}个并行下载任务...")
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        # 提交所有下载任务
        future_to_task = {executor.submit(download_file, task): task for task in download_tasks}
        
        # 等待所有任务完成
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                download_result = future.result(timeout=70)  # 单个任务最多70秒
                
                if download_result['type'] == 'baseline':
                    results['baseline'] = download_result
                elif download_result['type'] == 'target':
                    results['target'] = download_result
                    
            except Exception as e:
                print(f"[并行下载] 任务异常: {e}")
                if task['type'] == 'baseline':
                    results['baseline'] = {
                        'success': False,
                        'error': str(e)
                    }
                elif task['type'] == 'target':
                    results['target'] = {
                        'success': False,
                        'error': str(e)
                    }
    
    total_time = time.time() - start_time
    results['total_time'] = total_time
    
    print(f"\n[并行下载] 所有任务完成，总耗时: {total_time:.2f}秒")
    print(f"[并行下载] 基线文件: {'成功' if results['baseline'] and results['baseline'].get('success') else '失败'}")
    print(f"[并行下载] 目标文件: {'成功' if results['target'] and results['target'].get('success') else '失败'}")
    
    return results


# 导出补丁函数
def apply_parallel_download_patch():
    """
    应用并行下载补丁到comparison_test_ui.py
    这个函数需要在comparison_test_ui.py中集成
    """
    print("✨ 并行下载补丁已准备就绪")
    print("📌 使用方法：")
    print("1. 在comparison_test_ui.py中导入: from comparison_test_ui_patch import parallel_download_handler")
    print("2. 替换compare函数中的串行下载部分")
    print("3. 调用parallel_download_handler(data, download_file_from_url, BASE_DIR)")
    return True


if __name__ == "__main__":
    print("🚀 8094端口并行下载补丁")
    print("=" * 60)
    print("此补丁将串行下载改为并行下载，解决502超时问题")
    print("预期效果：")
    print("- 原耗时: ~105秒（串行）")
    print("- 新耗时: ~45秒（并行）")
    print("- 避免502 Bad Gateway错误")
    apply_parallel_download_patch()