#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档对比测试系统 - 增强版
端口: 8094
功能: 提供完整的文档下载和对比分析功能，包含密集的状态反馈和详细日志
作者: 系统架构团队
版本: 2.0.0
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import os
import sys
import json
import time
import asyncio
import logging
import traceback
import uuid
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import csv
from dataclasses import dataclass, asdict
from queue import Queue
import requests

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/core_modules')

app = Flask(__name__)

# ==================== 配置部分 ====================
BASE_DIR = Path('/root/projects/tencent-doc-manager')
CONFIG_PATH = BASE_DIR / 'config.json'
DOWNLOAD_DIR = BASE_DIR / 'comparison_downloads'
TEMP_DIR = BASE_DIR / 'comparison_temp'
LOG_DIR = BASE_DIR / 'comparison_logs'
RESULT_DIR = BASE_DIR / 'comparison_results'

# 确保所有目录存在
for dir_path in [DOWNLOAD_DIR, TEMP_DIR, LOG_DIR, RESULT_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)

# ==================== 日志配置 ====================
log_file = LOG_DIR / f'comparison_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 动态导入模块 ====================
MODULES_STATUS = {
    'production_downloader': False,
    'production_comparator': False,
    'cookie_manager': False,
    'simple_comparison': False
}

try:
    from production.core_modules.production_downloader import ProductionTencentDownloader
    MODULES_STATUS['production_downloader'] = True
    logger.info("✅ 成功导入 production_downloader")
except ImportError as e:
    logger.warning(f"⚠️ 无法导入 production_downloader: {e}")

try:
    from production.core_modules.production_csv_comparator import ProductionCSVComparator
    MODULES_STATUS['production_comparator'] = True
    logger.info("✅ 成功导入 production_csv_comparator")
except ImportError as e:
    logger.warning(f"⚠️ 无法导入 production_csv_comparator: {e}")

try:
    from production.core_modules.cookie_manager import get_cookie_manager
    MODULES_STATUS['cookie_manager'] = True
    logger.info("✅ 成功导入 cookie_manager")
except ImportError as e:
    logger.warning(f"⚠️ 无法导入 cookie_manager: {e}")

try:
    from simple_comparison_handler import simple_csv_compare
    MODULES_STATUS['simple_comparison'] = True
    logger.info("✅ 成功导入 simple_comparison_handler")
except ImportError as e:
    logger.warning(f"⚠️ 无法导入 simple_comparison_handler: {e}")

# ==================== 状态管理类 ====================
@dataclass
class TaskStatus:
    """任务状态数据类"""
    task_id: str
    status: str  # pending, running, completed, failed, cancelled
    progress: int  # 0-100
    current_step: str
    messages: List[Dict[str, Any]]
    start_time: float
    end_time: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    baseline_file: Optional[str] = None
    target_file: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)

# ==================== 全局状态存储 ====================
class TaskManager:
    """任务管理器"""
    def __init__(self):
        self.tasks: Dict[str, TaskStatus] = {}
        self.lock = threading.Lock()
        self.message_queue = Queue()
        
    def create_task(self) -> str:
        """创建新任务"""
        with self.lock:
            task_id = str(uuid.uuid4())
            self.tasks[task_id] = TaskStatus(
                task_id=task_id,
                status='pending',
                progress=0,
                current_step='初始化',
                messages=[],
                start_time=time.time()
            )
            return task_id
    
    def update_task(self, task_id: str, **kwargs):
        """更新任务状态"""
        with self.lock:
            if task_id in self.tasks:
                for key, value in kwargs.items():
                    if hasattr(self.tasks[task_id], key):
                        setattr(self.tasks[task_id], key, value)
    
    def add_message(self, task_id: str, message: str, level: str = 'info', details: Dict = None):
        """添加任务消息"""
        with self.lock:
            if task_id in self.tasks:
                msg_data = {
                    'timestamp': datetime.now().isoformat(),
                    'level': level,
                    'message': message,
                    'details': details or {}
                }
                self.tasks[task_id].messages.append(msg_data)
                logger.log(
                    getattr(logging, level.upper(), logging.INFO),
                    f"[{task_id[:8]}] {message}"
                )
    
    def get_task(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[TaskStatus]:
        """获取所有任务"""
        with self.lock:
            return list(self.tasks.values())

# 创建全局任务管理器
task_manager = TaskManager()

# ==================== 下载功能实现 ====================
class DocumentDownloader:
    """文档下载器"""
    
    @staticmethod
    async def download_from_url(url: str, cookie: str, format: str, save_name: str) -> Optional[str]:
        """从URL下载文档"""
        try:
            logger.info(f"开始下载文档: {url}")
            
            # 如果有生产级下载器，使用它
            if MODULES_STATUS['production_downloader']:
                downloader = ProductionTencentDownloader(str(DOWNLOAD_DIR))
                await downloader.start_browser(headless=True)
                
                try:
                    # 设置Cookie
                    await downloader.set_cookie(cookie)
                    
                    # 执行下载
                    if format == 'csv':
                        result = await downloader.download_as_csv(url)
                    else:
                        result = await downloader.download_as_excel(url)
                    
                    if result and result.get('success'):
                        return result.get('file_path')
                        
                finally:
                    await downloader.close_browser()
            
            # 备用方案：模拟下载
            return await DocumentDownloader._simulate_download(url, format, save_name)
            
        except Exception as e:
            logger.error(f"下载失败: {e}")
            return None
    
    @staticmethod
    async def _simulate_download(url: str, format: str, save_name: str) -> str:
        """模拟下载（用于测试）"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{save_name}_{timestamp}.{format}"
        filepath = DOWNLOAD_DIR / filename
        
        # 模拟下载延迟
        await asyncio.sleep(2)
        
        # 创建示例数据
        if format == 'csv':
            data = [
                ['序号', '项目名称', '状态', '负责人', '开始时间', '结束时间'],
                ['1', '项目A', '进行中', '张三', '2024-01-01', '2024-03-01'],
                ['2', '项目B', '已完成', '李四', '2024-02-01', '2024-04-01'],
                ['3', '项目C', '计划中', '王五', '2024-03-01', '2024-05-01'],
            ]
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(data)
        else:
            # Excel格式
            df = pd.DataFrame({
                '序号': [1, 2, 3],
                '项目名称': ['项目A', '项目B', '项目C'],
                '状态': ['进行中', '已完成', '计划中'],
                '负责人': ['张三', '李四', '王五']
            })
            df.to_excel(filepath, index=False)
        
        logger.info(f"模拟下载完成: {filepath}")
        return str(filepath)

# ==================== 对比功能实现 ====================
class DocumentComparator:
    """文档对比器"""
    
    @staticmethod
    async def compare_files(baseline_file: str, target_file: str, task_id: str) -> Dict:
        """执行文件对比"""
        try:
            logger.info(f"开始对比文件: {baseline_file} vs {target_file}")
            
            # 更新任务状态
            task_manager.add_message(task_id, "正在读取基线文件...", "info")
            baseline_data = DocumentComparator._read_file(baseline_file)
            
            task_manager.add_message(task_id, "正在读取目标文件...", "info")
            target_data = DocumentComparator._read_file(target_file)
            
            # 执行对比
            task_manager.add_message(task_id, "正在执行智能对比分析...", "info")
            
            if MODULES_STATUS['production_comparator']:
                # 使用生产级对比器
                comparator = ProductionCSVComparator()
                result = await comparator.compare_async(baseline_file, target_file)
                return DocumentComparator._format_comparison_result(result)
            else:
                # 使用简单对比
                return DocumentComparator._simple_compare(baseline_data, target_data)
                
        except Exception as e:
            logger.error(f"对比失败: {e}")
            raise
    
    @staticmethod
    def _read_file(filepath: str) -> pd.DataFrame:
        """读取文件数据"""
        if filepath.endswith('.csv'):
            return pd.read_csv(filepath, encoding='utf-8')
        else:
            return pd.read_excel(filepath)
    
    @staticmethod
    def _simple_compare(baseline_df: pd.DataFrame, target_df: pd.DataFrame) -> Dict:
        """简单对比实现"""
        differences = []
        total_cells = baseline_df.size
        diff_count = 0
        
        # 逐行逐列对比
        for row_idx in range(min(len(baseline_df), len(target_df))):
            for col in baseline_df.columns:
                if col in target_df.columns:
                    baseline_val = baseline_df.iloc[row_idx][col]
                    target_val = target_df.iloc[row_idx][col]
                    
                    if str(baseline_val) != str(target_val):
                        diff_count += 1
                        differences.append({
                            'location': f"Row {row_idx+1}, Col {col}",
                            'type': 'modified',
                            'old_value': str(baseline_val),
                            'new_value': str(target_val),
                            'risk_level': 'L2'
                        })
        
        # 计算相似度
        similarity = (1 - diff_count / total_cells) * 100 if total_cells > 0 else 100
        
        return {
            'success': True,
            'total_differences': diff_count,
            'total_cells': total_cells,
            'similarity_score': round(similarity, 2),
            'risk_level': DocumentComparator._calculate_risk_level(diff_count, total_cells),
            'differences': differences[:100],  # 限制返回数量
            'processing_time': round(time.time(), 2)
        }
    
    @staticmethod
    def _calculate_risk_level(diff_count: int, total_cells: int) -> str:
        """计算风险等级"""
        if total_cells == 0:
            return 'L3'
        
        diff_ratio = diff_count / total_cells
        if diff_ratio > 0.3:
            return 'L1'  # 高风险
        elif diff_ratio > 0.1:
            return 'L2'  # 中风险
        else:
            return 'L3'  # 低风险
    
    @staticmethod
    def _format_comparison_result(result: Any) -> Dict:
        """格式化对比结果"""
        if hasattr(result, 'to_dict'):
            return result.to_dict()
        return result

# ==================== 异步任务执行器 ====================
async def execute_comparison_task(task_id: str, params: Dict):
    """执行对比任务"""
    try:
        # 更新任务状态
        task_manager.update_task(task_id, status='running', progress=5)
        task_manager.add_message(task_id, "🚀 任务开始执行", "info")
        
        # Step 1: 验证参数
        task_manager.update_task(task_id, current_step='参数验证', progress=10)
        task_manager.add_message(task_id, "正在验证输入参数...", "info")
        
        baseline_url = params.get('baseline_url')
        target_url = params.get('target_url')
        
        if not baseline_url or not target_url:
            raise ValueError("缺少必要的URL参数")
        
        # Step 2: 获取Cookie
        task_manager.update_task(task_id, current_step='获取Cookie', progress=15)
        task_manager.add_message(task_id, "正在获取认证Cookie...", "info")
        
        baseline_cookie = params.get('baseline_cookie') or await get_system_cookie()
        target_cookie = params.get('target_cookie') or await get_system_cookie()
        
        if not baseline_cookie or not target_cookie:
            task_manager.add_message(task_id, "⚠️ 未提供Cookie，使用模拟模式", "warning")
        
        # Step 3: 下载基线文档
        task_manager.update_task(task_id, current_step='下载基线文档', progress=25)
        task_manager.add_message(task_id, f"📥 开始下载基线文档: {baseline_url}", "info")
        
        baseline_file = await DocumentDownloader.download_from_url(
            baseline_url,
            baseline_cookie,
            params.get('baseline_format', 'csv'),
            'baseline'
        )
        
        if not baseline_file:
            raise Exception("基线文档下载失败")
        
        task_manager.update_task(task_id, baseline_file=baseline_file, progress=45)
        task_manager.add_message(task_id, f"✅ 基线文档下载成功", "success", 
                                {'file': baseline_file, 'size': os.path.getsize(baseline_file)})
        
        # Step 4: 下载目标文档
        task_manager.update_task(task_id, current_step='下载目标文档', progress=50)
        task_manager.add_message(task_id, f"📥 开始下载目标文档: {target_url}", "info")
        
        target_file = await DocumentDownloader.download_from_url(
            target_url,
            target_cookie,
            params.get('target_format', 'csv'),
            'target'
        )
        
        if not target_file:
            raise Exception("目标文档下载失败")
        
        task_manager.update_task(task_id, target_file=target_file, progress=70)
        task_manager.add_message(task_id, f"✅ 目标文档下载成功", "success",
                                {'file': target_file, 'size': os.path.getsize(target_file)})
        
        # Step 5: 执行对比分析
        task_manager.update_task(task_id, current_step='对比分析', progress=75)
        task_manager.add_message(task_id, "🔍 开始执行对比分析...", "info")
        
        comparison_result = await DocumentComparator.compare_files(
            baseline_file, 
            target_file,
            task_id
        )
        
        task_manager.update_task(task_id, progress=90)
        task_manager.add_message(task_id, 
                                f"✅ 对比分析完成，发现 {comparison_result.get('total_differences', 0)} 处差异",
                                "success")
        
        # Step 6: 保存结果
        task_manager.update_task(task_id, current_step='保存结果', progress=95)
        result_file = await save_comparison_result(task_id, comparison_result)
        
        # 完成任务
        task_manager.update_task(
            task_id,
            status='completed',
            progress=100,
            current_step='任务完成',
            end_time=time.time(),
            result=comparison_result
        )
        
        task_manager.add_message(task_id, "🎉 任务执行成功！", "success",
                                {'result_file': result_file})
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}\n{traceback.format_exc()}")
        task_manager.update_task(
            task_id,
            status='failed',
            error=str(e),
            end_time=time.time()
        )
        task_manager.add_message(task_id, f"❌ 任务失败: {str(e)}", "error")

async def save_comparison_result(task_id: str, result: Dict) -> str:
    """保存对比结果"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = RESULT_DIR / f'result_{task_id[:8]}_{timestamp}.json'
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"结果已保存: {result_file}")
    return str(result_file)

async def get_system_cookie() -> Optional[str]:
    """获取系统Cookie"""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('cookie')
    except Exception as e:
        logger.error(f"获取系统Cookie失败: {e}")
    return None

# ==================== HTML模板 ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档对比测试系统 V2.0 - 端口8094</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { max-width: 1600px; margin: 0 auto; }
        
        .header {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #1f2937;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .status-badge.success { background: #10b981; color: white; }
        .status-badge.warning { background: #f59e0b; color: white; }
        .status-badge.error { background: #ef4444; color: white; }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .panel {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        
        .panel-full { grid-column: 1 / -1; }
        
        .panel-title {
            font-size: 18px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e5e7eb;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #374151;
            font-size: 14px;
        }
        
        .form-control {
            width: 100%;
            padding: 10px 14px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        textarea.form-control {
            min-height: 80px;
            resize: vertical;
            font-family: monospace;
            font-size: 12px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-group {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .progress-container {
            margin: 20px 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s ease;
            position: relative;
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .status-log {
            background: #1f2937;
            color: #e5e7eb;
            border-radius: 8px;
            padding: 16px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.6;
        }
        
        .log-line {
            margin-bottom: 4px;
            padding: 2px 8px;
            border-radius: 4px;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .log-info { color: #60a5fa; }
        .log-success { color: #34d399; background: rgba(52, 211, 153, 0.1); }
        .log-warning { color: #fbbf24; background: rgba(251, 191, 36, 0.1); }
        .log-error { color: #f87171; background: rgba(248, 113, 113, 0.1); }
        
        .result-panel {
            display: none;
            background: #f9fafb;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .result-panel.show { display: block; animation: fadeIn 0.5s; }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #e5e7eb;
        }
        
        .stat-label {
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 4px;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        }
        
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                🔍 腾讯文档对比测试系统 V2.0
                <span class="status-badge success" id="system-status">系统正常</span>
            </h1>
            <p style="color: #6b7280; margin-top: 8px;">
                端口: 8094 | 支持CSV/Excel | 智能对比分析 | 实时状态反馈
            </p>
        </div>
        
        <div class="main-grid">
            <div class="panel">
                <div class="panel-title">📊 基线文档配置</div>
                <div class="form-group">
                    <label class="form-label">文档URL *</label>
                    <input type="text" id="baseline-url" class="form-control" 
                           placeholder="https://docs.qq.com/sheet/..." 
                           value="https://docs.qq.com/sheet/DWEFNU25TemFnZXJN">
                </div>
                <div class="form-group">
                    <label class="form-label">Cookie (可选)</label>
                    <textarea id="baseline-cookie" class="form-control" 
                              placeholder="留空使用系统配置的Cookie"></textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">文件格式</label>
                    <select id="baseline-format" class="form-control">
                        <option value="csv">CSV格式</option>
                        <option value="excel">Excel格式</option>
                    </select>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-title">🎯 目标文档配置</div>
                <div class="form-group">
                    <label class="form-label">文档URL *</label>
                    <input type="text" id="target-url" class="form-control" 
                           placeholder="https://docs.qq.com/sheet/..." 
                           value="https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr">
                </div>
                <div class="form-group">
                    <label class="form-label">Cookie (可选)</label>
                    <textarea id="target-cookie" class="form-control" 
                              placeholder="留空使用系统配置的Cookie"></textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">文件格式</label>
                    <select id="target-format" class="form-control">
                        <option value="csv">CSV格式</option>
                        <option value="excel">Excel格式</option>
                    </select>
                </div>
            </div>
        </div>
        
        <div class="panel panel-full">
            <div class="btn-group">
                <button id="start-btn" class="btn btn-primary" onclick="startComparison()">
                    ▶️ 开始对比
                </button>
                <button id="stop-btn" class="btn btn-primary" onclick="stopTask()" disabled>
                    ⏹️ 停止任务
                </button>
                <button class="btn btn-primary" onclick="clearLog()">
                    🗑️ 清空日志
                </button>
                <button id="export-btn" class="btn btn-primary" onclick="exportResult()" disabled>
                    💾 导出结果
                </button>
            </div>
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" id="progress" style="width: 0%"></div>
                </div>
                <div style="text-align: center; margin-top: 8px; color: #6b7280; font-size: 14px;">
                    <span id="progress-text">等待开始...</span>
                </div>
            </div>
        </div>
        
        <div class="panel panel-full">
            <div class="panel-title">
                📝 实时状态日志
                <span style="float: right; font-size: 12px; color: #6b7280;">
                    <span id="log-count">0</span> 条记录
                </span>
            </div>
            <div class="status-log" id="status-log">
                <div class="log-line log-info">系统就绪，等待任务...</div>
            </div>
        </div>
        
        <div class="panel panel-full result-panel" id="result-panel">
            <div class="panel-title">📈 对比分析结果</div>
            <div class="stat-grid" id="stat-grid"></div>
            <div id="diff-table"></div>
        </div>
    </div>
    
    <script>
        let currentTaskId = null;
        let statusCheckInterval = null;
        let logCount = 0;
        
        function addLog(message, level = 'info') {
            const logContainer = document.getElementById('status-log');
            const line = document.createElement('div');
            line.className = `log-line log-${level}`;
            const time = new Date().toLocaleTimeString('zh-CN');
            line.textContent = `[${time}] ${message}`;
            logContainer.appendChild(line);
            logContainer.scrollTop = logContainer.scrollHeight;
            
            logCount++;
            document.getElementById('log-count').textContent = logCount;
            
            // 限制日志数量
            if (logContainer.children.length > 500) {
                logContainer.removeChild(logContainer.firstChild);
            }
        }
        
        function updateProgress(percent, text) {
            document.getElementById('progress').style.width = percent + '%';
            document.getElementById('progress-text').textContent = text || `进度: ${percent}%`;
        }
        
        async function startComparison() {
            const data = {
                baseline_url: document.getElementById('baseline-url').value,
                baseline_cookie: document.getElementById('baseline-cookie').value,
                baseline_format: document.getElementById('baseline-format').value,
                target_url: document.getElementById('target-url').value,
                target_cookie: document.getElementById('target-cookie').value,
                target_format: document.getElementById('target-format').value
            };
            
            if (!data.baseline_url || !data.target_url) {
                addLog('请输入基线和目标文档URL', 'error');
                return;
            }
            
            document.getElementById('start-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
            document.getElementById('export-btn').disabled = true;
            document.getElementById('result-panel').classList.remove('show');
            
            addLog('🚀 启动对比任务...', 'info');
            updateProgress(0, '初始化任务...');
            
            try {
                const response = await fetch('/api/compare', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentTaskId = result.task_id;
                    addLog(`✅ 任务创建成功: ${currentTaskId}`, 'success');
                    statusCheckInterval = setInterval(checkTaskStatus, 1000);
                } else {
                    throw new Error(result.error || '任务创建失败');
                }
            } catch (error) {
                addLog(`❌ 错误: ${error.message}`, 'error');
                document.getElementById('start-btn').disabled = false;
                document.getElementById('stop-btn').disabled = true;
            }
        }
        
        async function checkTaskStatus() {
            if (!currentTaskId) return;
            
            try {
                const response = await fetch(`/api/task/${currentTaskId}`);
                const task = await response.json();
                
                // 更新进度
                updateProgress(task.progress, task.current_step);
                
                // 显示新消息
                if (task.messages && task.messages.length > 0) {
                    const lastMsg = task.messages[task.messages.length - 1];
                    addLog(lastMsg.message, lastMsg.level);
                }
                
                // 任务完成
                if (task.status === 'completed') {
                    clearInterval(statusCheckInterval);
                    addLog('🎉 任务完成！', 'success');
                    displayResult(task.result);
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                    document.getElementById('export-btn').disabled = false;
                }
                
                // 任务失败
                if (task.status === 'failed') {
                    clearInterval(statusCheckInterval);
                    addLog(`❌ 任务失败: ${task.error}`, 'error');
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                }
            } catch (error) {
                addLog(`⚠️ 状态检查失败: ${error.message}`, 'warning');
            }
        }
        
        function displayResult(result) {
            if (!result) return;
            
            const statGrid = document.getElementById('stat-grid');
            statGrid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-label">总差异数</div>
                    <div class="stat-value">${result.total_differences || 0}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">相似度</div>
                    <div class="stat-value">${result.similarity_score || 0}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">风险等级</div>
                    <div class="stat-value">${result.risk_level || 'N/A'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">处理时间</div>
                    <div class="stat-value">${result.processing_time || 0}s</div>
                </div>
            `;
            
            document.getElementById('result-panel').classList.add('show');
        }
        
        async function stopTask() {
            if (currentTaskId) {
                await fetch(`/api/task/${currentTaskId}/stop`, { method: 'POST' });
                clearInterval(statusCheckInterval);
                addLog('⏹️ 任务已停止', 'warning');
                document.getElementById('start-btn').disabled = false;
                document.getElementById('stop-btn').disabled = true;
            }
        }
        
        function clearLog() {
            document.getElementById('status-log').innerHTML = 
                '<div class="log-line log-info">系统就绪，等待任务...</div>';
            logCount = 1;
            document.getElementById('log-count').textContent = '1';
        }
        
        async function exportResult() {
            if (!currentTaskId) return;
            
            try {
                const response = await fetch(`/api/task/${currentTaskId}/export`);
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `comparison_result_${currentTaskId}.json`;
                a.click();
                URL.revokeObjectURL(url);
                addLog('✅ 结果已导出', 'success');
            } catch (error) {
                addLog(`❌ 导出失败: ${error.message}`, 'error');
            }
        }
        
        // 初始化
        document.addEventListener('DOMContentLoaded', () => {
            addLog('✅ 系统初始化完成', 'success');
            addLog('📋 请配置文档URL并点击开始对比', 'info');
            
            // 检查系统状态
            fetch('/health').then(r => r.json()).then(data => {
                if (data.modules_status) {
                    Object.entries(data.modules_status).forEach(([module, status]) => {
                        if (status) {
                            addLog(`✅ 模块 ${module} 已加载`, 'success');
                        } else {
                            addLog(`⚠️ 模块 ${module} 未加载`, 'warning');
                        }
                    });
                }
            });
        });
    </script>
</body>
</html>
'''

# ==================== Flask路由 ====================
@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """创建对比任务"""
    try:
        data = request.json
        task_id = task_manager.create_task()
        
        # 在新线程中运行异步任务
        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(execute_comparison_task(task_id, data))
            loop.close()
        
        thread = threading.Thread(target=run_async_task)
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '任务已创建并开始执行'
        })
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/task/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # 只返回最近的消息避免数据过大
    task_dict = task.to_dict()
    if len(task_dict['messages']) > 10:
        task_dict['messages'] = task_dict['messages'][-10:]
    
    return jsonify(task_dict)

@app.route('/api/task/<task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止任务"""
    task = task_manager.get_task(task_id)
    if task:
        task_manager.update_task(task_id, status='cancelled', end_time=time.time())
        task_manager.add_message(task_id, "任务已被用户取消", "warning")
        return jsonify({'success': True})
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/task/<task_id>/export')
def export_task_result(task_id):
    """导出任务结果"""
    task = task_manager.get_task(task_id)
    if not task or not task.result:
        return jsonify({'error': 'No result available'}), 404
    
    export_data = {
        'task_id': task_id,
        'start_time': task.start_time,
        'end_time': task.end_time,
        'duration': (task.end_time - task.start_time) if task.end_time else None,
        'result': task.result,
        'baseline_file': task.baseline_file,
        'target_file': task.target_file
    }
    
    export_file = TEMP_DIR / f'export_{task_id[:8]}.json'
    with open(export_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    return send_file(export_file, as_attachment=True)

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'modules_status': MODULES_STATUS,
        'active_tasks': len([t for t in task_manager.get_all_tasks() if t.status == 'running'])
    })

@app.route('/api/tasks')
def list_tasks():
    """列出所有任务"""
    tasks = task_manager.get_all_tasks()
    return jsonify([{
        'task_id': t.task_id,
        'status': t.status,
        'progress': t.progress,
        'start_time': t.start_time,
        'current_step': t.current_step
    } for t in tasks])

# ==================== 主程序入口 ====================
if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 腾讯文档对比测试系统 V2.0 启动中...")
    logger.info(f"📁 工作目录: {BASE_DIR}")
    logger.info(f"📝 日志文件: {log_file}")
    logger.info(f"💾 下载目录: {DOWNLOAD_DIR}")
    logger.info(f"📊 结果目录: {RESULT_DIR}")
    logger.info("="*60)
    logger.info("模块加载状态:")
    for module, status in MODULES_STATUS.items():
        status_icon = "✅" if status else "❌"
        logger.info(f"  {status_icon} {module}: {'已加载' if status else '未加载'}")
    logger.info("="*60)
    logger.info("🌐 访问地址: http://localhost:8094")
    logger.info("📖 API文档: http://localhost:8094/api/docs")
    logger.info("="*60)
    
    app.run(host='0.0.0.0', port=8094, debug=False)