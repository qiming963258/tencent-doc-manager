#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档管理系统 - 8094端口优化版
结合8093成功经验，解决502超时问题
"""

import os
import sys
import json
import time
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from flask import Flask, jsonify, request, send_file, render_template_string
from flask_cors import CORS
import logging

# 添加项目路径
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'production' / 'core_modules'))

# 导入核心模块
from production.core_modules.tencent_export_automation import UnifiedDownloadInterface
from production.core_modules.adaptive_table_comparator import AdaptiveTableComparator
from production.core_modules.simple_comparison_handler import simple_csv_compare
from enhanced_csv_comparison import enhanced_csv_compare

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局任务存储
download_tasks = {}
comparison_tasks = {}

class BackgroundTaskManager:
    """后台任务管理器，避免超时"""
    
    def __init__(self):
        self.tasks = {}
        self.lock = threading.Lock()
    
    def create_task(self, task_type="download"):
        """创建新任务"""
        task_id = str(uuid4())
        task = {
            'id': task_id,
            'type': task_type,
            'status': 'pending',
            'progress': 0,
            'message': '任务已创建',
            'created_at': datetime.now().isoformat(),
            'result': None,
            'error': None
        }
        with self.lock:
            self.tasks[task_id] = task
        return task_id
    
    def update_task(self, task_id, **kwargs):
        """更新任务状态"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].update(kwargs)
    
    def get_task(self, task_id):
        """获取任务状态"""
        with self.lock:
            return self.tasks.get(task_id, None)
    
    def run_async_task(self, task_id, async_func, *args, **kwargs):
        """在后台运行异步任务"""
        def _run():
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 更新状态为运行中
                self.update_task(task_id, status='running', progress=10, message='任务开始执行')
                
                # 运行异步函数
                result = loop.run_until_complete(async_func(*args, **kwargs))
                
                # 更新为完成
                self.update_task(
                    task_id, 
                    status='completed', 
                    progress=100, 
                    message='任务完成',
                    result=result
                )
            except Exception as e:
                logger.error(f"任务 {task_id} 执行失败: {e}")
                self.update_task(
                    task_id,
                    status='failed',
                    error=str(e),
                    message=f'任务失败: {str(e)}'
                )
            finally:
                loop.close()
        
        # 启动后台线程
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

# 初始化任务管理器
task_manager = BackgroundTaskManager()

async def download_with_progress(url, cookie, task_id):
    """带进度更新的下载函数"""
    try:
        # 更新进度：开始下载
        task_manager.update_task(task_id, progress=20, message='正在连接腾讯文档...')
        
        # 创建下载器实例
        downloader = UnifiedDownloadInterface()
        
        # 更新进度：登录
        task_manager.update_task(task_id, progress=40, message='正在验证权限...')
        
        # 执行下载
        result = await downloader.download(url, 'csv', cookie)
        
        # 更新进度：下载完成
        task_manager.update_task(task_id, progress=80, message='下载完成，正在处理文件...')
        
        if result.get('success'):
            file_path = result.get('file_path', '')
            # 确保文件存在
            if Path(file_path).exists():
                task_manager.update_task(task_id, progress=90, message='文件验证成功')
                return {
                    'success': True,
                    'file': file_path,
                    'size': Path(file_path).stat().st_size,
                    'download_time': result.get('download_time', 0)
                }
        
        raise Exception(result.get('error', '下载失败'))
        
    except Exception as e:
        logger.error(f"下载任务失败: {e}")
        raise

async def compare_with_progress(baseline_url, target_url, cookie, task_id):
    """带进度更新的对比函数"""
    try:
        # 下载基线文档
        task_manager.update_task(task_id, progress=10, message='正在下载基线文档...')
        downloader = UnifiedDownloadInterface()
        baseline_result = await downloader.download(baseline_url, 'csv', cookie)
        
        if not baseline_result.get('success'):
            raise Exception('基线文档下载失败')
        
        baseline_file = baseline_result.get('file_path')
        task_manager.update_task(task_id, progress=40, message='基线文档下载完成')
        
        # 下载目标文档
        task_manager.update_task(task_id, progress=50, message='正在下载目标文档...')
        target_result = await downloader.download(target_url, 'csv', cookie)
        
        if not target_result.get('success'):
            raise Exception('目标文档下载失败')
        
        target_file = target_result.get('file_path')
        task_manager.update_task(task_id, progress=80, message='目标文档下载完成')
        
        # 执行对比
        task_manager.update_task(task_id, progress=90, message='正在执行对比分析...')
        comparison_result = enhanced_csv_compare(baseline_file, target_file)
        
        task_manager.update_task(task_id, progress=95, message='对比完成')
        
        return {
            'success': True,
            'baseline_file': baseline_file,
            'target_file': target_file,
            'comparison': comparison_result,
            'baseline_download_time': baseline_result.get('download_time', 0),
            'target_download_time': target_result.get('download_time', 0)
        }
        
    except Exception as e:
        logger.error(f"对比任务失败: {e}")
        raise

@app.route('/')
def index():
    """主页"""
    return '''
    <h1>腾讯文档管理系统 v4.2 优化版</h1>
    <p>端口: 8094</p>
    <p>状态: 运行中</p>
    <p>特性: 后台任务处理，避免502超时</p>
    <ul>
        <li>POST /api/download - 下载文档（异步）</li>
        <li>POST /api/compare - 对比文档（异步）</li>
        <li>GET /api/task/{task_id} - 查询任务状态</li>
        <li>GET /api/status - 系统状态</li>
    </ul>
    '''

@app.route('/api/download', methods=['POST'])
def api_download():
    """异步下载接口"""
    try:
        data = request.json
        url = data.get('url', '')
        cookie = data.get('cookie', '')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        # 从配置加载cookie（如果没有提供）
        if not cookie:
            config_file = BASE_DIR / 'config.json'
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    cookie = config.get('cookie', '')
        
        # 创建后台任务
        task_id = task_manager.create_task('download')
        
        # 启动后台下载
        task_manager.run_async_task(
            task_id,
            download_with_progress,
            url, cookie, task_id
        )
        
        # 立即返回任务ID（避免超时）
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '下载任务已创建，请使用task_id查询进度',
            'check_url': f'/api/task/{task_id}'
        })
        
    except Exception as e:
        logger.error(f"创建下载任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """异步对比接口"""
    try:
        data = request.json
        baseline_url = data.get('baseline_url', '')
        target_url = data.get('target_url', '')
        cookie = data.get('cookie', '')
        
        if not baseline_url or not target_url:
            return jsonify({
                'success': False, 
                'error': 'E001: URL参数缺失',
                'details': 'baseline_url和target_url都是必需参数'
            }), 400
        
        # 从配置加载cookie
        if not cookie:
            config_file = BASE_DIR / 'config.json'
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    cookie = config.get('cookie', '')
        
        # 创建后台任务
        task_id = task_manager.create_task('compare')
        
        # 启动后台对比
        task_manager.run_async_task(
            task_id,
            compare_with_progress,
            baseline_url, target_url, cookie, task_id
        )
        
        # 立即返回任务ID
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '对比任务已创建，请使用task_id查询进度',
            'check_url': f'/api/task/{task_id}'
        })
        
    except Exception as e:
        logger.error(f"创建对比任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/task/<task_id>')
def get_task_status(task_id):
    """查询任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'task': task
    })

@app.route('/api/status')
def api_status():
    """系统状态"""
    return jsonify({
        'status': 'running',
        'version': '4.2-optimized',
        'port': 8094,
        'active_tasks': len(task_manager.tasks),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    logger.info("🚀 腾讯文档管理系统 v4.2 优化版启动")
    logger.info("📁 项目根目录: " + str(BASE_DIR))
    logger.info("🔧 特性: 后台任务处理，避免502超时")
    app.run(host='0.0.0.0', port=8094, debug=False)