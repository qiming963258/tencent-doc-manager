#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档管理项目 - 完整集成测试系统（增强版）
端口: 8093
版本: 5.0.0 - Enhanced Production Integration
功能: 完整的端到端测试流程，从双文档下载到智能涂色上传
新增: 文件浏览器、历史记录、预设模板、高级配置等功能
作者: 系统架构团队
日期: 2025-09-10
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import os
import sys
import json
import time
import csv
import logging
import shutil
from pathlib import Path

# 加载.env文件
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ 已加载.env文件: {env_path}")
except ImportError:
    print("⚠️ dotenv未安装，使用系统环境变量")
import traceback
import uuid
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import subprocess
import glob
import hashlib

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')
# 修复：使用append而不是insert，避免production/core_modules的deepseek_client覆盖根目录版本
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

app = Flask(__name__)

# ==================== 项目正式路径配置 ====================
BASE_DIR = Path('/root/projects/tencent-doc-manager')
DOWNLOAD_DIR = BASE_DIR / 'downloads'
CSV_VERSIONS_DIR = BASE_DIR / 'csv_versions'
COMPARISON_RESULTS_DIR = BASE_DIR / 'comparison_results'
SCORING_RESULTS_DIR = BASE_DIR / 'scoring_results' / 'detailed'
EXCEL_OUTPUTS_DIR = BASE_DIR / 'excel_outputs' / 'marked'
LOG_DIR = BASE_DIR / 'logs'
TEMP_DIR = BASE_DIR / 'temp_workflow'
HISTORY_DIR = BASE_DIR / 'workflow_history'
PRESETS_DIR = BASE_DIR / 'workflow_presets'

# 确保所有目录存在
for dir_path in [DOWNLOAD_DIR, CSV_VERSIONS_DIR, COMPARISON_RESULTS_DIR, 
                 SCORING_RESULTS_DIR, EXCEL_OUTPUTS_DIR, LOG_DIR, TEMP_DIR,
                 HISTORY_DIR, PRESETS_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)

# ==================== 日志配置 ====================
log_file = LOG_DIR / f'integrated_test_8093_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 全局状态管理 ====================
class WorkflowState:
    def __init__(self):
        self.current_task = ""
        self.progress = 0
        self.logs = []
        self.status = "idle"  # idle, running, completed, error
        self.results = {}
        self.baseline_file = None
        self.target_file = None
        self.score_file = None
        self.marked_file = None
        self.upload_url = None
        self.start_time = None
        self.end_time = None
        self.execution_id = None
        self.advanced_settings = {}
        
    def add_log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,  # 改为timestamp以匹配8089期望的格式
            "level": level,
            "message": message
        }
        self.logs.append(log_entry)
        logger.info(f"[{level}] {message}")
        
    def update_progress(self, task, progress):
        self.current_task = task
        self.progress = progress
        
    def reset(self):
        self.__init__()
        
    def save_to_history(self):
        """保存执行历史"""
        if self.execution_id:
            history_file = HISTORY_DIR / f"workflow_{self.execution_id}.json"
            history_data = {
                "id": self.execution_id,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "status": self.status,
                "results": self.results,
                "logs": self.logs[-20:],  # 只保存最后20条日志
                "settings": self.advanced_settings
            }
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)

workflow_state = WorkflowState()

# ==================== 工作流预设管理 ====================
class PresetManager:
    @staticmethod
    def save_preset(name, config):
        """保存预设配置"""
        preset_file = PRESETS_DIR / f"{name}.json"
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_preset(name):
        """加载预设配置"""
        preset_file = PRESETS_DIR / f"{name}.json"
        if preset_file.exists():
            with open(preset_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    @staticmethod
    def list_presets():
        """列出所有预设"""
        presets = []
        for preset_file in PRESETS_DIR.glob("*.json"):
            with open(preset_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                presets.append({
                    "name": preset_file.stem,
                    "description": config.get("description", "无描述"),
                    "created": preset_file.stat().st_mtime
                })
        return sorted(presets, key=lambda x: x['created'], reverse=True)

# ==================== 导入生产模块（符合规范版） ====================
MODULES_STATUS = {}

# 1. 时间管理器（核心模块，符合规范）
try:
    from production.core_modules.week_time_manager import WeekTimeManager
    week_manager = WeekTimeManager()
    MODULES_STATUS['week_manager'] = True
    logger.info("✅ 成功导入周时间管理器")
except ImportError as e:
    MODULES_STATUS['week_manager'] = False
    logger.warning(f"⚠️ 无法导入周时间管理器: {e}")
    week_manager = None

# 2. 下载模块（使用符合架构规格的PlaywrightDownloader）
try:
    from production.core_modules.playwright_downloader import PlaywrightDownloader
    # 为了向后兼容，保留TencentDocAutoExporter的别名
    TencentDocAutoExporter = PlaywrightDownloader
    MODULES_STATUS['downloader'] = True
    logger.info("✅ 成功导入PlaywrightDownloader（符合架构规格）")
except ImportError:
    try:
        # 备用：使用原有的TencentDocAutoExporter
        from production.core_modules.tencent_export_automation import TencentDocAutoExporter
        MODULES_STATUS['downloader'] = True
        logger.info("✅ 成功导入TencentDocAutoExporter（备用）")
    except ImportError as e:
        MODULES_STATUS['downloader'] = False
        logger.error(f"❌ 无法导入下载模块: {e}")

# 3. 比较模块（使用UnifiedCSVComparator符合规范）
try:
    from unified_csv_comparator import UnifiedCSVComparator
    MODULES_STATUS['comparator'] = True
    logger.info("✅ 成功导入统一CSV对比器")
except ImportError as e:
    MODULES_STATUS['comparator'] = False
    logger.error(f"❌ 无法导入比较模块: {e}")

# 4. 列标准化模块（优先使用V3版本）
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

# 5. DeepSeek客户端（用于AI增强）
try:
    from production.core_modules.deepseek_client import DeepSeekClient
    MODULES_STATUS['deepseek'] = True
    logger.info("✅ 成功导入DeepSeek客户端")
except ImportError as e:
    MODULES_STATUS['deepseek'] = False
    logger.warning(f"⚠️ DeepSeek客户端未加载: {e}")

# 6. L2语义分析模块
try:
    from production.core_modules.l2_semantic_analysis_two_layer import L2SemanticAnalyzer
    MODULES_STATUS['l2_analyzer'] = True
    logger.info("✅ 成功导入L2语义分析模块")
except ImportError as e:
    MODULES_STATUS['l2_analyzer'] = False
    logger.error(f"❌ 无法导入L2语义分析模块: {e}")

# 5. 智能标记模块
try:
    from intelligent_excel_marker import IntelligentExcelMarker
    from production.scoring_engine.integrated_scorer import IntegratedScorer
    MODULES_STATUS['marker'] = True
    logger.info("✅ 成功导入智能标记模块")
except ImportError as e:
    MODULES_STATUS['marker'] = False
    logger.error(f"❌ 无法导入智能标记模块: {e}")

# 6. Excel修复模块
try:
    from fix_tencent_excel import fix_tencent_excel
    MODULES_STATUS['fixer'] = True
    logger.info("✅ 成功导入Excel修复模块")
except ImportError as e:
    MODULES_STATUS['fixer'] = False
    logger.error(f"❌ 无法导入Excel修复模块: {e}")

# 7. 上传模块（优先使用生产级v3 - 2025-09-20更新）
try:
    # 生产级v3模块：95%+链接准确率，多策略识别（推荐）
    from production.core_modules.tencent_doc_upload_production_v3 import sync_upload_v3 as sync_upload_file
    MODULES_STATUS['uploader'] = True
    logger.info("✅ 成功导入上传模块(生产级v3，推荐)")
except ImportError:
    try:
        # 备用1：终极修复版（临时方案，不推荐）
        from tencent_doc_uploader_ultimate import sync_upload_file
        MODULES_STATUS['uploader'] = True
        logger.warning("⚠️ 使用上传模块(终极版，可能返回错误链接)")
    except ImportError:
        try:
            # 备用2：修复版（临时方案，不推荐）
            from tencent_doc_uploader_fixed import sync_upload_file
            MODULES_STATUS['uploader'] = True
            logger.warning("⚠️ 使用上传模块(修复版，可能返回错误链接)")
        except ImportError:
            try:
                # 备用3：原版本（会返回错误链接，强烈不推荐）
                from tencent_doc_uploader import sync_upload_file
                MODULES_STATUS['uploader'] = True
                logger.error("❌ 使用上传模块(原版本，会返回错误链接!)")
            except ImportError as e:
                MODULES_STATUS['uploader'] = False
                logger.error(f"❌ 无法导入任何上传模块: {e}")

# 8. 周时间管理器
try:
    from production.core_modules.week_time_manager import WeekTimeManager
    MODULES_STATUS['week_manager'] = True
    logger.info("✅ 成功导入周时间管理器")
except ImportError as e:
    MODULES_STATUS['week_manager'] = False
    logger.error(f"❌ 无法导入周时间管理器: {e}")

# ==================== 智能基线下载和存储函数 ====================
def download_and_store_baseline(baseline_url: str, cookie: str, week_manager=None, workflow_state=None):
    """
    下载基线文件并按照规范存储到当周baseline目录
    
    Args:
        baseline_url: 基线文档URL
        cookie: 认证cookie
        week_manager: 周时间管理器实例
    
    Returns:
        str: 规范化后的基线文件路径
    """
    try:
        import shutil
        import re
        from urllib.parse import urlparse, parse_qs
        
        # 获取当前周信息
        now = datetime.now()
        week_info = now.isocalendar()
        current_year = week_info[0]
        current_week = week_info[1]
        
        # 确定基线应该存储的周数（根据时间管理规范）
        weekday = now.weekday()  # 0=周一
        hour = now.hour
        
        if weekday < 1 or (weekday == 1 and hour < 12):
            # 周一全天 OR 周二12点前 -> 使用上周
            target_week = current_week - 1
        else:
            # 周二12点后至周日 -> 使用本周
            target_week = current_week
        
        logger.info(f"基线文件将存储到第{target_week}周")
        if workflow_state:
            workflow_state.add_log(f"📁 基线文件将存储到第{target_week}周", "INFO")
        
        # 创建目标目录
        baseline_dir = Path(f"/root/projects/tencent-doc-manager/csv_versions/{current_year}_W{target_week:02d}/baseline")
        baseline_dir.mkdir(parents=True, exist_ok=True)
        
        # 下载文档
        if workflow_state:
            workflow_state.add_log("🌐 初始化浏览器下载器...", "INFO")
        exporter = TencentDocAutoExporter()
        if workflow_state:
            workflow_state.add_log(f"🔗 正在打开腾讯文档: {baseline_url}", "INFO")
            workflow_state.add_log("🍪 设置Cookie认证...", "INFO")
            workflow_state.add_log("⏳ 开始下载，请耐心等待（通常需要30-60秒）...", "INFO")
        # 下载文档 - 根据下载器类型选择接口
        if hasattr(exporter, 'download'):
            # PlaywrightDownloader接口（异步）
            import asyncio
            result = asyncio.run(exporter.download(baseline_url, cookies=cookie, format='csv'))
        else:
            # TencentDocAutoExporter接口（同步）
            result = exporter.export_document(baseline_url, cookies=cookie, format='csv')
        if workflow_state:
            workflow_state.add_log("✅ 下载请求已完成", "INFO")
        
        if not result or not result.get('success'):
            error_msg = result.get('error', '未知错误') if result else '下载器返回空结果'
            logger.error(f"基线文档下载失败: {error_msg}")
            if workflow_state:
                workflow_state.add_log(f"❌ 下载失败: {error_msg}", "ERROR")
                workflow_state.add_log("💡 提示: 请检查Cookie是否有效或网络连接", "WARNING")
            return None
        
        downloaded_file = result.get('file_path')
        if not downloaded_file or not os.path.exists(downloaded_file):
            logger.error("下载的文件不存在")
            return None
        
        # 从配置文件获取文档名称
        doc_name = "基线文档"
        try:
            # 加载文档配置
            import json
            config_file = '/root/projects/tencent-doc-manager/production/config/real_documents.json'
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 根据URL查找文档名
            for doc in config.get('documents', []):
                if doc['url'] in baseline_url:
                    # 使用简化的文档名（去掉前缀）
                    full_name = doc['name']
                    # 去掉"副本-测试版本-"前缀
                    doc_name = full_name.replace('副本-测试版本-', '').replace('测试版本-', '')
                    logger.info(f"使用配置文件中的文档名: {doc_name}")
                    break
            else:
                # 如果没有找到，fallback到从URL提取
                parsed_url = urlparse(baseline_url)
                if 'sheet' in parsed_url.path:
                    # 腾讯文档链接格式
                    path_parts = parsed_url.path.split('/')
                    if len(path_parts) > 2:
                        doc_id = path_parts[-1]
                        # 从下载的文件名中提取文档名
                        original_name = os.path.basename(downloaded_file)
                        # 移除时间戳和扩展名
                        doc_name_match = re.search(r'^(.+?)_\d{8}_\d{4}', original_name)
                        if doc_name_match:
                            doc_name = doc_name_match.group(1)
                        else:
                            # 使用文件名的前部分
                            doc_name = original_name.split('_')[0] if '_' in original_name else original_name.split('.')[0]
                logger.warning(f"未在配置中找到文档，使用fallback名称: {doc_name}")
        except Exception as e:
            logger.warning(f"无法从配置解析文档名: {e}")
        
        # 生成符合规范的文件名
        # 格式: tencent_{doc_name}_{YYYYMMDD_HHMM}_baseline_W{week}.csv
        timestamp = now.strftime("%Y%m%d_%H%M")
        normalized_name = f"tencent_{doc_name}_{timestamp}_baseline_W{target_week:02d}.csv"
        
        # 清理文件名（移除可能的特殊字符）
        normalized_name = re.sub(r'[<>:"|?*]', '_', normalized_name)
        normalized_name = re.sub(r'_{2,}', '_', normalized_name)  # 移除连续的下划线
        
        # 目标文件路径
        target_path = baseline_dir / normalized_name
        
        # 移动并重命名文件
        shutil.move(downloaded_file, str(target_path))
        logger.info(f"基线文件已规范化存储: {target_path}")
        
        return str(target_path)
        
    except Exception as e:
        logger.error(f"下载和存储基线文件失败: {e}")
        return None

def download_and_store_target(target_url: str, cookie: str, week_manager=None, workflow_state=None):
    """
    下载目标文档并规范化存储到对应的时间文件夹（midweek/weekend）

    Args:
        target_url: 腾讯文档URL
        cookie: 认证cookie
        week_manager: 周管理器实例
        workflow_state: 工作流状态对象

    Returns:
        str: 规范化后的文件路径，失败返回None
    """
    try:
        if not week_manager:
            logger.error("周管理器未初始化")
            return None

        # 创建下载器实例
        exporter = TencentDocAutoExporter()

        if workflow_state:
            workflow_state.add_log("🌐 开始下载目标文档...", "INFO")

        # 下载文档 - 根据下载器类型选择接口
        if hasattr(exporter, 'download'):
            # PlaywrightDownloader接口（异步）
            import asyncio
            result = asyncio.run(exporter.download(target_url, cookies=cookie, format='csv'))
        else:
            # TencentDocAutoExporter接口（同步）
            result = exporter.export_document(target_url, cookies=cookie, format='csv')

        if not result or not result.get('success'):
            logger.error(f"目标文档下载失败: {result.get('error') if result else '未知错误'}")
            return None

        downloaded_file = result.get('file_path')
        if not os.path.exists(downloaded_file):
            logger.error(f"下载的文件不存在: {downloaded_file}")
            return None

        # 从配置文件获取文档名
        doc_name = 'target_doc'
        try:
            # 加载文档配置
            import json
            config_file = '/root/projects/tencent-doc-manager/production/config/real_documents.json'
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 根据URL查找文档名
            for doc in config.get('documents', []):
                if doc['url'] in target_url:
                    # 使用简化的文档名（去掉前缀）
                    full_name = doc['name']
                    # 去掉"副本-测试版本-"前缀
                    doc_name = full_name.replace('副本-测试版本-', '').replace('测试版本-', '')
                    logger.info(f"使用配置文件中的文档名: {doc_name}")
                    break
            else:
                # 如果没有找到，fallback到从URL提取
                from urllib.parse import urlparse
                path_parts = urlparse(target_url).path.split('/')
                if len(path_parts) > 1:
                    doc_name = path_parts[-1] or path_parts[-2]
                logger.warning(f"未在配置中找到文档，使用URL提取的名称: {doc_name}")
        except Exception as e:
            logger.error(f"获取文档名失败: {e}")
            pass

        # 获取当前时间信息
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour

        # 判断版本类型（根据WeekTimeManager的逻辑）
        if weekday == 5 and hour >= 19:  # 周六晚上7点后
            version_type = "weekend"
        else:
            version_type = "midweek"

        if workflow_state:
            workflow_state.add_log(f"📁 目标文档将存储为{version_type}版本", "INFO")

        # 获取周信息和目录
        week_info = week_manager.get_current_week_info()
        current_week = week_info['week_number']
        week_dirs = week_manager.get_week_directory(week_info['year'], current_week)

        # 获取目标目录
        target_dir = week_dirs / version_type
        target_dir.mkdir(parents=True, exist_ok=True)

        # 生成规范化文件名
        file_extension = os.path.splitext(downloaded_file)[1].lstrip('.') or 'csv'
        target_filename = week_manager.generate_filename(
            doc_name=doc_name,
            file_time=now,
            version_type=version_type,
            week_number=current_week,
            file_extension=file_extension
        )

        # 目标路径
        target_path = target_dir / target_filename

        # 移动并重命名文件
        shutil.move(downloaded_file, str(target_path))
        logger.info(f"目标文件已规范化存储: {target_path}")

        if workflow_state:
            workflow_state.add_log(f"✅ 目标文档已存储到{version_type}文件夹: {target_filename}", "INFO")

        return str(target_path)

    except Exception as e:
        logger.error(f"下载和存储目标文件失败: {e}")
        if workflow_state:
            workflow_state.add_log(f"❌ 目标文档存储失败: {str(e)}", "ERROR")
        return None

# ==================== 核心工作流函数 ====================
def run_complete_workflow(baseline_url: str, target_url: str, cookie: str, advanced_settings: dict = None):
    """
    执行完整的工作流程（增强版）
    """
    try:
        workflow_state.reset()
        workflow_state.status = "running"
        workflow_state.start_time = datetime.now()
        workflow_state.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        workflow_state.advanced_settings = advanced_settings or {}
        
        # ========== 步骤1: 获取基线文件 ==========
        workflow_state.update_progress("获取基线文档", 10)
        workflow_state.add_log("开始获取基线文档...")

        # 检查是否强制下载新文件
        force_download = advanced_settings.get('force_download', True)  # 默认改为True，始终下载
        use_existing_baseline = advanced_settings.get('use_existing_baseline', False)  # 是否使用现有基线

        baseline_file = None

        # 如果baseline_url为None或use_existing_baseline为True，必须使用现有基线
        if baseline_url is None or use_existing_baseline:
            workflow_state.add_log("📂 刷新模式：使用现有基线文件")
            if MODULES_STATUS.get('week_manager') and week_manager:
                try:
                    baseline_files, baseline_desc = week_manager.find_baseline_files()
                    if baseline_files:
                        baseline_file = baseline_files[0]  # 使用最新的基线文件
                        workflow_state.baseline_file = baseline_file
                        workflow_state.add_log(f"✅ 找到基线文件: {os.path.basename(baseline_file)}")
                        workflow_state.add_log(f"📊 基线描述: {baseline_desc}")
                    else:
                        workflow_state.add_log("❌ 未找到基线文件，请先下载基线", "ERROR")
                        raise Exception("未找到基线文件，请先下载基线")
                except Exception as e:
                    workflow_state.add_log(f"❌ 基线文件查找失败: {str(e)}", "ERROR")
                    raise
            else:
                workflow_state.add_log("❌ 周管理器未加载，无法查找基线", "ERROR")
                raise Exception("周管理器未加载，无法查找基线文件")

        # 如果有baseline_url，根据force_download决定是否下载
        elif baseline_url:
            # 如果不强制下载，优先尝试使用本地文件
            if not force_download and MODULES_STATUS.get('week_manager') and week_manager:
                try:
                    baseline_files, baseline_desc = week_manager.find_baseline_files()
                    if baseline_files:
                        baseline_file = baseline_files[0]  # 使用最新的基线文件
                        workflow_state.baseline_file = baseline_file
                        workflow_state.add_log(f"✅ 使用本地基线文件: {os.path.basename(baseline_file)}")
                except Exception as e:
                    workflow_state.add_log(f"⚠️ 本地文件查找失败: {str(e)}", "WARNING")
            elif force_download:
                workflow_state.add_log("🔄 强制下载模式：跳过本地文件检查")

            # 如果本地没有基线文件，则下载并规范化存储
            if not baseline_file:
                if MODULES_STATUS.get('downloader'):
                    workflow_state.add_log("开始下载基线文档并规范化存储...")

                    # 下载基线文档到规范位置
                    baseline_file = download_and_store_baseline(
                        baseline_url=baseline_url,
                        cookie=cookie,
                        week_manager=week_manager,
                        workflow_state=workflow_state
                    )

                    if baseline_file:
                        workflow_state.baseline_file = baseline_file
                        workflow_state.add_log(f"✅ 基线文档下载并规范化存储成功: {os.path.basename(baseline_file)}")
                    else:
                        raise Exception("基线文档下载或存储失败")
                else:
                    # 不允许降级，必须有下载模块
                    workflow_state.add_log("❌ 下载模块未加载", "ERROR")
                    raise Exception("下载模块未加载，无法继续")
        
        # ========== 步骤2: 获取目标文件 ==========
        workflow_state.update_progress("获取目标文档", 20)
        workflow_state.add_log("开始获取目标文档...")
        
        # 如果不强制下载，优先尝试使用本地文件（但现在force_download默认为True）
        target_file = None
        if not force_download and MODULES_STATUS.get('week_manager') and week_manager:
            try:
                target_files = week_manager.find_target_files()
                if target_files:
                    target_file = target_files[0]  # 使用最新的目标文件
                    workflow_state.target_file = target_file
                    workflow_state.add_log(f"✅ 使用本地目标文件: {os.path.basename(target_file)}")
            except Exception as e:
                workflow_state.add_log(f"⚠️ 本地文件查找失败: {str(e)}", "WARNING")
        elif force_download:
            workflow_state.add_log("🔄 强制下载模式：跳过本地文件检查")
        
        # 如果本地没有目标文件，则下载并规范化存储
        if not target_file:
            if MODULES_STATUS.get('downloader'):
                workflow_state.add_log("开始下载目标文档并规范化存储...")

                # 使用新的规范化存储函数
                target_file = download_and_store_target(
                    target_url=target_url,
                    cookie=cookie,
                    week_manager=week_manager,
                    workflow_state=workflow_state
                )

                if target_file:
                    workflow_state.target_file = target_file
                    workflow_state.add_log(f"✅ 目标文档下载并规范化存储成功: {os.path.basename(target_file)}")
                else:
                    # 输出详细的错误信息
                    workflow_state.add_log(f"❌ 目标文档下载或存储失败", "ERROR")
                    workflow_state.add_log(f"目标URL: {target_url}", "ERROR")
                    workflow_state.add_log("💡 提示: 请检查Cookie是否有效或网络连接", "WARNING")
                    raise Exception("目标文档下载或存储失败")
            else:
                workflow_state.target_file = str(DOWNLOAD_DIR / "test_target.csv")
                workflow_state.add_log("⚠️ 下载模块未加载，使用测试文件", "WARNING")
        
        # ========== 步骤3: CSV对比分析 ==========
        workflow_state.update_progress("执行CSV对比分析", 30)
        workflow_state.add_log("开始对比分析...")
        
        comparison_result = None
        if MODULES_STATUS.get('comparator'):
            # 使用统一CSV对比器（根据规范要求）
            unified_comparator = UnifiedCSVComparator()
            
            # 直接对比CSV文件
            comparison_result = unified_comparator.compare(
                workflow_state.baseline_file,
                workflow_state.target_file
            )
            
            # 保存对比结果
            comparison_file = COMPARISON_RESULTS_DIR / f"comparison_{workflow_state.execution_id}.json"
            with open(comparison_file, 'w', encoding='utf-8') as f:
                json.dump(comparison_result, f, ensure_ascii=False, indent=2)
            
            # 获取变更数量
            num_changes = comparison_result.get('statistics', {}).get('total_modifications', 0)
            workflow_state.add_log(f"✅ 对比分析完成，发现 {num_changes} 处变更")
        else:
            workflow_state.add_log("⚠️ 比较模块未加载，跳过", "WARNING")
        
        # ========== 步骤4: 列标准化（使用V3版本） ==========
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
                    from production.core_modules.column_standardization_prompt import ColumnStandardizationPrompt
                    standardizer = ColumnStandardizationPrompt()
                    
                    # 提取列名进行标准化
                    if workflow_state.baseline_file and workflow_state.target_file:
                        # 读取文件获取列名
                        with open(workflow_state.baseline_file, 'r', encoding='utf-8') as f:
                            baseline_headers = csv.reader(f).__next__()
                        with open(workflow_state.target_file, 'r', encoding='utf-8') as f:
                            target_headers = csv.reader(f).__next__()
                        
                        # 调用标准化（这里可能需要AI，但我们使用规则基础方法）
                        standardized_result = {
                            'baseline_headers': baseline_headers,
                            'target_headers': target_headers,
                            'mapping': dict(zip(target_headers, baseline_headers[:len(target_headers)]))
                        }
                        workflow_state.add_log(f"⚠️ 使用旧版列标准化，映射了 {len(standardized_result['mapping'])} 个列", "WARNING")
            except Exception as e:
                workflow_state.add_log(f"⚠️ 列标准化出错: {str(e)}", "WARNING")
        else:
            workflow_state.add_log("⚠️ 标准化模块未加载或无对比结果", "WARNING")
        
        # ========== 步骤5: L2语义分析 + L1L3规则打分 ==========
        workflow_state.update_progress("语义分析和打分", 50)
        workflow_state.add_log("开始L2语义分析和L1L3规则打分...")
        
        semantic_scores = None
        if MODULES_STATUS.get('l2_analyzer') and comparison_result:
            try:
                from production.core_modules.l2_semantic_analysis_two_layer import L2SemanticAnalyzer
                analyzer = L2SemanticAnalyzer()
                
                # 准备修改数据格式（兼容UnifiedCSVComparator的输出）
                modifications = []
                # UnifiedCSVComparator使用'modifications'而不是'changes'
                if comparison_result and 'modifications' in comparison_result:
                    for change in comparison_result['modifications']:
                        # 从单元格地址提取行号
                        cell = change.get('cell', 'A1')
                        row_num = int(''.join(filter(str.isdigit, cell))) if any(c.isdigit() for c in cell) else 0
                        
                        modifications.append({
                            'column_name': cell[0] if cell else '',
                            'old_value': change.get('old', ''),
                            'new_value': change.get('new', ''),
                            'row': row_num,
                            'cell': cell
                        })
                
                # 执行语义分析（使用正确的方法名）
                semantic_scores = analyzer.analyze_modifications(modifications)
                workflow_state.add_log(f"✅ 语义分析完成，分析了 {len(modifications)} 处变更")
            except Exception as e:
                workflow_state.add_log(f"❌ 语义分析失败: {str(e)}", "ERROR")
                raise  # 不允许降级，直接抛出异常
        
        # ========== 步骤6: 生成详细打分JSON ==========
        workflow_state.update_progress("生成详细打分", 60)
        workflow_state.add_log("生成详细打分JSON...")
        
        if MODULES_STATUS.get('marker') and comparison_result:
            try:
                # 使用统一的IntegratedScorer（必须使用AI，L2强制要求）
                scorer = IntegratedScorer(use_ai=True, cache_enabled=False)
                
                # 将对比结果保存为临时JSON文件供scorer处理
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                    json.dump(comparison_result, tmp)
                    tmp_input_file = tmp.name
                
                # 使用IntegratedScorer处理文件
                score_file_path = scorer.process_file(
                    input_file=tmp_input_file,
                    output_dir=str(SCORING_RESULTS_DIR)
                )
                
                # 删除临时文件
                os.unlink(tmp_input_file)
                
                workflow_state.score_file = score_file_path
                workflow_state.add_log(f"✅ 详细打分生成完成: {os.path.basename(score_file_path)}")
            except Exception as e:
                # 不允许降级，直接抛出异常
                workflow_state.add_log(f"❌ 打分生成失败: {str(e)}", "ERROR")
                raise
        
        # ========== 步骤7: 下载目标XLSX ==========
        workflow_state.update_progress("下载Excel格式", 70)
        workflow_state.add_log("下载目标文档的Excel格式...")
        
        excel_file = None
        if MODULES_STATUS.get('downloader'):
            # 为Excel下载创建新的exporter实例
            exporter_excel = TencentDocAutoExporter()
            
            import asyncio
            if hasattr(exporter_excel, 'download'):
                # PlaywrightDownloader接口
                excel_result = asyncio.run(exporter_excel.download(target_url, cookies=cookie, format='xlsx'))
            else:
                # TencentDocAutoExporter接口
                excel_result = asyncio.run(exporter_excel.export_document(target_url, cookies=cookie, format='xlsx'))
            if excel_result and excel_result.get('success'):
                excel_file = excel_result.get('file_path')
                workflow_state.add_log(f"✅ Excel文档下载成功: {os.path.basename(excel_file)}")
            else:
                workflow_state.add_log("⚠️ Excel下载失败", "WARNING")
        
        # ========== 步骤8: 修复Excel格式 ==========
        if excel_file and MODULES_STATUS.get('fixer'):
            workflow_state.update_progress("修复Excel格式", 75)
            workflow_state.add_log("修复腾讯文档Excel格式问题...")
            
            fixed_file = fix_tencent_excel(excel_file)
            if fixed_file:
                excel_file = fixed_file
                workflow_state.add_log(f"✅ Excel格式修复完成")
        
        # ========== 步骤9: 应用条纹涂色 ==========
        if excel_file and MODULES_STATUS.get('marker') and workflow_state.score_file:
            workflow_state.update_progress("应用智能涂色", 85)
            workflow_state.add_log("应用条纹涂色标记...")
            
            marker = IntelligentExcelMarker()
            marked_file = marker.apply_striped_coloring(
                excel_file,
                workflow_state.score_file
            )
            
            if marked_file:
                workflow_state.marked_file = marked_file
                workflow_state.add_log(f"✅ 涂色标记完成: {os.path.basename(marked_file)}")
        
        # ========== 步骤10: 上传到腾讯文档 ==========
        if workflow_state.marked_file and MODULES_STATUS.get('uploader'):
            workflow_state.update_progress("上传腾讯文档", 95)
            workflow_state.add_log("上传处理后的文档到腾讯文档...")
            
            # 根据高级设置决定上传方式
            upload_option = advanced_settings.get('upload_option', 'new')
            target_doc_url = advanced_settings.get('upload_target_url', '')
            
            upload_result = sync_upload_file(
                workflow_state.marked_file,
                upload_option=upload_option,
                target_url=target_doc_url,
                cookie_string=cookie
            )
            
            if upload_result and upload_result.get('success'):
                workflow_state.upload_url = upload_result.get('url')
                workflow_state.add_log(f"✅ 文档上传成功!")
                if workflow_state.upload_url:
                    workflow_state.add_log(f"📎 文档链接: {workflow_state.upload_url}")
            else:
                workflow_state.add_log("⚠️ 文档上传失败", "WARNING")
        
        # ========== 完成 ==========
        workflow_state.update_progress("处理完成", 100)
        workflow_state.status = "completed"
        workflow_state.end_time = datetime.now()
        workflow_state.add_log("🎉 所有步骤执行完成!", "SUCCESS")
        
        # 保存结果
        workflow_state.results = {
            "baseline_file": workflow_state.baseline_file,
            "target_file": workflow_state.target_file,
            "score_file": workflow_state.score_file,
            "marked_file": workflow_state.marked_file,
            "upload_url": workflow_state.upload_url,
            "execution_time": str(workflow_state.end_time - workflow_state.start_time) if workflow_state.end_time and workflow_state.start_time else None
        }
        
        # 保存历史记录
        workflow_state.save_to_history()
        
    except Exception as e:
        workflow_state.status = "error"
        workflow_state.end_time = datetime.now()
        workflow_state.add_log(f"❌ 执行出错: {str(e)}", "ERROR")
        workflow_state.save_to_history()
        logger.error(f"工作流执行失败: {e}", exc_info=True)

# ==================== Flask路由 ====================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/modules')
def get_modules():
    """获取模块加载状态"""
    return jsonify(MODULES_STATUS)

@app.route('/api/status')
def get_status():
    """获取当前工作流状态"""
    return jsonify({
        "status": workflow_state.status,
        "progress": workflow_state.progress,
        "current_task": workflow_state.current_task,
        "logs": workflow_state.logs[-50:],  # 最后50条日志
        "results": workflow_state.results
    })

@app.route('/api/save-cookie', methods=['POST'])
def save_cookie():
    """保存Cookie到配置文件"""
    try:
        data = request.json
        cookie_string = data.get('cookie')
        
        if not cookie_string:
            return jsonify({"error": "Cookie不能为空"}), 400
        
        # Cookie配置文件路径
        cookie_file = Path("/root/projects/tencent-doc-manager/config/cookies.json")
        
        # 解析Cookie字符串
        cookie_list = []
        for cookie_part in cookie_string.split('; '):
            if '=' in cookie_part:
                name, value = cookie_part.split('=', 1)
                cookie_list.append({
                    "name": name.strip(),
                    "value": value.strip()
                })
        
        # 构建Cookie配置
        cookie_config = {
            "cookies": cookie_list,
            "cookie_string": cookie_string,
            "current_cookies": cookie_string,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 确保目录存在
        cookie_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存到文件
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookie_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Cookie已保存到配置文件: {cookie_file}")
        return jsonify({
            "success": True,
            "message": f"Cookie已成功保存到配置文件",
            "cookie_count": len(cookie_list),
            "last_updated": cookie_config["last_updated"]
        })
        
    except Exception as e:
        logger.error(f"保存Cookie失败: {e}")
        return jsonify({"error": f"保存Cookie失败: {str(e)}"}), 500

@app.route('/api/load-cookie', methods=['GET'])
def load_cookie():
    """从配置文件加载Cookie"""
    try:
        cookie_file = Path("/root/projects/tencent-doc-manager/config/cookies.json")
        
        if not cookie_file.exists():
            return jsonify({"error": "Cookie配置文件不存在"}), 404
        
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie_config = json.load(f)
        
        return jsonify({
            "success": True,
            "cookie": cookie_config.get("cookie_string", ""),
            "last_updated": cookie_config.get("last_updated", ""),
            "cookie_count": len(cookie_config.get("cookies", []))
        })
        
    except Exception as e:
        logger.error(f"加载Cookie失败: {e}")
        return jsonify({"error": f"加载Cookie失败: {str(e)}"}), 500

@app.route('/api/start', methods=['POST'])
def start_workflow():
    """启动工作流"""
    if workflow_state.status == "running":
        return jsonify({"error": "工作流正在运行中"}), 400
    
    data = request.json
    baseline_url = data.get('baseline_url')
    target_url = data.get('target_url')
    cookie = data.get('cookie')
    advanced_settings = data.get('advanced_settings', {})
    
    # 刷新模式：baseline_url可以为None，但target_url和cookie必须提供
    if not target_url or not cookie:
        return jsonify({"error": "缺少必要参数: target_url和cookie"}), 400
    
    # 在后台线程中运行工作流
    thread = threading.Thread(
        target=run_complete_workflow,
        args=(baseline_url, target_url, cookie, advanced_settings)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "工作流已启动", "execution_id": workflow_state.execution_id})

@app.route('/api/files/<path:category>')
def list_files(category):
    """列出特定类别的文件"""
    file_dirs = {
        'downloads': DOWNLOAD_DIR,
        'csv_versions': CSV_VERSIONS_DIR,
        'comparisons': COMPARISON_RESULTS_DIR,
        'scores': SCORING_RESULTS_DIR,
        'excel_outputs': EXCEL_OUTPUTS_DIR
    }
    
    if category not in file_dirs:
        return jsonify({"error": "无效的文件类别"}), 400
    
    target_dir = file_dirs[category]
    files = []
    
    for file_path in sorted(target_dir.glob('*'), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
        if file_path.is_file():
            files.append({
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                'path': str(file_path)
            })
    
    return jsonify(files)

@app.route('/api/presets')
def list_presets():
    """列出所有预设"""
    return jsonify(PresetManager.list_presets())

@app.route('/api/presets/<name>')
def get_preset(name):
    """获取特定预设"""
    preset = PresetManager.load_preset(name)
    if preset:
        return jsonify(preset)
    return jsonify({"error": "预设不存在"}), 404

@app.route('/api/presets', methods=['POST'])
def save_preset():
    """保存预设"""
    data = request.json
    name = data.get('name')
    config = data.get('config')
    
    if not name or not config:
        return jsonify({"error": "缺少预设名称或配置"}), 400
    
    PresetManager.save_preset(name, config)
    return jsonify({"message": "预设保存成功"})

@app.route('/api/history')
def list_history():
    """列出执行历史"""
    history_files = sorted(HISTORY_DIR.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)[:20]
    history = []
    
    for history_file in history_files:
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            history.append({
                'id': data['id'],
                'start_time': data['start_time'],
                'end_time': data['end_time'],
                'status': data['status'],
                'results': data.get('results', {})
            })
    
    return jsonify(history)

@app.route('/api/download/<path:file_path>')
def download_file(file_path):
    """下载文件"""
    file_path = Path(file_path)
    if file_path.exists() and file_path.is_file():
        return send_file(str(file_path), as_attachment=True)
    return jsonify({"error": "文件不存在"}), 404

# ==================== HTML模板（增强版） ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档智能处理系统 - 完整集成测试（增强版）</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        
        .header p {
            color: #666;
            text-align: center;
        }
        
        .version-badge {
            display: inline-block;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 400px 1fr 400px;
            gap: 30px;
        }
        
        .panel {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: none;
            color: #666;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom: 3px solid #667eea;
            margin-bottom: -2px;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        
        .form-group input, 
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus, 
        .form-group textarea:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: #f5f5f5;
            color: #333;
        }
        
        .progress-bar {
            height: 40px;
            background: #f0f0f0;
            border-radius: 20px;
            margin: 20px 0;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            transition: width 0.5s ease;
        }
        
        .modules-status {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }
        
        .module-item {
            padding: 8px;
            border-radius: 8px;
            font-size: 12px;
            text-align: center;
        }
        
        .module-loaded {
            background: #E8F5E9;
            color: #2E7D32;
        }
        
        .module-failed {
            background: #FFEBEE;
            color: #C62828;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-idle { background: #9E9E9E; }
        .status-running { 
            background: #4CAF50;
            animation: pulse 1.5s infinite;
        }
        .status-completed { background: #2196F3; }
        .status-error { background: #F44336; }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .log-container {
            height: 400px;
            overflow-y: auto;
            background: #f8f8f8;
            border-radius: 10px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
        }
        
        .log-entry {
            margin-bottom: 8px;
            padding: 8px;
            border-radius: 5px;
            background: white;
        }
        
        .log-INFO { border-left: 3px solid #4CAF50; }
        .log-WARNING { 
            border-left: 3px solid #FF9800;
            background: #FFF3E0;
        }
        .log-ERROR { 
            border-left: 3px solid #F44336;
            background: #FFEBEE;
        }
        .log-SUCCESS {
            border-left: 3px solid #2196F3;
            background: #E3F2FD;
            font-weight: bold;
        }
        
        .results-panel {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }
        
        .result-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: #f8f8f8;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .result-item a {
            color: #667eea;
            text-decoration: none;
        }
        
        .file-browser {
            max-height: 300px;
            overflow-y: auto;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 10px;
        }
        
        .file-item {
            padding: 8px;
            cursor: pointer;
            border-radius: 5px;
            transition: background 0.2s;
        }
        
        .file-item:hover {
            background: #f0f0f0;
        }
        
        .file-item.selected {
            background: #E3F2FD;
            border: 1px solid #2196F3;
        }
        
        .history-item {
            padding: 15px;
            background: #f8f8f8;
            border-radius: 10px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .history-item:hover {
            background: #e0e0e0;
            transform: translateX(5px);
        }
        
        .preset-item {
            padding: 12px;
            background: #f8f8f8;
            border-radius: 8px;
            margin-bottom: 10px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .preset-item:hover {
            background: #e0e0e0;
        }
        
        .advanced-settings {
            background: #f8f8f8;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
        }
        
        .setting-row {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .setting-row label {
            flex: 1;
            margin-bottom: 0;
        }
        
        .setting-row input[type="checkbox"] {
            width: auto;
            margin-left: 10px;
        }
        
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .quick-action-btn {
            padding: 10px;
            background: #f5f5f5;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
        }
        
        .quick-action-btn:hover {
            background: #e0e0e0;
            border-color: #667eea;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 腾讯文档智能处理系统 <span class="version-badge">v5.0 增强版</span></h1>
            <div style="background: #f0f8ff; border-left: 4px solid #1890ff; padding: 12px; margin: 20px 0; border-radius: 4px;">
                <strong>📌 使用说明：</strong><br>
                <ul style="margin: 8px 0 0 0; padding-left: 20px;">
                    <li><strong>基线文档</strong>：选择上周或更早的版本作为对比基准</li>
                    <li><strong>目标文档</strong>：选择当前最新版本进行变更检测</li>
                    <li><strong>重要</strong>：两个URL必须不同，否则无法检测到变更</li>
                </ul>
            </div>
            <p>完整集成测试 - 从下载到上传的全自动化流程</p>
        </div>
        
        <div class="main-content">
            <!-- 左侧面板：输入配置 -->
            <div class="panel">
                <h2>📥 输入配置</h2>
                
                <div class="tabs">
                    <button class="tab active" onclick="switchTab('basic')">基础配置</button>
                    <button class="tab" onclick="switchTab('advanced')">高级选项</button>
                    <button class="tab" onclick="switchTab('presets')">预设模板</button>
                </div>
                
                <!-- 基础配置 -->
                <div id="basic-tab" class="tab-content active">
                    <div class="form-group">
                        <label>基线文档链接 <span style="color: #666; font-size: 12px;">(上周或更早版本)</span></label>
                        <input type="text" id="baselineUrl" placeholder="https://docs.qq.com/sheet/xxx (旧版本)">
                        <button class="btn-secondary" style="margin-top: 5px; padding: 5px;" onclick="browseFiles('baseline')">
                            选择已下载文件
                        </button>
                    </div>
                    
                    <div class="form-group">
                        <label>目标文档链接 <span style="color: #666; font-size: 12px;">(当前最新版本)</span></label>
                        <input type="text" id="targetUrl" placeholder="https://docs.qq.com/sheet/xxx (新版本)">
                        <button class="btn-secondary" style="margin-top: 5px; padding: 5px;" onclick="browseFiles('target')">
                            选择已下载文件
                        </button>
                    </div>
                    
                    <div class="form-group">
                        <label>Cookie（用于下载和上传）</label>
                        <textarea id="cookie" rows="4" placeholder="输入完整的Cookie字符串"></textarea>
                        <div style="margin-top: 5px;">
                            <button class="btn-secondary" style="padding: 5px; margin-right: 10px; background: #28a745;" onclick="saveCookieToServer()">
                                💾 保存Cookie到服务器
                            </button>
                            <button class="btn-secondary" style="padding: 5px; margin-right: 10px; background: #17a2b8;" onclick="loadCookieFromServer()">
                                📥 从服务器加载Cookie
                            </button>
                            <button class="btn-secondary" style="padding: 5px; margin-right: 10px;" onclick="loadSavedCookie()">
                                加载本地Cookie
                            </button>
                            <button class="btn-secondary" style="padding: 5px; background: #ff6b6b;" onclick="clearSavedData()">
                                清除保存的数据
                            </button>
                        </div>
                    </div>
                    
                    <button class="btn" id="startBtn" onclick="startWorkflow()">
                        开始执行完整流程
                    </button>
                </div>
                
                <!-- 高级选项 -->
                <div id="advanced-tab" class="tab-content">
                    <div class="advanced-settings">
                        <div class="setting-row">
                            <label>上传方式</label>
                            <select id="uploadOption">
                                <option value="new">创建新文档</option>
                                <option value="replace">替换现有文档</option>
                            </select>
                        </div>
                        
                        <div class="setting-row">
                            <label>目标文档URL（替换模式）</label>
                            <input type="text" id="uploadTargetUrl" placeholder="留空则创建新文档">
                        </div>
                        
                        <div class="setting-row">
                            <label>启用详细日志</label>
                            <input type="checkbox" id="verboseLogging">
                        </div>
                        
                        <div class="setting-row">
                            <label>强制下载新文件（不使用本地缓存）</label>
                            <input type="checkbox" id="forceDownload" checked>
                        </div>
                        
                        <div class="setting-row">
                            <label>保存执行配置为预设</label>
                            <input type="checkbox" id="saveAsPreset">
                        </div>
                        
                        <div class="form-group" id="presetNameGroup" style="display: none;">
                            <label>预设名称</label>
                            <input type="text" id="presetName" placeholder="输入预设名称">
                        </div>
                    </div>
                </div>
                
                <!-- 预设模板 -->
                <div id="presets-tab" class="tab-content">
                    <div class="quick-actions">
                        <div class="quick-action-btn" onclick="loadPreset('weekly_check')">
                            📅 周度检查
                        </div>
                        <div class="quick-action-btn" onclick="loadPreset('emergency_check')">
                            🚨 紧急检查
                        </div>
                        <div class="quick-action-btn" onclick="loadPreset('full_analysis')">
                            📊 完整分析
                        </div>
                        <div class="quick-action-btn" onclick="loadPreset('quick_test')">
                            ⚡ 快速测试
                        </div>
                    </div>
                    
                    <div id="presetsList"></div>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" id="progressBar" style="width: 0%">
                        0%
                    </div>
                </div>
                
                <div class="modules-status" id="modulesStatus"></div>
            </div>
            
            <!-- 中间面板：执行状态和日志 -->
            <div class="panel">
                <h2>📊 执行状态</h2>
                
                <div style="margin-bottom: 15px;">
                    <span class="status-indicator status-idle" id="statusIndicator"></span>
                    <span id="statusText">等待开始</span>
                    <span style="float: right;" id="currentTask"></span>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="changedCells">0</div>
                        <div class="stat-label">变更单元格</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #FF6B6B, #FF8E53);">
                        <div class="stat-value" id="riskScore">0</div>
                        <div class="stat-label">风险分数</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #4ECDC4, #44A08D);">
                        <div class="stat-value" id="executionTime">00:00</div>
                        <div class="stat-label">执行时间</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #FA709A, #FEE140);">
                        <div class="stat-value" id="successRate">0%</div>
                        <div class="stat-label">成功率</div>
                    </div>
                </div>
                
                <div class="log-container" id="logContainer"></div>
                
                <div class="results-panel" id="resultsPanel">
                    <h3>处理结果</h3>
                    <div id="resultsContent"></div>
                </div>
            </div>
            
            <!-- 右侧面板：历史记录和文件管理 -->
            <div class="panel">
                <h2>📚 历史与文件</h2>
                
                <div class="tabs">
                    <button class="tab active" onclick="switchRightTab('history')">执行历史</button>
                    <button class="tab" onclick="switchRightTab('files')">文件管理</button>
                </div>
                
                <!-- 执行历史 -->
                <div id="history-tab" class="tab-content active">
                    <div id="historyList"></div>
                </div>
                
                <!-- 文件管理 -->
                <div id="files-tab" class="tab-content">
                    <div class="form-group">
                        <label>文件类别</label>
                        <select id="fileCategory" onchange="loadFiles()">
                            <option value="downloads">下载文件</option>
                            <option value="csv_versions">CSV版本</option>
                            <option value="comparisons">对比结果</option>
                            <option value="scores">打分文件</option>
                            <option value="excel_outputs">Excel输出</option>
                        </select>
                    </div>
                    
                    <div class="file-browser" id="fileBrowser"></div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 文件选择对话框 -->
    <div id="fileDialog" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000;">
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 20px; width: 600px; max-height: 500px;">
            <h3>选择文件</h3>
            <div class="file-browser" id="dialogFileBrowser" style="height: 300px; margin: 20px 0;"></div>
            <div style="text-align: right;">
                <button class="btn-secondary" style="width: auto; padding: 10px 20px; margin-right: 10px;" onclick="closeFileDialog()">取消</button>
                <button class="btn" style="width: auto; padding: 10px 20px;" onclick="selectFile()">选择</button>
            </div>
        </div>
    </div>
    
    <script>
        let isRunning = false;
        let statusInterval = null;
        let selectedFile = null;
        let fileDialogTarget = null;
        let executionStartTime = null;
        let timeInterval = null;
        
        // 页面加载时初始化
        window.onload = function() {
            loadModules();
            loadHistory();
            loadPresets();
            
            // 自动加载保存的URL和Cookie
            loadSavedInputs();
            
            // 监听高级设置变化
            document.getElementById('saveAsPreset').addEventListener('change', function(e) {
                document.getElementById('presetNameGroup').style.display = e.target.checked ? 'block' : 'none';
            });
            
            // 监听URL输入变化，自动保存
            document.getElementById('baselineUrl').addEventListener('change', function() {
                if (this.value) {
                    localStorage.setItem('tencent_baseline_url', this.value);
                }
            });
            
            document.getElementById('targetUrl').addEventListener('change', function() {
                if (this.value) {
                    localStorage.setItem('tencent_target_url', this.value);
                }
            });
        }
        
        // 加载保存的输入值
        function loadSavedInputs() {
            // 加载保存的URL
            const savedBaselineUrl = localStorage.getItem('tencent_baseline_url');
            const savedTargetUrl = localStorage.getItem('tencent_target_url');
            const savedCookie = localStorage.getItem('tencent_doc_cookie');
            
            if (savedBaselineUrl) {
                document.getElementById('baselineUrl').value = savedBaselineUrl;
            }
            
            if (savedTargetUrl) {
                document.getElementById('targetUrl').value = savedTargetUrl;
            }
            
            if (savedCookie) {
                document.getElementById('cookie').value = savedCookie;
            }
            
            // 如果有保存的值，显示提示
            if (savedBaselineUrl || savedTargetUrl || savedCookie) {
                console.log('已自动加载上次保存的输入');
            }
        }
        
        function loadModules() {
            fetch('/api/modules')
                .then(r => r.json())
                .then(data => {
                    displayModules(data);
                });
        }
        
        function displayModules(modules) {
            const container = document.getElementById('modulesStatus');
            container.innerHTML = '<h4 style="grid-column: 1/-1; margin-bottom: 10px;">模块加载状态</h4>';
            
            const moduleNames = {
                'downloader': '下载模块',
                'comparator': '比较模块',
                'standardizer': '标准化',
                'l2_analyzer': 'L2分析',
                'marker': '智能标记',
                'fixer': 'Excel修复',
                'uploader': '上传模块',
                'week_manager': '时间管理'
            };
            
            let loadedCount = 0;
            let totalCount = 0;
            
            for (let [key, loaded] of Object.entries(modules)) {
                totalCount++;
                if (loaded) loadedCount++;
                
                const div = document.createElement('div');
                div.className = 'module-item ' + (loaded ? 'module-loaded' : 'module-failed');
                div.innerHTML = (loaded ? '[OK] ' : '[X] ') + (moduleNames[key] || key);
                container.appendChild(div);
            }
            
            // 更新成功率
            document.getElementById('successRate').textContent = Math.round(loadedCount / totalCount * 100) + '%';
        }
        
        function switchTab(tabName) {
            // 隐藏所有标签内容
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // 移除所有标签的active类
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // 显示选中的标签
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }
        
        function switchRightTab(tabName) {
            // 右侧面板的标签切换
            const rightPanel = event.target.closest('.panel');
            rightPanel.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            rightPanel.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            rightPanel.querySelector('#' + tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
            
            if (tabName === 'files') {
                loadFiles();
            }
        }
        
        function startWorkflow() {
            if (isRunning) {
                alert('工作流正在运行中，请等待完成');
                return;
            }
            
            const baselineUrl = document.getElementById('baselineUrl').value;
            const targetUrl = document.getElementById('targetUrl').value;
            const cookie = document.getElementById('cookie').value;
            
            if (!baselineUrl || !targetUrl || !cookie) {
                alert('请填写所有必要字段');
                return;
            }
            
            // 验证URL不能相同
            if (baselineUrl === targetUrl) {
                alert('错误：基线文档和目标文档不能相同！\\n\\n' +
                      '基线文档：应选择上周或更早版本\\n' +
                      '目标文档：应选择当前最新版本\\n\\n' +
                      '请使用不同的文档URL进行对比。');
                return;
            }
            
            // 收集高级设置
            const advancedSettings = {
                upload_option: document.getElementById('uploadOption').value,
                upload_target_url: document.getElementById('uploadTargetUrl').value,
                verbose_logging: document.getElementById('verboseLogging').checked,
                force_download: document.getElementById('forceDownload').checked
            };
            
            // 如果需要保存为预设
            if (document.getElementById('saveAsPreset').checked) {
                const presetName = document.getElementById('presetName').value;
                if (presetName) {
                    savePreset(presetName, {
                        baseline_url: baselineUrl,
                        target_url: targetUrl,
                        advanced_settings: advancedSettings,
                        description: '用户自定义预设'
                    });
                }
            }
            
            isRunning = true;
            document.getElementById('startBtn').disabled = true;
            document.getElementById('logContainer').innerHTML = '';
            document.getElementById('resultsContent').innerHTML = '';
            
            // 开始计时
            executionStartTime = Date.now();
            timeInterval = setInterval(updateExecutionTime, 1000);
            
            fetch('/api/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    baseline_url: baselineUrl,
                    target_url: targetUrl,
                    cookie: cookie,
                    advanced_settings: advancedSettings
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    resetUI();
                } else {
                    // 开始轮询状态
                    statusInterval = setInterval(updateStatus, 1000);
                }
            });
        }
        
        function updateStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    // 更新进度条
                    document.getElementById('progressBar').style.width = data.progress + '%';
                    document.getElementById('progressBar').textContent = data.progress + '%';
                    
                    // 更新状态指示器
                    const indicator = document.getElementById('statusIndicator');
                    indicator.className = 'status-indicator status-' + data.status;
                    
                    // 更新状态文本
                    const statusTexts = {
                        'idle': '等待开始',
                        'running': '正在执行',
                        'completed': '执行完成',
                        'error': '执行出错'
                    };
                    document.getElementById('statusText').textContent = statusTexts[data.status] || data.status;
                    
                    // 更新当前任务
                    document.getElementById('currentTask').textContent = data.current_task || '';
                    
                    // 更新日志
                    if (data.logs && data.logs.length > 0) {
                        const container = document.getElementById('logContainer');
                        container.innerHTML = '';
                        data.logs.forEach(log => {
                            const div = document.createElement('div');
                            div.className = 'log-entry log-' + log.level;
                            div.innerHTML = `<span style="color: #666;">[${log.time}]</span> ${log.message}`;
                            container.appendChild(div);
                        });
                        container.scrollTop = container.scrollHeight;
                    }
                    
                    // 更新统计信息
                    if (data.results && data.results.statistics) {
                        const stats = data.results.statistics;
                        document.getElementById('changedCells').textContent = stats.changed_cells || 0;
                        document.getElementById('riskScore').textContent = stats.risk_score || 0;
                    }
                    
                    // 如果完成或出错，停止轮询
                    if (data.status === 'completed' || data.status === 'error') {
                        clearInterval(statusInterval);
                        clearInterval(timeInterval);
                        isRunning = false;
                        document.getElementById('startBtn').disabled = false;
                        
                        // 显示结果
                        if (data.results) {
                            displayResults(data.results);
                        }
                        
                        // 刷新历史记录
                        loadHistory();
                    }
                });
        }
        
        function updateExecutionTime() {
            if (executionStartTime) {
                const elapsed = Math.floor((Date.now() - executionStartTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                document.getElementById('executionTime').textContent = 
                    `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }
        
        function displayResults(results) {
            const container = document.getElementById('resultsContent');
            container.innerHTML = '';
            
            const files = [
                {label: '基线文件', key: 'baseline_file'},
                {label: '目标文件', key: 'target_file'},
                {label: '打分文件', key: 'score_file'},
                {label: '标记文件', key: 'marked_file'}
            ];
            
            files.forEach(file => {
                if (results[file.key]) {
                    const div = document.createElement('div');
                    div.className = 'result-item';
                    const filename = results[file.key].split('/').pop();
                    div.innerHTML = `
                        <span>${file.label}: ${filename}</span>
                        <a href="/api/download/${results[file.key]}" download>下载</a>
                    `;
                    container.appendChild(div);
                }
            });
            
            if (results.upload_url) {
                const div = document.createElement('div');
                div.className = 'result-item';
                div.innerHTML = `
                    <span>上传链接:</span>
                    <a href="${results.upload_url}" target="_blank">打开文档</a>
                `;
                container.appendChild(div);
            }
        }
        
        function resetUI() {
            isRunning = false;
            document.getElementById('startBtn').disabled = false;
            clearInterval(statusInterval);
            clearInterval(timeInterval);
        }
        
        function browseFiles(target) {
            fileDialogTarget = target;
            document.getElementById('fileDialog').style.display = 'block';
            loadDialogFiles();
        }
        
        function loadDialogFiles() {
            fetch('/api/files/downloads')
                .then(r => r.json())
                .then(files => {
                    const browser = document.getElementById('dialogFileBrowser');
                    browser.innerHTML = '';
                    
                    files.forEach(file => {
                        const div = document.createElement('div');
                        div.className = 'file-item';
                        div.onclick = () => {
                            document.querySelectorAll('.file-item').forEach(item => {
                                item.classList.remove('selected');
                            });
                            div.classList.add('selected');
                            selectedFile = file;
                        };
                        
                        const size = (file.size / 1024).toFixed(2) + ' KB';
                        const date = new Date(file.modified).toLocaleDateString();
                        
                        div.innerHTML = `
                            <div style="font-weight: 500;">${file.name}</div>
                            <div style="font-size: 12px; color: #666;">${size} | ${date}</div>
                        `;
                        
                        browser.appendChild(div);
                    });
                });
        }
        
        function selectFile() {
            if (selectedFile) {
                if (fileDialogTarget === 'baseline') {
                    document.getElementById('baselineUrl').value = selectedFile.path;
                } else if (fileDialogTarget === 'target') {
                    document.getElementById('targetUrl').value = selectedFile.path;
                }
            }
            closeFileDialog();
        }
        
        function closeFileDialog() {
            document.getElementById('fileDialog').style.display = 'none';
            selectedFile = null;
            fileDialogTarget = null;
        }
        
        function loadFiles() {
            const category = document.getElementById('fileCategory').value;
            fetch('/api/files/' + category)
                .then(r => r.json())
                .then(files => {
                    const browser = document.getElementById('fileBrowser');
                    browser.innerHTML = '';
                    
                    files.forEach(file => {
                        const div = document.createElement('div');
                        div.className = 'file-item';
                        
                        const size = (file.size / 1024).toFixed(2) + ' KB';
                        const date = new Date(file.modified).toLocaleDateString();
                        
                        div.innerHTML = `
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-weight: 500;">${file.name}</div>
                                    <div style="font-size: 12px; color: #666;">${size} | ${date}</div>
                                </div>
                                <a href="/api/download/${file.path}" download style="color: #667eea;">下载</a>
                            </div>
                        `;
                        
                        browser.appendChild(div);
                    });
                });
        }
        
        function loadHistory() {
            fetch('/api/history')
                .then(r => r.json())
                .then(history => {
                    const container = document.getElementById('historyList');
                    container.innerHTML = '';
                    
                    if (history.length === 0) {
                        container.innerHTML = '<div style="text-align: center; color: #999; padding: 20px;">暂无执行历史</div>';
                        return;
                    }
                    
                    history.forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'history-item';
                        
                        const startTime = item.start_time ? new Date(item.start_time).toLocaleString() : '未知';
                        const statusIcon = {
                            'completed': '[完成]',
                            'error': '[错误]',
                            'running': '[运行中]'
                        }[item.status] || '❓';
                        
                        div.innerHTML = `
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <strong>${statusIcon} ${item.id}</strong>
                                <span style="color: #666; font-size: 12px;">${item.status}</span>
                            </div>
                            <div style="font-size: 12px; color: #666;">${startTime}</div>
                        `;
                        
                        div.onclick = () => loadHistoryDetails(item.id);
                        container.appendChild(div);
                    });
                });
        }
        
        function loadHistoryDetails(id) {
            // 可以展开显示历史详情
            console.log('Loading history:', id);
        }
        
        function loadPresets() {
            fetch('/api/presets')
                .then(r => r.json())
                .then(presets => {
                    const container = document.getElementById('presetsList');
                    container.innerHTML = '<h4 style="margin-bottom: 10px;">自定义预设</h4>';
                    
                    if (presets.length === 0) {
                        container.innerHTML += '<div style="text-align: center; color: #999; padding: 20px;">暂无自定义预设</div>';
                        return;
                    }
                    
                    presets.forEach(preset => {
                        const div = document.createElement('div');
                        div.className = 'preset-item';
                        div.innerHTML = `
                            <div>
                                <div style="font-weight: 500;">${preset.name}</div>
                                <div style="font-size: 12px; color: #666;">${preset.description}</div>
                            </div>
                            <button class="btn-secondary" style="width: auto; padding: 5px 15px;" onclick="applyPreset('${preset.name}')">应用</button>
                        `;
                        container.appendChild(div);
                    });
                });
        }
        
        function loadPreset(presetType) {
            // 预定义的快速预设
            const presets = {
                'weekly_check': {
                    baseline_url: 'https://docs.qq.com/sheet/baseline_week',
                    target_url: 'https://docs.qq.com/sheet/target_week',
                    advanced_settings: {
                        upload_option: 'new'
                    }
                },
                'emergency_check': {
                    baseline_url: '',
                    target_url: '',
                    advanced_settings: {
                        upload_option: 'replace',
                        verbose_logging: true
                    }
                },
                'full_analysis': {
                    baseline_url: '',
                    target_url: '',
                    advanced_settings: {
                        upload_option: 'new',
                        verbose_logging: true
                    }
                },
                'quick_test': {
                    baseline_url: '',
                    target_url: '',
                    advanced_settings: {
                        upload_option: 'new'
                    }
                }
            };
            
            const preset = presets[presetType];
            if (preset) {
                if (preset.baseline_url) document.getElementById('baselineUrl').value = preset.baseline_url;
                if (preset.target_url) document.getElementById('targetUrl').value = preset.target_url;
                if (preset.advanced_settings) {
                    document.getElementById('uploadOption').value = preset.advanced_settings.upload_option || 'new';
                    document.getElementById('uploadTargetUrl').value = preset.advanced_settings.upload_target_url || '';
                    document.getElementById('verboseLogging').checked = preset.advanced_settings.verbose_logging || false;
                }
                
                // 切换到基础配置标签
                document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                document.querySelector('.tab').classList.add('active');
                document.getElementById('basic-tab').classList.add('active');
            }
        }
        
        function applyPreset(name) {
            fetch('/api/presets/' + name)
                .then(r => r.json())
                .then(preset => {
                    if (preset.baseline_url) document.getElementById('baselineUrl').value = preset.baseline_url;
                    if (preset.target_url) document.getElementById('targetUrl').value = preset.target_url;
                    if (preset.cookie) document.getElementById('cookie').value = preset.cookie;
                    if (preset.advanced_settings) {
                        document.getElementById('uploadOption').value = preset.advanced_settings.upload_option || 'new';
                        document.getElementById('uploadTargetUrl').value = preset.advanced_settings.upload_target_url || '';
                        document.getElementById('verboseLogging').checked = preset.advanced_settings.verbose_logging || false;
                    }
                    
                    // 切换到基础配置标签
                    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                    document.querySelector('.tab').classList.add('active');
                    document.getElementById('basic-tab').classList.add('active');
                });
        }
        
        function savePreset(name, config) {
            fetch('/api/presets', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name,
                    config: config
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.message) {
                    loadPresets();
                }
            });
        }
        
        function saveCookieToServer() {
            const cookie = document.getElementById('cookie').value.trim();
            
            if (!cookie) {
                alert('请先输入Cookie');
                return;
            }
            
            fetch('/api/save-cookie', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ cookie: cookie })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(`✅ Cookie已成功保存到服务器！\n保存了 ${data.cookie_count} 个Cookie字段\n更新时间: ${data.last_updated}`);
                    // 同时保存到本地存储
                    localStorage.setItem('tencent_doc_cookie', cookie);
                } else {
                    alert('❌ 保存失败: ' + (data.error || '未知错误'));
                }
            })
            .catch(error => {
                alert('❌ 保存Cookie时出错: ' + error);
            });
        }
        
        function loadCookieFromServer() {
            fetch('/api/load-cookie')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('cookie').value = data.cookie;
                    // 同时保存到本地存储
                    localStorage.setItem('tencent_doc_cookie', data.cookie);
                    alert(`✅ Cookie加载成功！\n包含 ${data.cookie_count} 个Cookie字段\n最后更新: ${data.last_updated}`);
                } else {
                    alert('❌ 加载失败: ' + (data.error || '未找到Cookie配置文件'));
                }
            })
            .catch(error => {
                alert('❌ 加载Cookie时出错: ' + error);
            });
        }
        
        function loadSavedCookie() {
            // 尝试从本地存储加载Cookie
            const savedCookie = localStorage.getItem('tencent_doc_cookie');
            if (savedCookie) {
                document.getElementById('cookie').value = savedCookie;
                alert('Cookie加载成功（从浏览器本地存储）');
            } else {
                alert('没有保存的Cookie');
            }
        }
        
        function clearSavedData() {
            if (confirm('确定要清除所有保存的URL和Cookie吗？')) {
                // 清除localStorage中的所有相关数据
                localStorage.removeItem('tencent_baseline_url');
                localStorage.removeItem('tencent_target_url');
                localStorage.removeItem('tencent_doc_cookie');
                
                // 清空输入框
                document.getElementById('baselineUrl').value = '';
                document.getElementById('targetUrl').value = '';
                document.getElementById('cookie').value = '';
                
                alert('已清除所有保存的数据');
            }
        }
        
        // 保存Cookie到本地存储
        document.getElementById('cookie').addEventListener('change', function() {
            if (this.value) {
                localStorage.setItem('tencent_doc_cookie', this.value);
            }
        });
    </script>
</body>
</html>
'''

# ==================== 主程序入口 ====================
if __name__ == '__main__':
    logger.info("="*60)
    logger.info("腾讯文档智能处理系统 - 完整集成测试（增强版）")
    logger.info(f"访问: http://localhost:8093")
    logger.info("="*60)
    
    # 尝试多个端口
    ports = [8093, 8094, 8095, 8096, 8097, 8098, 8099, 8100, 8101, 8102]
    
    for port in ports:
        try:
            app.run(host='0.0.0.0', port=port, debug=False)
            break
        except OSError as e:
            if "Address already in use" in str(e):
                logger.warning(f"端口 {port} 已被占用，尝试下一个...")
                continue
            else:
                raise
    else:
        logger.error("所有端口都被占用，无法启动服务")