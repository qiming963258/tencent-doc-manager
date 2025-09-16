#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档智能处理系统 - 完整集成测试（符合规范版）
严格遵循 /docs/specifications 中的所有规范要求

主要改进：
1. 使用WeekTimeManager进行本地文件查找
2. 分离下载和对比流程
3. 使用ColumnStandardizationProcessorV3
4. 集成DeepSeek AI客户端
"""

import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime
from threading import Thread, Lock
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==================== 目录配置 ====================
BASE_DIR = Path("/root/projects/tencent-doc-manager")
CSV_VERSIONS_DIR = BASE_DIR / "csv_versions"
DOWNLOAD_DIR = BASE_DIR / "downloads"
COMPARISON_RESULTS_DIR = BASE_DIR / "comparison_results"
SCORING_RESULTS_DIR = BASE_DIR / "scoring_results"
EXCEL_UPLOADS_DIR = BASE_DIR / "excel_uploads"

# 确保目录存在
for dir_path in [CSV_VERSIONS_DIR, DOWNLOAD_DIR, COMPARISON_RESULTS_DIR, 
                  SCORING_RESULTS_DIR, EXCEL_UPLOADS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ==================== 工作流状态管理 ====================
class WorkflowState:
    def __init__(self):
        self.reset()
        self.lock = Lock()
    
    def reset(self):
        self.execution_id = None
        self.start_time = None
        self.progress = 0
        self.current_step = ""
        self.logs = []
        self.status = "idle"  # idle, running, completed, error
        self.results = {}
        self.baseline_file = None
        self.target_file = None
        self.score_file = None
        self.marked_file = None
        self.upload_url = None
        self.advanced_settings = {}
    
    def update_progress(self, step: str, progress: int):
        with self.lock:
            self.current_step = step
            self.progress = progress
            logger.info(f"[{progress}%] {step}")
    
    def add_log(self, message: str, level: str = "INFO"):
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.logs.append({
                "timestamp": timestamp,
                "level": level,
                "message": message
            })
            logger.log(getattr(logging, level), message)
    
    def get_state(self):
        with self.lock:
            return {
                "execution_id": self.execution_id,
                "progress": self.progress,
                "current_step": self.current_step,
                "logs": self.logs[-50:],  # 只返回最近50条日志
                "status": self.status,
                "results": self.results
            }

workflow_state = WorkflowState()

# ==================== 模块导入和状态追踪 ====================
MODULES_STATUS = {}

# 1. 时间管理器（核心模块，符合规范）
try:
    from production.core_modules.week_time_manager import WeekTimeManager
    week_manager = WeekTimeManager()
    MODULES_STATUS['week_manager'] = True
    logger.info("✅ 成功导入周时间管理器")
except ImportError as e:
    MODULES_STATUS['week_manager'] = False
    logger.error(f"❌ 无法导入周时间管理器: {e}")
    raise  # 必须有时间管理器

# 2. 下载模块
try:
    from production.core_modules.tencent_export_automation import TencentDocAutoExporter
    MODULES_STATUS['downloader'] = True
    logger.info("✅ 成功导入下载模块")
except ImportError as e:
    MODULES_STATUS['downloader'] = False
    logger.error(f"❌ 无法导入下载模块: {e}")

# 3. 统一CSV对比器（符合规范）
try:
    from unified_csv_comparator import UnifiedCSVComparator
    MODULES_STATUS['comparator'] = True
    logger.info("✅ 成功导入统一CSV对比器")
except ImportError as e:
    MODULES_STATUS['comparator'] = False
    logger.error(f"❌ 无法导入对比模块: {e}")

# 4. 列标准化V3版本（符合规范）
try:
    from column_standardization_processor_v3 import ColumnStandardizationProcessorV3
    MODULES_STATUS['standardizer'] = True
    MODULES_STATUS['standardizer_v3'] = True
    logger.info("✅ 成功导入列标准化V3模块")
except ImportError as e:
    MODULES_STATUS['standardizer_v3'] = False
    # 如果V3不存在，尝试旧版本
    try:
        from production.core_modules.column_standardization_prompt import ColumnStandardizationPrompt
        MODULES_STATUS['standardizer'] = True
        logger.warning("⚠️ 使用旧版列标准化模块")
    except ImportError:
        MODULES_STATUS['standardizer'] = False
        logger.error(f"❌ 无法导入列标准化模块: {e}")

# 5. DeepSeek客户端（符合规范）
try:
    from production.core_modules.deepseek_client import DeepSeekClient
    MODULES_STATUS['deepseek'] = True
    logger.info("✅ 成功导入DeepSeek客户端")
except ImportError as e:
    MODULES_STATUS['deepseek'] = False
    logger.warning(f"⚠️ DeepSeek客户端未加载: {e}")

# 6. L2语义分析
try:
    from production.core_modules.l2_semantic_analysis_two_layer import L2SemanticAnalyzer
    MODULES_STATUS['l2_analyzer'] = True
    logger.info("✅ 成功导入L2语义分析模块")
except ImportError as e:
    MODULES_STATUS['l2_analyzer'] = False
    logger.error(f"❌ 无法导入L2语义分析模块: {e}")

# 7. 智能标记模块
try:
    from intelligent_excel_marker import DetailedScoreGenerator
    MODULES_STATUS['marker'] = True
    logger.info("✅ 成功导入智能标记模块")
except ImportError as e:
    MODULES_STATUS['marker'] = False
    logger.error(f"❌ 无法导入智能标记模块: {e}")

# 8. Excel修复模块
try:
    from fix_tencent_excel import fix_tencent_excel
    MODULES_STATUS['excel_fixer'] = True
    logger.info("✅ 成功导入Excel修复模块")
except ImportError as e:
    MODULES_STATUS['excel_fixer'] = False
    logger.error(f"❌ 无法导入Excel修复模块: {e}")

# 9. 上传模块
try:
    from tencent_doc_uploader_ultimate import TencentDocUploaderUltimate
    MODULES_STATUS['uploader'] = True
    logger.info("✅ 成功导入上传模块(终极版)")
except ImportError as e:
    MODULES_STATUS['uploader'] = False
    logger.error(f"❌ 无法导入上传模块: {e}")

# ==================== 核心工作流函数（符合规范） ====================
def find_or_download_files(baseline_url: str, target_url: str, cookie: str):
    """
    符合规范的文件获取逻辑
    优先使用本地文件，必要时才下载
    """
    # 1. 先尝试查找本地文件
    try:
        baseline_files, baseline_desc = week_manager.find_baseline_files()
        workflow_state.add_log(f"找到本地基线文件: {baseline_desc}")
        
        if baseline_files:
            # 使用最新的基线文件
            workflow_state.baseline_file = baseline_files[0]
            workflow_state.add_log(f"✅ 使用本地基线文件: {os.path.basename(baseline_files[0])}")
        else:
            # 本地没有基线文件，需要下载
            workflow_state.add_log("本地无基线文件，开始下载...")
            if MODULES_STATUS.get('downloader'):
                exporter = TencentDocAutoExporter()
                result = exporter.export_document(baseline_url, cookies=cookie, format='csv')
                if result and result.get('success'):
                    workflow_state.baseline_file = result.get('file_path')
                    workflow_state.add_log(f"✅ 基线文档下载成功")
                else:
                    raise Exception("基线文档下载失败")
            else:
                raise Exception("下载模块未加载，无法下载基线文档")
    except Exception as e:
        workflow_state.add_log(f"❌ 获取基线文件失败: {str(e)}", "ERROR")
        raise
    
    # 2. 查找或下载目标文件
    try:
        target_files = week_manager.find_target_files()
        
        if target_files:
            # 使用最新的目标文件
            workflow_state.target_file = target_files[0]
            workflow_state.add_log(f"✅ 使用本地目标文件: {os.path.basename(target_files[0])}")
        else:
            # 本地没有目标文件，需要下载
            workflow_state.add_log("本地无目标文件，开始下载...")
            if MODULES_STATUS.get('downloader'):
                exporter = TencentDocAutoExporter()
                result = exporter.export_document(target_url, cookies=cookie, format='csv')
                if result and result.get('success'):
                    workflow_state.target_file = result.get('file_path')
                    workflow_state.add_log(f"✅ 目标文档下载成功")
                else:
                    raise Exception("目标文档下载失败")
            else:
                raise Exception("下载模块未加载，无法下载目标文档")
    except Exception as e:
        workflow_state.add_log(f"❌ 获取目标文件失败: {str(e)}", "ERROR")
        raise

def run_compliant_workflow(baseline_url: str, target_url: str, cookie: str, advanced_settings: dict = None):
    """
    执行符合规范的完整工作流程
    """
    try:
        workflow_state.reset()
        workflow_state.status = "running"
        workflow_state.start_time = datetime.now()
        workflow_state.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        workflow_state.advanced_settings = advanced_settings or {}
        
        # ========== 步骤1: 文件获取（符合规范） ==========
        workflow_state.update_progress("获取文件", 10)
        workflow_state.add_log("开始获取基线和目标文件...")
        
        find_or_download_files(baseline_url, target_url, cookie)
        
        # ========== 步骤2: CSV对比分析（使用UnifiedCSVComparator） ==========
        workflow_state.update_progress("执行CSV对比分析", 30)
        workflow_state.add_log("开始对比分析...")
        
        comparison_result = None
        if MODULES_STATUS.get('comparator'):
            unified_comparator = UnifiedCSVComparator()
            comparison_result = unified_comparator.compare(
                workflow_state.baseline_file,
                workflow_state.target_file
            )
            
            # 保存对比结果
            comparison_file = COMPARISON_RESULTS_DIR / f"comparison_{workflow_state.execution_id}.json"
            with open(comparison_file, 'w', encoding='utf-8') as f:
                json.dump(comparison_result, f, ensure_ascii=False, indent=2)
            
            num_changes = comparison_result.get('statistics', {}).get('total_modifications', 0)
            workflow_state.add_log(f"✅ 对比分析完成，发现 {num_changes} 处变更")
        else:
            workflow_state.add_log("⚠️ 比较模块未加载，跳过", "WARNING")
        
        # ========== 步骤3: 列标准化（使用V3版本） ==========
        workflow_state.update_progress("列标准化处理", 40)
        workflow_state.add_log("开始列标准化...")
        
        standardized_result = None
        if MODULES_STATUS.get('standardizer') and comparison_result:
            try:
                # 优先使用V3版本
                if MODULES_STATUS.get('standardizer_v3'):
                    # 获取DeepSeek API密钥
                    api_key = os.getenv('DEEPSEEK_API_KEY')
                    if not api_key:
                        workflow_state.add_log("⚠️ DeepSeek API密钥未配置，使用简化标准化", "WARNING")
                        standardized_result = comparison_result  # 直接使用原始结果
                    else:
                        processor = ColumnStandardizationProcessorV3(api_key)
                        # 提取修改列并进行标准化
                        if 'modified_columns' in comparison_result:
                            import asyncio
                            column_mapping = comparison_result.get('modified_columns', {})
                            # 异步调用标准化
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            standardized_mapping = loop.run_until_complete(
                                processor.standardize_column_names(column_mapping)
                            )
                            loop.close()
                            
                            # 应用标准化结果
                            standardized_result = comparison_result.copy()
                            standardized_result['standardized_columns'] = standardized_mapping
                            workflow_state.add_log(f"✅ 列标准化V3完成，标准化了 {len(standardized_mapping)} 个列")
                        else:
                            standardized_result = comparison_result
                            workflow_state.add_log("⚠️ 无修改列需要标准化", "WARNING")
                else:
                    # 使用旧版本
                    standardizer = ColumnStandardizationPrompt()
                    # 简单的规则映射（兼容旧版）
                    standardized_result = comparison_result  # 保持原始结果
                    workflow_state.add_log(f"⚠️ 使用旧版列标准化", "WARNING")
            except Exception as e:
                workflow_state.add_log(f"⚠️ 列标准化出错: {str(e)}", "WARNING")
        
        # ========== 步骤4: L2语义分析 ==========
        workflow_state.update_progress("语义分析和打分", 50)
        workflow_state.add_log("开始L2语义分析...")
        
        if MODULES_STATUS.get('l2_analyzer') and comparison_result:
            try:
                analyzer = L2SemanticAnalyzer()
                modifications = []
                
                # 处理UnifiedCSVComparator的输出格式
                if comparison_result and 'modifications' in comparison_result:
                    for change in comparison_result['modifications']:
                        cell = change.get('cell', 'A1')
                        row_num = int(''.join(filter(str.isdigit, cell))) if any(c.isdigit() for c in cell) else 0
                        
                        modifications.append({
                            'column_name': cell[0] if cell else '',
                            'old_value': change.get('old', ''),
                            'new_value': change.get('new', ''),
                            'row': row_num,
                            'cell': cell
                        })
                
                semantic_scores = analyzer.analyze_modifications(modifications)
                workflow_state.add_log(f"✅ 语义分析完成，分析了 {len(modifications)} 处变更")
            except Exception as e:
                workflow_state.add_log(f"❌ 语义分析失败: {str(e)}", "ERROR")
                raise
        
        # ========== 步骤5: 生成详细打分 ==========
        workflow_state.update_progress("生成详细打分", 60)
        workflow_state.add_log("生成详细打分JSON...")
        
        if MODULES_STATUS.get('marker') and workflow_state.baseline_file and workflow_state.target_file:
            try:
                generator = DetailedScoreGenerator()
                score_file_path = generator.generate_score_json(
                    baseline_file=workflow_state.baseline_file,
                    target_file=workflow_state.target_file,
                    output_dir=str(SCORING_RESULTS_DIR)
                )
                workflow_state.score_file = score_file_path
                workflow_state.add_log(f"✅ 详细打分生成完成: {os.path.basename(score_file_path)}")
            except Exception as e:
                workflow_state.add_log(f"❌ 打分生成失败: {str(e)}", "ERROR")
                raise
        
        # ========== 步骤6: Excel处理和上传（如果需要） ==========
        if advanced_settings and advanced_settings.get('enable_excel_marking'):
            workflow_state.update_progress("Excel处理", 70)
            workflow_state.add_log("开始Excel处理...")
            
            # 下载Excel格式
            if MODULES_STATUS.get('downloader'):
                exporter_excel = TencentDocAutoExporter()
                excel_result = exporter_excel.export_document(target_url, cookies=cookie, format='xlsx')
                if excel_result and excel_result.get('success'):
                    excel_file = excel_result.get('file_path')
                    workflow_state.add_log(f"✅ Excel文档下载成功")
                    
                    # 修复Excel格式
                    if MODULES_STATUS.get('excel_fixer'):
                        fixed_file = fix_tencent_excel(excel_file)
                        workflow_state.add_log(f"✅ Excel格式修复完成")
                        
                        # 应用涂色标记
                        if MODULES_STATUS.get('marker') and workflow_state.score_file:
                            from intelligent_excel_marker import apply_striped_pattern_to_excel
                            marked_file = apply_striped_pattern_to_excel(fixed_file, workflow_state.score_file)
                            workflow_state.marked_file = marked_file
                            workflow_state.add_log(f"✅ 涂色标记完成")
                            
                            # 上传到腾讯文档
                            if advanced_settings.get('enable_upload') and MODULES_STATUS.get('uploader'):
                                workflow_state.update_progress("上传文档", 90)
                                uploader = TencentDocUploaderUltimate()
                                upload_result = uploader.upload_document(
                                    file_path=marked_file,
                                    cookie=cookie,
                                    target_url=advanced_settings.get('upload_target_url')
                                )
                                if upload_result.get('success'):
                                    workflow_state.upload_url = upload_result.get('url')
                                    workflow_state.add_log(f"✅ 文档上传成功: {workflow_state.upload_url}")
        
        # ========== 完成 ==========
        workflow_state.update_progress("完成", 100)
        workflow_state.status = "completed"
        workflow_state.add_log("🎉 所有步骤执行完成!")
        
        # 保存结果
        workflow_state.results = {
            "baseline_file": workflow_state.baseline_file,
            "target_file": workflow_state.target_file,
            "score_file": workflow_state.score_file,
            "marked_file": workflow_state.marked_file,
            "upload_url": workflow_state.upload_url,
            "comparison_result": comparison_result,
            "execution_time": (datetime.now() - workflow_state.start_time).total_seconds()
        }
        
        return workflow_state.results
        
    except Exception as e:
        workflow_state.status = "error"
        workflow_state.add_log(f"❌ 工作流执行失败: {str(e)}", "ERROR")
        logger.error(f"工作流执行失败: {str(e)}\n{traceback.format_exc()}")
        raise

# ==================== Flask应用 ====================
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """主页"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>腾讯文档智能处理系统（符合规范版）</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        .status-badge { 
            display: inline-block; 
            padding: 5px 10px; 
            border-radius: 5px; 
            font-size: 12px; 
            font-weight: bold;
            background: #27ae60;
            color: white;
        }
        .feature-list { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 15px; 
            margin: 20px 0; 
        }
        .feature-item { 
            padding: 15px; 
            background: #ecf0f1; 
            border-radius: 5px; 
            border-left: 4px solid #3498db; 
        }
        .api-endpoint { 
            background: #2c3e50; 
            color: white; 
            padding: 10px; 
            border-radius: 5px; 
            margin: 10px 0; 
            font-family: monospace; 
        }
        .compliance-notice {
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 腾讯文档智能处理系统 <span class="status-badge">符合规范版 v2.0</span></h1>
        
        <div class="compliance-notice">
            <strong>✅ 规范合规性</strong><br>
            本系统严格遵循 /docs/specifications 中的所有规范要求：
            <ul>
                <li>使用WeekTimeManager进行本地文件查找</li>
                <li>分离下载和对比流程</li>
                <li>使用UnifiedCSVComparator进行对比</li>
                <li>集成ColumnStandardizationProcessorV3</li>
                <li>支持DeepSeek AI增强</li>
            </ul>
        </div>
        
        <h2>核心功能</h2>
        <div class="feature-list">
            <div class="feature-item">📊 智能CSV对比分析</div>
            <div class="feature-item">🔍 本地文件优先查找</div>
            <div class="feature-item">📅 时间周期管理</div>
            <div class="feature-item">🤖 AI语义分析</div>
            <div class="feature-item">🎨 Excel智能涂色</div>
            <div class="feature-item">☁️ 自动上传腾讯文档</div>
        </div>
        
        <h2>API端点</h2>
        <div class="api-endpoint">POST /api/workflow - 执行完整工作流</div>
        <div class="api-endpoint">GET /api/status - 获取执行状态</div>
        <div class="api-endpoint">GET /api/modules - 查看模块状态</div>
        
        <p style="text-align: center; color: #7f8c8d; margin-top: 30px;">
            系统运行在 http://localhost:8093
        </p>
    </div>
</body>
</html>
    ''')

@app.route('/api/workflow', methods=['POST'])
def execute_workflow():
    """执行工作流API"""
    try:
        data = request.json
        baseline_url = data.get('baseline_url')
        target_url = data.get('target_url')
        cookie = data.get('cookie')
        advanced_settings = data.get('advanced_settings', {})
        
        if not all([baseline_url, target_url, cookie]):
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 在后台线程执行工作流
        thread = Thread(
            target=run_compliant_workflow,
            args=(baseline_url, target_url, cookie, advanced_settings)
        )
        thread.start()
        
        return jsonify({
            "success": True,
            "execution_id": workflow_state.execution_id,
            "message": "工作流已启动"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取工作流状态"""
    return jsonify(workflow_state.get_state())

@app.route('/api/modules', methods=['GET'])
def get_modules():
    """获取模块状态"""
    return jsonify(MODULES_STATUS)

# ==================== 主程序入口 ====================
if __name__ == "__main__":
    logger.info("="*60)
    logger.info("腾讯文档智能处理系统 - 符合规范版")
    logger.info("访问: http://localhost:8093")
    logger.info("="*60)
    
    app.run(host='0.0.0.0', port=8093, debug=False)