#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档管理系统 - 增强版Flask API服务器
集成所有核心组件：自适应表格对比、AI语义分析、Excel MCP可视化、腾讯文档上传
版本: 2.0.0
作者: Claude Code System Integration Team
创建时间: 2025-08-12

Excel MCP 使用说明:
请在使用Excel MCP相关功能前，务必阅读 docs/Excel-MCP-AI-使用指南.md
确保正确使用 mcp__excel-optimized__* 系列函数，避免内存溢出和格式错误。
"""

from flask import Flask, request, jsonify, send_file, render_template, stream_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import sqlite3
from pathlib import Path
import secrets
import logging
import threading
import time
from functools import wraps
from typing import Dict, List, Any, Optional
import traceback

# 导入现有的自动化工具
try:
    from tencent_export_automation import TencentDocAutoExporter
    from tencent_upload_automation import TencentDocUploader
    from concurrent_processor import get_processor, TaskType
except ImportError:
    print("⚠️ 部分腾讯文档自动化工具未找到，将跳过相关功能")

# 导入集成的新组件
from document_change_analyzer import DocumentChangeAnalyzer
from adaptive_table_comparator import AdaptiveTableComparator, IntelligentColumnMatcher
# 使用新的Claude封装程序集成
from claude_wrapper_integration import AISemanticAnalysisOrchestrator
from excel_mcp_visualizer import ExcelMCPVisualizationClient, VisualizationConfig

# 兼容性导入
try:
    from claude_semantic_analysis import ModificationAnalysisRequest
except ImportError:
    # 如果原模块不存在，创建基本数据结构
    from dataclasses import dataclass
    from typing import Optional
    
    @dataclass
    class ModificationAnalysisRequest:
        modification_id: str
        column_name: str
        original_value: str
        new_value: str
        table_name: str
        row_index: int
        change_context: Optional[str] = None
        modification_time: Optional[str] = None
        modifier: Optional[str] = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tencent_doc_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 配置
app.config.update({
    'SECRET_KEY': secrets.token_hex(32),
    'UPLOAD_FOLDER': 'uploads',
    'DOWNLOAD_FOLDER': 'downloads',
    'ANALYSIS_FOLDER': 'analysis_results',
    'VISUALIZATION_FOLDER': 'visualizations',
    'MAX_CONTENT_LENGTH': 500 * 1024 * 1024,  # 500MB限制
    'DATABASE': 'tencent_docs_enhanced.db',
    'REDIS_URL': 'redis://localhost:6379/0',
    'CLAUDE_API_KEY': os.getenv('CLAUDE_API_KEY', ''),
    'CLAUDE_WRAPPER_URL': os.getenv('CLAUDE_WRAPPER_URL', 'http://localhost:8081'),  # 新增
    'PROCESSING_TIMEOUT': 300,  # 5分钟处理超时
    'MAX_CONCURRENT_JOBS': 3,
    'BATCH_SIZE': 30
})

# 确保所有目录存在
for folder in ['UPLOAD_FOLDER', 'DOWNLOAD_FOLDER', 'ANALYSIS_FOLDER', 'VISUALIZATION_FOLDER']:
    os.makedirs(app.config[folder], exist_ok=True)

os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# ===================== 核心组件初始化 =====================

class EnhancedDocumentManager:
    """增强版文档管理器 - 统一管理所有组件"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化核心组件
        self.document_analyzer = DocumentChangeAnalyzer()
        self.adaptive_comparator = AdaptiveTableComparator()
        self.column_matcher = IntelligentColumnMatcher()
        
        # 初始化AI语义分析器（使用Claude封装程序）
        self.ai_analyzer = None
        claude_wrapper_url = config.get('CLAUDE_WRAPPER_URL', 'http://localhost:8081')
        try:
            self.ai_analyzer = AISemanticAnalysisOrchestrator(claude_wrapper_url)
            self.logger.info("✅ AI语义分析器初始化成功 (使用Claude封装程序)")
        except Exception as e:
            self.logger.warning(f"⚠️ AI语义分析器初始化失败: {e}")
            # 保持兼容性，如果有直接API密钥也可以用
            if config.get('CLAUDE_API_KEY'):
                try:
                    from claude_semantic_analysis import AISemanticAnalysisOrchestrator as DirectAI
                    self.ai_analyzer = DirectAI(config['CLAUDE_API_KEY'])
                    self.logger.info("✅ 使用直接API作为备选方案")
                except Exception:
                    pass
        
        # 初始化Excel可视化器
        self.visualization_config = VisualizationConfig(
            enable_diagonal_pattern=True,
            enable_detailed_comments=True,
            enable_risk_charts=True,
            enable_interactive_dashboard=True,
            color_scheme="professional"
        )
        self.excel_visualizer = ExcelMCPVisualizationClient(self.visualization_config)
        
        # 处理统计
        self.processing_stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "ai_analyses_performed": 0,
            "visualizations_created": 0,
            "start_time": datetime.now()
        }
    
    async def comprehensive_document_analysis(self, file_paths: List[str], 
                                            reference_file: str = None,
                                            enable_ai_analysis: bool = True,
                                            enable_visualization: bool = True,
                                            job_id: str = None) -> Dict[str, Any]:
        """
        全面的文档分析流程
        
        Args:
            file_paths: 要分析的文件路径列表
            reference_file: 参考文件路径（可选）
            enable_ai_analysis: 是否启用AI分析
            enable_visualization: 是否启用可视化
            job_id: 作业ID（用于进度跟踪）
            
        Returns:
            完整的分析结果
        """
        
        analysis_start_time = time.time()
        self.processing_stats["total_analyses"] += 1
        
        try:
            self.logger.info(f"🚀 开始全面文档分析，文件数量: {len(file_paths)}")
            
            analysis_result = {
                "job_id": job_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "file_paths": file_paths,
                "reference_file": reference_file,
                "processing_summary": {},
                "adaptive_comparison_results": [],
                "ai_analysis_results": {},
                "visualization_results": {},
                "risk_summary": {},
                "recommendations": [],
                "processing_stats": {}
            }
            
            # 第1阶段：自适应表格对比分析
            self.logger.info("📊 第1阶段：执行自适应表格对比分析...")
            
            # 构建表格数据结构
            current_tables = []
            for i, file_path in enumerate(file_paths):
                try:
                    # 根据文件类型选择解析方法
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path, encoding='utf-8-sig')
                    elif file_path.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(file_path)
                    else:
                        self.logger.warning(f"⚠️ 不支持的文件格式: {file_path}")
                        continue
                    
                    table_data = {
                        "name": os.path.basename(file_path),
                        "data": [df.columns.tolist()] + df.values.tolist()
                    }
                    current_tables.append(table_data)
                    
                except Exception as e:
                    self.logger.error(f"❌ 文件解析失败 {file_path}: {e}")
                    continue
            
            if not current_tables:
                raise ValueError("没有成功解析的文件")
            
            # 执行自适应对比
            reference_tables = None
            if reference_file:
                try:
                    if reference_file.endswith('.csv'):
                        ref_df = pd.read_csv(reference_file, encoding='utf-8-sig')
                    elif reference_file.endswith(('.xlsx', '.xls')):
                        ref_df = pd.read_excel(reference_file)
                    
                    reference_tables = [{
                        "name": os.path.basename(reference_file),
                        "data": [ref_df.columns.tolist()] + ref_df.values.tolist()
                    }]
                except Exception as e:
                    self.logger.warning(f"⚠️ 参考文件解析失败: {e}")
            
            adaptive_result = self.adaptive_comparator.adaptive_compare_tables(
                current_tables, reference_tables
            )
            analysis_result["adaptive_comparison_results"] = adaptive_result
            
            # 第2阶段：AI语义分析（如果启用且检测到L2级别变更）
            if enable_ai_analysis and self.ai_analyzer:
                self.logger.info("🤖 第2阶段：执行AI语义分析...")
                
                # 提取需要AI分析的L2级别修改
                l2_modifications = []
                for comparison in adaptive_result.get("comparison_results", []):
                    change_result = comparison.get("change_detection_result")
                    if change_result and "changes" in change_result:
                        for change in change_result["changes"]:
                            if change.get("risk_level") == "L2":
                                mod_request = ModificationAnalysisRequest(
                                    modification_id=f"{comparison.get('table_id', 'unknown')}_{change.get('row_index', 0)}_{change.get('column_name', '')}",
                                    column_name=change.get("column_name", ""),
                                    original_value=str(change.get("original_value", "")),
                                    new_value=str(change.get("new_value", "")),
                                    table_name=comparison.get("table_name", ""),
                                    row_index=change.get("row_index", 0),
                                    change_context="自动检测的表格修改",
                                    modification_time=datetime.now().isoformat(),
                                    modifier="system"
                                )
                                l2_modifications.append(mod_request)
                
                if l2_modifications:
                    ai_results = await self.ai_analyzer.analyze_modifications_with_caching(
                        l2_modifications, use_cache=True
                    )
                    
                    # 生成AI分析摘要
                    ai_summary = self.ai_analyzer.generate_analysis_summary(ai_results)
                    analysis_result["ai_analysis_results"] = {
                        "individual_analyses": {r.modification_id: {
                            "recommendation": r.recommendation,
                            "confidence": r.confidence,
                            "reasoning": r.reasoning,
                            "business_impact": r.business_impact,
                            "suggested_action": r.suggested_action,
                            "risk_factors": r.risk_factors
                        } for r in ai_results},
                        "summary": ai_summary
                    }
                    
                    self.processing_stats["ai_analyses_performed"] += len(ai_results)
                    self.logger.info(f"✅ AI分析完成，处理了{len(ai_results)}个L2级别修改")
                else:
                    analysis_result["ai_analysis_results"] = {"message": "未检测到需要AI分析的L2级别修改"}
            
            # 第3阶段：Excel MCP可视化（如果启用）
            if enable_visualization:
                self.logger.info("🎨 第3阶段：生成Excel可视化报告...")
                
                try:
                    # 构建可视化数据
                    visualization_data = {
                        "comparison_results": adaptive_result.get("comparison_results", []),
                        "ai_analysis_results": analysis_result.get("ai_analysis_results", {}).get("individual_analyses", {}),
                        "table_metadata": {"generated_by": "Enhanced Document Manager"}
                    }
                    
                    # 生成Excel可视化报告
                    output_path = os.path.join(
                        app.config['VISUALIZATION_FOLDER'], 
                        f"analysis_report_{job_id or 'manual'}_{int(time.time())}.xlsx"
                    )
                    
                    visualization_result = await self.excel_visualizer.create_comprehensive_risk_report(
                        visualization_data, output_path
                    )
                    
                    analysis_result["visualization_results"] = visualization_result
                    self.processing_stats["visualizations_created"] += 1
                    self.logger.info(f"✅ 可视化报告生成完成: {output_path}")
                    
                except Exception as e:
                    self.logger.error(f"❌ 可视化生成失败: {e}")
                    analysis_result["visualization_results"] = {"error": str(e)}
            
            # 第4阶段：风险汇总和建议
            self.logger.info("📋 第4阶段：生成风险汇总和建议...")
            analysis_result["risk_summary"] = self._generate_comprehensive_risk_summary(analysis_result)
            analysis_result["recommendations"] = self._generate_actionable_recommendations(analysis_result)
            
            # 处理统计
            processing_time = time.time() - analysis_start_time
            analysis_result["processing_stats"] = {
                "total_processing_time": processing_time,
                "files_processed": len(current_tables),
                "phases_completed": 4,
                "ai_analysis_enabled": enable_ai_analysis and bool(self.ai_analyzer),
                "visualization_enabled": enable_visualization,
                "success": True
            }
            
            self.processing_stats["successful_analyses"] += 1
            self.logger.info(f"🎉 全面文档分析完成！耗时: {processing_time:.2f}秒")
            
            return analysis_result
            
        except Exception as e:
            self.processing_stats["failed_analyses"] += 1
            self.logger.error(f"❌ 全面文档分析失败: {e}")
            self.logger.error(traceback.format_exc())
            
            return {
                "job_id": job_id,
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat(),
                "processing_stats": {
                    "success": False,
                    "error_message": str(e),
                    "processing_time": time.time() - analysis_start_time
                }
            }
    
    def _generate_comprehensive_risk_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合风险汇总"""
        
        risk_summary = {
            "overall_risk_level": "LOW",
            "critical_issues_count": 0,
            "high_risk_issues_count": 0,
            "medium_risk_issues_count": 0,
            "l1_violations": 0,
            "l2_modifications": 0,
            "l3_modifications": 0,
            "ai_high_confidence_rejections": 0,
            "data_quality_concerns": [],
            "processing_warnings": []
        }
        
        # 分析自适应对比结果
        for comparison in analysis_result.get("adaptive_comparison_results", {}).get("comparison_results", []):
            change_result = comparison.get("change_detection_result")
            if change_result:
                risk_dist = change_result.get("risk_distribution", {})
                risk_summary["l1_violations"] += risk_dist.get("L1", 0)
                risk_summary["l2_modifications"] += risk_dist.get("L2", 0)
                risk_summary["l3_modifications"] += risk_dist.get("L3", 0)
            
            # 检查数据质量
            std_result = comparison.get("standardization_result", {})
            quality_score = std_result.get("data_quality_score", 1.0)
            if quality_score < 0.7:
                risk_summary["data_quality_concerns"].append({
                    "table_name": comparison.get("table_name", "unknown"),
                    "quality_score": quality_score,
                    "issues": std_result.get("issues", [])[:3]  # 前3个问题
                })
        
        # 分析AI结果
        ai_results = analysis_result.get("ai_analysis_results", {})
        if "individual_analyses" in ai_results:
            for mod_id, ai_result in ai_results["individual_analyses"].items():
                if ai_result["recommendation"] == "REJECT" and ai_result["confidence"] > 0.8:
                    risk_summary["ai_high_confidence_rejections"] += 1
        
        # 确定整体风险等级
        if risk_summary["l1_violations"] > 0:
            risk_summary["overall_risk_level"] = "CRITICAL"
            risk_summary["critical_issues_count"] = risk_summary["l1_violations"]
        elif risk_summary["ai_high_confidence_rejections"] > 0 or risk_summary["l2_modifications"] > 5:
            risk_summary["overall_risk_level"] = "HIGH"
            risk_summary["high_risk_issues_count"] = risk_summary["ai_high_confidence_rejections"] + min(risk_summary["l2_modifications"], 5)
        elif risk_summary["l2_modifications"] > 0 or len(risk_summary["data_quality_concerns"]) > 0:
            risk_summary["overall_risk_level"] = "MEDIUM"
            risk_summary["medium_risk_issues_count"] = risk_summary["l2_modifications"] + len(risk_summary["data_quality_concerns"])
        
        return risk_summary
    
    def _generate_actionable_recommendations(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成可操作的建议"""
        
        recommendations = []
        risk_summary = analysis_result.get("risk_summary", {})
        
        # L1违规建议
        if risk_summary.get("l1_violations", 0) > 0:
            recommendations.append({
                "priority": "critical",
                "category": "compliance",
                "title": "严重违规需要立即处理",
                "description": f"检测到{risk_summary['l1_violations']}个L1级别违规修改，这些字段绝对不能修改",
                "action_items": [
                    "立即回滚所有L1级别的修改",
                    "联系相关负责人确认修改意图",
                    "检查权限设置防止未授权修改"
                ],
                "estimated_effort": "高优先级，立即处理"
            })
        
        # AI高置信度拒绝建议
        if risk_summary.get("ai_high_confidence_rejections", 0) > 0:
            recommendations.append({
                "priority": "high",
                "category": "ai_review", 
                "title": "AI强烈建议拒绝的修改",
                "description": f"AI系统高置信度建议拒绝{risk_summary['ai_high_confidence_rejections']}个修改",
                "action_items": [
                    "人工复查AI标记的高风险修改",
                    "分析修改的业务合理性",
                    "考虑回滚不合理的修改"
                ],
                "estimated_effort": "24小时内完成审核"
            })
        
        # 数据质量建议
        if risk_summary.get("data_quality_concerns"):
            recommendations.append({
                "priority": "medium",
                "category": "data_quality",
                "title": "数据质量需要改进",
                "description": f"发现{len(risk_summary['data_quality_concerns'])}个表格存在数据质量问题",
                "action_items": [
                    "检查原始数据来源的准确性",
                    "标准化数据格式和命名规范",
                    "建立数据质量监控机制"
                ],
                "estimated_effort": "1-2个工作日"
            })
        
        # L2修改建议
        if risk_summary.get("l2_modifications", 0) > 0:
            recommendations.append({
                "priority": "medium",
                "category": "review",
                "title": "需要语义审核的修改",
                "description": f"{risk_summary['l2_modifications']}个L2级别修改需要人工确认",
                "action_items": [
                    "安排业务专家审核L2级别修改",
                    "确认修改符合业务规则",
                    "建立定期审核流程"
                ],
                "estimated_effort": "3-5个工作日"
            })
        
        # 系统优化建议
        adaptive_results = analysis_result.get("adaptive_comparison_results", {})
        avg_confidence = adaptive_results.get("processing_stats", {}).get("average_match_confidence", 1.0)
        if avg_confidence < 0.8:
            recommendations.append({
                "priority": "low",
                "category": "system_optimization",
                "title": "提升列匹配准确率",
                "description": f"平均列匹配置信度为{avg_confidence:.1%}，建议优化",
                "action_items": [
                    "标准化表格列名命名规范",
                    "创建列名映射词典",
                    "训练智能匹配算法"
                ],
                "estimated_effort": "长期优化项目"
            })
        
        return recommendations


# 全局文档管理器实例
doc_manager = EnhancedDocumentManager(app.config)

# ===================== 数据库初始化 =====================

def init_enhanced_db():
    """初始化增强版数据库"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  cookie_hash TEXT NOT NULL,
                  encrypted_cookies TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_used TIMESTAMP,
                  preferences TEXT)''')
    
    # 文档表
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  doc_url TEXT,
                  doc_name TEXT,
                  file_path TEXT,
                  operation TEXT,
                  status TEXT DEFAULT 'processing',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  metadata TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # 分析作业表
    c.execute('''CREATE TABLE IF NOT EXISTS analysis_jobs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_id TEXT UNIQUE NOT NULL,
                  user_id INTEGER,
                  job_name TEXT,
                  job_type TEXT,
                  status TEXT DEFAULT 'created',
                  progress REAL DEFAULT 0.0,
                  result_path TEXT,
                  error_message TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  started_at TIMESTAMP,
                  completed_at TIMESTAMP,
                  config TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # 文件处理记录表
    c.execute('''CREATE TABLE IF NOT EXISTS file_processing
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_id TEXT,
                  file_path TEXT,
                  file_name TEXT,
                  processing_status TEXT DEFAULT 'pending',
                  analysis_result TEXT,
                  error_message TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  processed_at TIMESTAMP,
                  FOREIGN KEY (job_id) REFERENCES analysis_jobs(job_id))''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_enhanced_db()

# ===================== 工具函数 =====================

def require_auth(f):
    """简单的认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = request.json.get('username') if request.is_json else request.form.get('username')
        if not username:
            return jsonify({'error': '需要用户名进行认证'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """根据用户名获取用户信息"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    c.execute("SELECT id, username, created_at, last_used FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'created_at': user[2],
            'last_used': user[3]
        }
    return None

def create_analysis_job(user_id: int, job_name: str, job_type: str, config: Dict[str, Any]) -> str:
    """创建分析作业记录"""
    job_id = f"{job_type}_{int(time.time())}_{secrets.token_hex(8)}"
    
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    c.execute("""INSERT INTO analysis_jobs 
                 (job_id, user_id, job_name, job_type, config) 
                 VALUES (?, ?, ?, ?, ?)""",
              (job_id, user_id, job_name, job_type, json.dumps(config)))
    conn.commit()
    conn.close()
    
    return job_id

def update_job_status(job_id: str, status: str, progress: float = None, 
                     result_path: str = None, error_message: str = None):
    """更新作业状态"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    
    update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
    values = [status]
    
    if progress is not None:
        update_fields.append("progress = ?")
        values.append(progress)
    
    if result_path:
        update_fields.append("result_path = ?")
        values.append(result_path)
    
    if error_message:
        update_fields.append("error_message = ?")
        values.append(error_message)
    
    if status == 'running' and progress == 0.0:
        update_fields.append("started_at = CURRENT_TIMESTAMP")
    elif status == 'completed':
        update_fields.append("completed_at = CURRENT_TIMESTAMP")
    
    values.append(job_id)
    
    c.execute(f"UPDATE analysis_jobs SET {', '.join(update_fields)} WHERE job_id = ?", values)
    conn.commit()
    conn.close()

# ===================== API路由 =====================

@app.route('/')
def index():
    """主页"""
    return jsonify({
        'service': '腾讯文档管理系统 - 增强版API',
        'version': '2.0.0',
        'status': 'running',
        'features': [
            '自适应表格对比分析',
            'AI语义分析集成',
            'Excel MCP可视化',
            '批量文档处理',
            '腾讯文档自动化',
            '风险评估和建议'
        ],
        'endpoints': {
            'health': '/api/health',
            'analysis': '/api/v2/analysis',
            'batch_analysis': '/api/v2/batch/analysis',
            'jobs': '/api/v2/jobs',
            'upload': '/api/v2/upload',
            'download': '/api/v2/download'
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """增强版健康检查"""
    
    # 检查核心组件状态
    component_status = {
        'document_analyzer': True,
        'adaptive_comparator': True,
        'column_matcher': True,
        'ai_analyzer': bool(doc_manager.ai_analyzer),
        'excel_visualizer': True,
        'database': True
    }
    
    # 检查数据库连接
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        component_status['database'] = False
    
    # 系统统计
    system_stats = doc_manager.processing_stats.copy()
    system_stats['uptime_seconds'] = (datetime.now() - system_stats['start_time']).total_seconds()
    
    overall_health = all(component_status.values())
    
    return jsonify({
        'status': 'healthy' if overall_health else 'degraded',
        'service': '腾讯文档管理系统 - 增强版',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'component_status': component_status,
        'system_stats': {
            'total_analyses': system_stats['total_analyses'],
            'successful_analyses': system_stats['successful_analyses'],
            'success_rate': system_stats['successful_analyses'] / max(1, system_stats['total_analyses']),
            'ai_analyses_performed': system_stats['ai_analyses_performed'],
            'visualizations_created': system_stats['visualizations_created'],
            'uptime_hours': round(system_stats['uptime_seconds'] / 3600, 2)
        }
    }), 200 if overall_health else 503

@app.route('/api/v2/analysis/single', methods=['POST'])
@require_auth
def single_file_analysis():
    """单文件分析API"""
    try:
        # 检查是否有上传文件
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        username = request.form.get('username')
        enable_ai = request.form.get('enable_ai', 'true').lower() == 'true'
        enable_viz = request.form.get('enable_visualization', 'true').lower() == 'true'
        
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{username}_{int(time.time())}_{filename}")
        file.save(file_path)
        
        # 获取用户信息
        user = get_user_by_username(username)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 创建分析作业
        config = {
            'enable_ai_analysis': enable_ai,
            'enable_visualization': enable_viz,
            'file_paths': [file_path]
        }
        job_id = create_analysis_job(user['id'], f"单文件分析-{filename}", "single_analysis", config)
        
        # 异步执行分析
        async def run_analysis():
            try:
                update_job_status(job_id, 'running', 0.0)
                
                result = await doc_manager.comprehensive_document_analysis(
                    file_paths=[file_path],
                    reference_file=None,
                    enable_ai_analysis=enable_ai,
                    enable_visualization=enable_viz,
                    job_id=job_id
                )
                
                # 保存结果
                result_path = os.path.join(app.config['ANALYSIS_FOLDER'], f"result_{job_id}.json")
                with open(result_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                
                if result.get('processing_stats', {}).get('success', False):
                    update_job_status(job_id, 'completed', 100.0, result_path)
                else:
                    update_job_status(job_id, 'failed', 100.0, error_message=result.get('error', '分析失败'))
                
            except Exception as e:
                logger.error(f"单文件分析失败 {job_id}: {e}")
                update_job_status(job_id, 'failed', error_message=str(e))
        
        # 在后台运行分析
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_analysis())
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '单文件分析作业已创建',
            'job_id': job_id,
            'file_name': filename,
            'config': config
        })
        
    except Exception as e:
        logger.error(f"单文件分析API错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/analysis/batch', methods=['POST'])
@require_auth 
def batch_analysis():
    """批量分析API"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        files = request.files.getlist('files')
        username = request.form.get('username')
        reference_file = request.files.get('reference_file')
        enable_ai = request.form.get('enable_ai', 'true').lower() == 'true'
        enable_viz = request.form.get('enable_visualization', 'true').lower() == 'true'
        job_name = request.form.get('job_name', f'批量分析-{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        
        if not files or not username:
            return jsonify({'error': '文件列表和用户名不能为空'}), 400
        
        if len(files) > app.config['BATCH_SIZE']:
            return jsonify({'error': f'批处理数量不能超过{app.config["BATCH_SIZE"]}个'}), 400
        
        # 获取用户信息
        user = get_user_by_username(username)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 保存上传的文件
        file_paths = []
        for file in files:
            if file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{username}_{int(time.time())}_{filename}")
                file.save(file_path)
                file_paths.append(file_path)
        
        # 保存参考文件（如果有）
        reference_file_path = None
        if reference_file and reference_file.filename != '':
            ref_filename = secure_filename(reference_file.filename)
            reference_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{username}_ref_{int(time.time())}_{ref_filename}")
            reference_file.save(reference_file_path)
        
        if not file_paths:
            return jsonify({'error': '没有有效文件'}), 400
        
        # 创建分析作业
        config = {
            'enable_ai_analysis': enable_ai,
            'enable_visualization': enable_viz,
            'file_paths': file_paths,
            'reference_file': reference_file_path,
            'batch_size': len(file_paths)
        }
        job_id = create_analysis_job(user['id'], job_name, "batch_analysis", config)
        
        # 异步执行批量分析
        async def run_batch_analysis():
            try:
                update_job_status(job_id, 'running', 0.0)
                
                result = await doc_manager.comprehensive_document_analysis(
                    file_paths=file_paths,
                    reference_file=reference_file_path,
                    enable_ai_analysis=enable_ai,
                    enable_visualization=enable_viz,
                    job_id=job_id
                )
                
                # 保存结果
                result_path = os.path.join(app.config['ANALYSIS_FOLDER'], f"batch_result_{job_id}.json")
                with open(result_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                
                if result.get('processing_stats', {}).get('success', False):
                    update_job_status(job_id, 'completed', 100.0, result_path)
                else:
                    update_job_status(job_id, 'failed', 100.0, error_message=result.get('error', '批量分析失败'))
                
            except Exception as e:
                logger.error(f"批量分析失败 {job_id}: {e}")
                update_job_status(job_id, 'failed', error_message=str(e))
        
        # 在后台运行分析
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_batch_analysis())
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'批量分析作业已创建，共{len(file_paths)}个文件',
            'job_id': job_id,
            'job_name': job_name,
            'total_files': len(file_paths),
            'config': {
                'ai_analysis_enabled': enable_ai,
                'visualization_enabled': enable_viz,
                'has_reference_file': bool(reference_file_path)
            }
        })
        
    except Exception as e:
        logger.error(f"批量分析API错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/jobs/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """获取作业状态"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute("""SELECT job_id, job_name, job_type, status, progress, 
                            result_path, error_message, created_at, started_at, completed_at
                     FROM analysis_jobs WHERE job_id = ?""", (job_id,))
        job = c.fetchone()
        conn.close()
        
        if not job:
            return jsonify({'error': '作业不存在'}), 404
        
        status_info = {
            'job_id': job[0],
            'job_name': job[1],
            'job_type': job[2],
            'status': job[3],
            'progress': job[4],
            'result_path': job[5],
            'error_message': job[6],
            'created_at': job[7],
            'started_at': job[8],
            'completed_at': job[9]
        }
        
        # 计算处理时间
        if job[8] and job[9]:  # started_at and completed_at
            start_time = datetime.fromisoformat(job[8])
            end_time = datetime.fromisoformat(job[9])
            status_info['processing_time_seconds'] = (end_time - start_time).total_seconds()
        elif job[8]:  # only started_at
            start_time = datetime.fromisoformat(job[8])
            status_info['elapsed_time_seconds'] = (datetime.now() - start_time).total_seconds()
        
        return jsonify({
            'success': True,
            'job_status': status_info
        })
        
    except Exception as e:
        logger.error(f"获取作业状态错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/jobs/<job_id>/result', methods=['GET'])
def get_job_result(job_id):
    """获取作业结果"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute("SELECT result_path, status FROM analysis_jobs WHERE job_id = ?", (job_id,))
        job = c.fetchone()
        conn.close()
        
        if not job:
            return jsonify({'error': '作业不存在'}), 404
        
        if job[1] != 'completed':
            return jsonify({'error': '作业尚未完成'}), 400
        
        if not job[0] or not os.path.exists(job[0]):
            return jsonify({'error': '结果文件不存在'}), 404
        
        # 读取结果文件
        with open(job[0], 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"获取作业结果错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/jobs/<job_id>/download', methods=['GET'])
def download_job_result(job_id):
    """下载作业结果文件"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute("SELECT result_path, status FROM analysis_jobs WHERE job_id = ?", (job_id,))
        job = c.fetchone()
        conn.close()
        
        if not job:
            return jsonify({'error': '作业不存在'}), 404
        
        if job[1] != 'completed':
            return jsonify({'error': '作业尚未完成'}), 400
        
        result_path = job[0]
        if not result_path or not os.path.exists(result_path):
            return jsonify({'error': '结果文件不存在'}), 404
        
        # 如果是Excel文件，直接提供下载
        if result_path.endswith('.xlsx'):
            return send_file(result_path, as_attachment=True, 
                           download_name=f"analysis_report_{job_id}.xlsx")
        
        # 如果是JSON结果文件，读取并查找Excel报告路径
        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            excel_path = result.get('visualization_results', {}).get('report_path')
            if excel_path and os.path.exists(excel_path):
                return send_file(excel_path, as_attachment=True,
                               download_name=f"analysis_report_{job_id}.xlsx")
            else:
                # 返回JSON文件
                return send_file(result_path, as_attachment=True,
                               download_name=f"analysis_result_{job_id}.json")
        
        except json.JSONDecodeError:
            return send_file(result_path, as_attachment=True,
                           download_name=f"analysis_result_{job_id}.txt")
        
    except Exception as e:
        logger.error(f"下载作业结果错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/jobs', methods=['GET'])
def list_jobs():
    """列出作业"""
    try:
        username = request.args.get('username')
        status = request.args.get('status')  # 可选状态过滤
        limit = int(request.args.get('limit', 50))
        
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        
        query = """SELECT j.job_id, j.job_name, j.job_type, j.status, j.progress,
                          j.created_at, j.started_at, j.completed_at, u.username
                   FROM analysis_jobs j 
                   JOIN users u ON j.user_id = u.id"""
        params = []
        
        conditions = []
        if username:
            conditions.append("u.username = ?")
            params.append(username)
        
        if status:
            conditions.append("j.status = ?")
            params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY j.created_at DESC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
        jobs = c.fetchall()
        conn.close()
        
        job_list = []
        for job in jobs:
            job_info = {
                'job_id': job[0],
                'job_name': job[1],
                'job_type': job[2],
                'status': job[3],
                'progress': job[4],
                'created_at': job[5],
                'started_at': job[6],
                'completed_at': job[7],
                'username': job[8]
            }
            job_list.append(job_info)
        
        return jsonify({
            'success': True,
            'jobs': job_list,
            'total_count': len(job_list)
        })
        
    except Exception as e:
        logger.error(f"列出作业错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/system/stats', methods=['GET'])
def system_statistics():
    """系统统计信息"""
    try:
        # 获取数据库统计
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        
        # 用户统计
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        # 作业统计
        c.execute("SELECT status, COUNT(*) FROM analysis_jobs GROUP BY status")
        job_stats = dict(c.fetchall())
        
        c.execute("SELECT COUNT(*) FROM analysis_jobs WHERE created_at > datetime('now', '-24 hours')")
        jobs_last_24h = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM analysis_jobs WHERE created_at > datetime('now', '-7 days')")
        jobs_last_7d = c.fetchone()[0]
        
        conn.close()
        
        # 获取文档管理器统计
        manager_stats = doc_manager.processing_stats.copy()
        uptime_seconds = (datetime.now() - manager_stats['start_time']).total_seconds()
        
        return jsonify({
            'success': True,
            'system_statistics': {
                'service_info': {
                    'version': '2.0.0',
                    'uptime_hours': round(uptime_seconds / 3600, 2),
                    'start_time': manager_stats['start_time'].isoformat()
                },
                'users': {
                    'total_registered': total_users
                },
                'jobs': {
                    'total_jobs': sum(job_stats.values()),
                    'status_distribution': job_stats,
                    'jobs_last_24h': jobs_last_24h,
                    'jobs_last_7d': jobs_last_7d
                },
                'processing': {
                    'total_analyses': manager_stats['total_analyses'],
                    'successful_analyses': manager_stats['successful_analyses'],
                    'failed_analyses': manager_stats['failed_analyses'],
                    'success_rate': manager_stats['successful_analyses'] / max(1, manager_stats['total_analyses']),
                    'ai_analyses_performed': manager_stats['ai_analyses_performed'],
                    'visualizations_created': manager_stats['visualizations_created']
                },
                'components': {
                    'ai_analyzer_available': bool(doc_manager.ai_analyzer),
                    'claude_api_configured': bool(app.config.get('CLAUDE_API_KEY')),
                    'excel_visualizer_available': True,
                    'adaptive_comparator_available': True
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取系统统计错误: {e}")
        return jsonify({'error': str(e)}), 500

# ===================== 兼容性API（保持原有接口） =====================

@app.route('/api/save_cookies', methods=['POST'])
def save_cookies():
    """保存用户cookies（兼容原API）"""
    try:
        data = request.json
        username = data.get('username')
        cookies = data.get('cookies')
        
        if not username or not cookies:
            return jsonify({'error': '用户名和cookies不能为空'}), 400
        
        # 使用简单的加密
        user_key = username + app.config['SECRET_KEY']
        cookie_hash = hashlib.sha256(cookies.encode()).hexdigest()
        
        # 简单的XOR加密
        key_hash = hashlib.sha256(user_key.encode()).hexdigest()
        encrypted = []
        for i, char in enumerate(cookies):
            encrypted.append(chr(ord(char) ^ ord(key_hash[i % len(key_hash)])))
        encrypted_cookies = ''.join(encrypted)
        
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        
        # 检查用户是否存在
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        
        if user:
            c.execute("""UPDATE users SET cookie_hash = ?, encrypted_cookies = ?, 
                        last_used = CURRENT_TIMESTAMP WHERE username = ?""",
                     (cookie_hash, encrypted_cookies, username))
        else:
            c.execute("""INSERT INTO users (username, cookie_hash, encrypted_cookies) 
                        VALUES (?, ?, ?)""",
                     (username, cookie_hash, encrypted_cookies))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Cookies保存成功',
            'username': username
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===================== 启动服务 =====================

if __name__ == '__main__':
    logger.info("🚀 启动腾讯文档管理系统 - 增强版API服务器")
    logger.info("📋 集成组件:")
    logger.info("   ✓ 自适应表格对比分析")
    logger.info("   ✓ 智能列匹配")
    if doc_manager.ai_analyzer:
        logger.info("   ✓ AI语义分析 (Claude)")
    else:
        logger.info("   ⚠ AI语义分析 (未配置API密钥)")
    logger.info("   ✓ Excel MCP可视化")
    logger.info("   ✓ 批量文档处理")
    logger.info("   ✓ 风险评估和建议")
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )