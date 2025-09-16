#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档监控系统 - 独立后端API服务
提供完整的RESTful API接口供前端调用
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import json
import time
import threading
import traceback
from datetime import datetime
from pathlib import Path
from queue import Queue
import logging

# 导入核心功能模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from production.core_modules.week_time_manager import WeekTimeManager
from production.core_modules.baseline_manager import BaselineManager
from production.core_modules.auto_comparison_task import AutoComparisonTask
from production.core_modules.document_change_analyzer import DocumentChangeAnalyzer
from unified_csv_comparator import UnifiedCSVComparator
from tencent_doc_downloader_new import TencentDocDownloader
from intelligent_excel_marker import IntelligentExcelMarker
from tencent_doc_uploader_ultimate import upload_to_tencent_docs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化Flask应用
app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)

# 全局状态管理
class WorkflowState:
    def __init__(self):
        self.status = "idle"
        self.current_task = None
        self.progress = 0
        self.total_steps = 0
        self.logs = []
        self.results = {}
        self.lock = threading.Lock()
        self.error = None

    def reset(self):
        with self.lock:
            self.status = "idle"
            self.current_task = None
            self.progress = 0
            self.total_steps = 0
            self.logs = []
            self.results = {}
            self.error = None

    def add_log(self, message, level="info"):
        with self.lock:
            log_entry = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "message": message,
                "level": level
            }
            self.logs.append(log_entry)
            logger.info(f"[{log_entry['timestamp']}] {message}")

    def update_progress(self, task, progress, total=None):
        with self.lock:
            self.current_task = task
            self.progress = progress
            if total:
                self.total_steps = total

    def set_status(self, status):
        with self.lock:
            self.status = status

    def get_state(self):
        with self.lock:
            return {
                "status": self.status,
                "current_task": self.current_task,
                "progress": self.progress,
                "total_steps": self.total_steps,
                "logs": self.logs[-100:],  # 只返回最近100条日志
                "error": self.error
            }

# 全局工作流状态
workflow_state = WorkflowState()

# 核心工作流处理函数
def process_workflow(baseline_url, target_url, cookie, advanced_settings=None):
    """执行完整的文档处理工作流"""
    try:
        workflow_state.reset()
        workflow_state.set_status("running")
        workflow_state.add_log("🚀 开始执行文档处理工作流", "info")

        # 初始化管理器
        week_manager = WeekTimeManager()
        baseline_manager = BaselineManager()

        # 确定文件存储路径
        current_week = week_manager.get_current_week()
        weekday = datetime.now().weekday()
        hour = datetime.now().hour

        # 根据时间决定版本类型
        if weekday == 1:  # Tuesday
            version_type = "baseline"
        elif weekday == 5 and hour >= 19:  # Saturday after 7pm
            version_type = "weekend"
        else:
            version_type = "midweek"

        workflow_state.add_log(f"📅 当前周: W{current_week}, 版本类型: {version_type}", "info")

        # 步骤1: 处理基线文档
        workflow_state.update_progress("处理基线文档", 1, 10)

        if baseline_url:
            # 下载新的基线文档
            workflow_state.add_log("📥 下载基线文档...", "info")
            downloader = TencentDocDownloader()

            # 从URL提取文档名
            doc_name = extract_doc_name_from_url(baseline_url)
            baseline_filename = week_manager.generate_filename(
                doc_name,
                version_type="baseline",
                extension="csv"
            )
            baseline_path = os.path.join(
                week_manager.get_version_dir(current_week, "baseline"),
                baseline_filename
            )

            # 确保目录存在
            os.makedirs(os.path.dirname(baseline_path), exist_ok=True)

            # 下载文档
            success = downloader.download_as_csv(
                baseline_url,
                baseline_path,
                cookie
            )

            if not success:
                raise Exception("基线文档下载失败")

            workflow_state.add_log(f"✅ 基线文档已保存: {baseline_filename}", "success")
        else:
            # 使用现有基线
            workflow_state.add_log("📂 使用现有基线文档", "info")
            doc_name = extract_doc_name_from_url(target_url)
            baseline_path = baseline_manager.get_latest_baseline(doc_name)

            if not baseline_path:
                raise Exception(f"未找到文档 {doc_name} 的基线文件")

            workflow_state.add_log(f"✅ 找到基线文档: {os.path.basename(baseline_path)}", "success")

        # 步骤2: 下载目标文档
        workflow_state.update_progress("下载目标文档", 2, 10)
        workflow_state.add_log("📥 下载目标文档...", "info")

        downloader = TencentDocDownloader()
        target_filename = week_manager.generate_filename(
            doc_name,
            version_type=version_type,
            extension="csv"
        )
        target_path = os.path.join(
            week_manager.get_version_dir(current_week, version_type),
            target_filename
        )

        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # 下载文档
        success = downloader.download_as_csv(
            target_url,
            target_path,
            cookie,
            force_download=True  # 总是强制下载最新版本
        )

        if not success:
            raise Exception("目标文档下载失败")

        workflow_state.add_log(f"✅ 目标文档已保存: {target_filename}", "success")

        # 步骤3: CSV对比分析
        workflow_state.update_progress("执行CSV对比分析", 3, 10)
        workflow_state.add_log("🔍 开始CSV对比分析...", "info")

        comparator = UnifiedCSVComparator()
        comparison_result = comparator.compare(baseline_path, target_path)

        total_modifications = comparison_result['statistics']['total_modifications']
        similarity = comparison_result['statistics']['similarity']

        workflow_state.add_log(
            f"📊 对比完成: 修改数={total_modifications}, 相似度={similarity:.1%}",
            "success"
        )

        # 步骤4: 生成变更分析报告
        workflow_state.update_progress("生成变更分析报告", 4, 10)
        workflow_state.add_log("📝 生成变更分析报告...", "info")

        analyzer = DocumentChangeAnalyzer()
        analysis_result = analyzer.analyze_changes(comparison_result)

        workflow_state.add_log(f"✅ 变更分析完成", "success")

        # 步骤5: 创建Excel标记文件
        workflow_state.update_progress("创建Excel标记文件", 5, 10)
        workflow_state.add_log("📑 创建Excel标记文件...", "info")

        marker = IntelligentExcelMarker()
        excel_filename = target_filename.replace('.csv', '_marked.xlsx')
        excel_path = os.path.join(
            week_manager.get_version_dir(current_week, version_type),
            excel_filename
        )

        marker.create_marked_excel(
            target_path,
            comparison_result,
            analysis_result,
            excel_path
        )

        workflow_state.add_log(f"✅ Excel文件已创建: {excel_filename}", "success")

        # 步骤6: 上传到腾讯文档（可选）
        if advanced_settings and advanced_settings.get('auto_upload'):
            workflow_state.update_progress("上传到腾讯文档", 6, 10)
            workflow_state.add_log("☁️ 上传到腾讯文档...", "info")

            upload_result = upload_to_tencent_docs(excel_path, cookie)

            if upload_result['success']:
                workflow_state.add_log(
                    f"✅ 已上传到腾讯文档: {upload_result.get('url', 'N/A')}",
                    "success"
                )
            else:
                workflow_state.add_log(
                    f"⚠️ 上传失败: {upload_result.get('error', '未知错误')}",
                    "warning"
                )

        # 完成
        workflow_state.update_progress("完成", 10, 10)
        workflow_state.set_status("completed")
        workflow_state.add_log("🎉 工作流执行完成!", "success")

        # 保存结果
        workflow_state.results = {
            "baseline_path": baseline_path,
            "target_path": target_path,
            "excel_path": excel_path,
            "comparison": comparison_result,
            "analysis": analysis_result
        }

    except Exception as e:
        logger.error(f"工作流执行失败: {str(e)}")
        logger.error(traceback.format_exc())
        workflow_state.error = str(e)
        workflow_state.set_status("error")
        workflow_state.add_log(f"❌ 错误: {str(e)}", "error")

def extract_doc_name_from_url(url):
    """从URL提取文档名称"""
    # 简单实现，实际应该从URL查询文档信息
    if "出国销售" in url:
        return "出国销售计划表"
    elif "回国销售" in url:
        return "回国销售计划表"
    elif "小红书" in url:
        return "小红书部门"
    else:
        # 从URL提取ID作为名称
        parts = url.split("/")
        return parts[-1] if parts else "unknown"

# API路由
@app.route('/api/status', methods=['GET'])
def get_status():
    """获取服务状态"""
    return jsonify({
        "status": "running",
        "version": "2.0",
        "service": "backend-api",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/workflow/start', methods=['POST'])
def start_workflow():
    """启动工作流"""
    try:
        data = request.get_json()

        # 验证必要参数
        if not data.get('target_url'):
            return jsonify({"error": "缺少target_url参数"}), 400

        if not data.get('cookie'):
            return jsonify({"error": "缺少cookie参数"}), 400

        # 检查是否有正在运行的工作流
        if workflow_state.status == "running":
            return jsonify({"error": "已有工作流正在运行"}), 409

        # 在后台线程中启动工作流
        thread = threading.Thread(
            target=process_workflow,
            args=(
                data.get('baseline_url'),
                data.get('target_url'),
                data.get('cookie'),
                data.get('advanced_settings', {})
            )
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            "success": True,
            "message": "工作流已启动"
        })

    except Exception as e:
        logger.error(f"启动工作流失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/workflow/status', methods=['GET'])
def get_workflow_status():
    """获取工作流状态"""
    return jsonify(workflow_state.get_state())

@app.route('/api/workflow/logs', methods=['GET'])
def get_workflow_logs():
    """获取工作流日志"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify({
        "logs": workflow_state.logs[-limit:],
        "total": len(workflow_state.logs)
    })

@app.route('/api/workflow/stop', methods=['POST'])
def stop_workflow():
    """停止工作流"""
    workflow_state.set_status("stopped")
    workflow_state.add_log("⛔ 工作流已停止", "warning")
    return jsonify({"success": True})

@app.route('/api/baseline/list', methods=['GET'])
def list_baselines():
    """列出所有基线文件"""
    try:
        manager = BaselineManager()
        baselines = manager.list_all_baselines()
        return jsonify({"baselines": baselines})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/baseline/upload', methods=['POST'])
def upload_baseline():
    """上传基线文件"""
    try:
        data = request.get_json()
        url = data.get('url')
        cookie = data.get('cookie')

        if not url or not cookie:
            return jsonify({"error": "缺少必要参数"}), 400

        # 下载并保存为基线
        downloader = TencentDocDownloader()
        week_manager = WeekTimeManager()

        doc_name = extract_doc_name_from_url(url)
        filename = week_manager.generate_filename(
            doc_name,
            version_type="baseline",
            extension="csv"
        )

        current_week = week_manager.get_current_week()
        filepath = os.path.join(
            week_manager.get_version_dir(current_week, "baseline"),
            filename
        )

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        success = downloader.download_as_csv(url, filepath, cookie)

        if success:
            return jsonify({
                "success": True,
                "filename": filename,
                "path": filepath
            })
        else:
            return jsonify({"error": "下载失败"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/files/csv/<week>/<version>', methods=['GET'])
def list_csv_files(week, version):
    """列出指定周和版本的CSV文件"""
    try:
        week_manager = WeekTimeManager()
        directory = week_manager.get_version_dir(week, version)

        if not os.path.exists(directory):
            return jsonify({"files": []})

        files = []
        for f in os.listdir(directory):
            if f.endswith('.csv'):
                filepath = os.path.join(directory, f)
                stat = os.stat(filepath)
                files.append({
                    "name": f,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        return jsonify({"files": files})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comparison/execute', methods=['POST'])
def execute_comparison():
    """执行CSV对比"""
    try:
        data = request.get_json()
        baseline_path = data.get('baseline_path')
        target_path = data.get('target_path')

        if not baseline_path or not target_path:
            return jsonify({"error": "缺少文件路径"}), 400

        comparator = UnifiedCSVComparator()
        result = comparator.compare(baseline_path, target_path)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "uptime": time.time(),
        "memory_usage": get_memory_usage()
    })

def get_memory_usage():
    """获取内存使用情况"""
    try:
        import psutil
        process = psutil.Process()
        return {
            "rss": process.memory_info().rss,
            "percent": process.memory_percent()
        }
    except:
        return {}

if __name__ == '__main__':
    print(f"🚀 腾讯文档监控系统后端API服务")
    print(f"📍 服务地址: http://0.0.0.0:8093")
    print(f"📊 API文档: http://0.0.0.0:8093/api/status")
    print(f"=" * 50)

    app.run(
        host='0.0.0.0',
        port=8093,
        debug=False,
        threaded=True
    )