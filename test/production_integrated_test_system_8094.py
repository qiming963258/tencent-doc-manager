#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档管理项目 - 生产环境集成测试系统
端口: 8094
版本: 3.0.0 - Production Integrated
功能: 完全按照项目正式流程运行，集成所有生产环境组件
作者: 系统架构团队
日期: 2025-09-03
"""

from flask import Flask, render_template_string, request, jsonify, send_file, redirect, url_for
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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import csv
# pandas是可选的，如果不存在则使用标准库
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    logger = None  # 将在后面初始化
from dataclasses import dataclass, asdict
from queue import Queue
import requests
import subprocess
import tempfile

# 添加项目路径 - 使用项目正式路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/core_modules')
sys.path.insert(0, '/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

# 导入分享链接解析器和文件命名服务
try:
    from production.core_modules.share_link_parser import ShareLinkParser, FileNamingService
    HAS_SHARE_PARSER = True
except ImportError:
    HAS_SHARE_PARSER = False

app = Flask(__name__)

# ==================== 项目正式路径配置 ====================
BASE_DIR = Path('/root/projects/tencent-doc-manager')
# 使用项目正式配置文件
CONFIG_PATH = BASE_DIR / 'config.json'
BACKUP_CONFIG_PATH = BASE_DIR / 'auto_download_config.json'

# 使用项目正式目录结构
DOWNLOAD_DIR = BASE_DIR / 'downloads'  # 项目正式下载目录
COMPARISON_BASELINE_DIR = BASE_DIR / 'comparison_baseline'
COMPARISON_TARGET_DIR = BASE_DIR / 'comparison_target'
COMPARISON_RESULTS_DIR = BASE_DIR / 'comparison_results'  # 项目正式结果目录
CSV_VERSIONS_DIR = BASE_DIR / 'csv_versions'  # 版本管理目录（符合规范）
LOG_DIR = BASE_DIR / 'logs'
TEMP_DIR = BASE_DIR / 'temp_workflow'

# 确保所有目录存在
for dir_path in [DOWNLOAD_DIR, COMPARISON_BASELINE_DIR, COMPARISON_TARGET_DIR, 
                 COMPARISON_RESULTS_DIR, CSV_VERSIONS_DIR, LOG_DIR, TEMP_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)

# ==================== 日志配置 ====================
log_file = LOG_DIR / f'production_test_system_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 动态导入项目正式模块 ====================
MODULES_STATUS = {
    'production_downloader': False,
    'adaptive_comparator': False,
    'cookie_manager': False,
    'simple_comparison': False,
    'post_processor': False,
    'tencent_exporter': False
}

# 导入项目核心模块
try:
    from production.core_modules.adaptive_table_comparator import AdaptiveTableComparator
    MODULES_STATUS['adaptive_comparator'] = True
    logger.info("✅ 成功导入 adaptive_table_comparator")
except ImportError as e:
    logger.warning(f"⚠️ 无法导入 adaptive_table_comparator: {e}")

try:
    from simple_comparison_handler import simple_csv_compare, save_comparison_result
    MODULES_STATUS['simple_comparison'] = True
    logger.info("✅ 成功导入 simple_comparison_handler")
except ImportError as e:
    logger.warning(f"⚠️ 无法导入 simple_comparison_handler: {e}")

try:
    from post_download_processor import PostDownloadProcessor
    MODULES_STATUS['post_processor'] = True
    logger.info("✅ 成功导入 post_download_processor")
except ImportError as e:
    logger.warning(f"⚠️ 无法导入 post_download_processor: {e}")

try:
    from production.core_modules.tencent_export_automation import TencentDocAutoExporter
    MODULES_STATUS['tencent_exporter'] = True
    logger.info("✅ 成功导入 tencent_export_automation")
except ImportError:
    try:
        from tencent_export_automation import TencentDocAutoExporter
        MODULES_STATUS['tencent_exporter'] = True
        logger.info("✅ 成功导入 tencent_export_automation (fallback)")
    except ImportError as e:
        logger.warning(f"⚠️ 无法导入 tencent_export_automation: {e}")

# ==================== 配置管理器 ====================
class ProductionConfigManager:
    """项目正式配置管理器"""
    
    def __init__(self):
        self.config_path = CONFIG_PATH
        self.backup_config_path = BACKUP_CONFIG_PATH
        self.config_cache = {}
        self.last_modified = 0
    
    def load_config(self) -> Dict[str, Any]:
        """加载项目正式配置"""
        try:
            if self.config_path.exists():
                config_stat = os.stat(self.config_path)
                if config_stat.st_mtime > self.last_modified:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        self.config_cache = json.load(f)
                    self.last_modified = config_stat.st_mtime
                    logger.info("✅ 从主配置文件加载配置")
                return self.config_cache.copy()
            
            elif self.backup_config_path.exists():
                with open(self.backup_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("✅ 从备用配置文件加载配置")
                return config
            
            else:
                logger.warning("⚠️ 未找到配置文件，返回默认配置")
                return self._get_default_config()
                
        except Exception as e:
            logger.error(f"❌ 配置加载失败: {e}")
            return self._get_default_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到项目正式配置文件"""
        try:
            # 同时更新主配置和备用配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 更新备用配置文件的结构
            backup_config = {
                "cookie": config.get("cookie", ""),
                "urls": config.get("urls", []),
                "format": config.get("format", "csv"),
                "interval": config.get("interval", 30),
                "download_dir": str(DOWNLOAD_DIR),
                "enable_version_management": config.get("enable_version_management", True),
                "enable_comparison": config.get("enable_comparison", True),
                "enable_heatmap": config.get("enable_heatmap", True),
                "enable_excel": config.get("enable_excel", True)
            }
            
            with open(self.backup_config_path, 'w', encoding='utf-8') as f:
                json.dump(backup_config, f, ensure_ascii=False, indent=2)
            
            self.config_cache = config.copy()
            self.last_modified = time.time()
            logger.info("✅ 配置保存成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置保存失败: {e}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "cookie": "",
            "urls": [],
            "format": "csv",
            "interval": 30,
            "download_dir": str(DOWNLOAD_DIR),
            "comparison_results_dir": str(COMPARISON_RESULTS_DIR),
            "enable_version_management": True,
            "enable_comparison": True,
            "enable_heatmap": False,
            "enable_excel": True
        }

# 初始化配置管理器
config_manager = ProductionConfigManager()

# ==================== 生产环境下载器 ====================
class ProductionDocumentDownloader:
    """项目正式文档下载器"""
    
    def __init__(self):
        self.exporter = None
        self.download_dir = DOWNLOAD_DIR
        self.download_history = []
    
    def download_document(self, url: str, cookie: str, format_type: str = "csv") -> Tuple[bool, str, str]:
        """
        使用项目正式流程下载文档 - 与8093相同的同步方法
        
        Returns:
            (success, filepath, error_message)
        """
        try:
            # 不再检查和初始化exporter，直接使用8093的方法
            
            # 重要修复：直接使用8093成功的方法 - 通过auto_download_ui_system的适配器
            # 这个适配器正确处理了异步转同步
            from auto_download_ui_system import download_file_from_url
            
            # 只有当cookie不为空时才保存到配置文件
            if cookie:
                config_file = BASE_DIR / 'config.json'
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump({'cookie': cookie}, f, ensure_ascii=False, indent=2)
            
            # 使用与8093完全相同的调用方式
            logger.info(f"📥 开始下载: {url[:100]}{'...' if len(url) > 100 else ''}")
            result = download_file_from_url(url, format_type)
            success = result and result.get('success', False)
            
            if success:
                # 从结果中获取文件路径
                file_path = result.get('file_path')
                
                # 如果file_path为空，尝试从files列表中获取
                if not file_path:
                    files = result.get('files', [])
                    if files:
                        # files可能是字典列表或字符串列表
                        first_file = files[0]
                        if isinstance(first_file, dict):
                            file_path = first_file.get('path')
                        else:
                            file_path = first_file
                        logger.info(f"📁 从files列表提取路径: {file_path}")
                
                if file_path and os.path.exists(file_path):
                    logger.info(f"✅ 文档下载成功: {file_path}")
                    return True, str(file_path), ""
                else:
                    # 不使用备用策略，直接报错
                    logger.error(f"❌ 文件路径无效或不存在: {file_path}")
                    logger.error(f"📊 完整结果信息: {result}")
                    return False, "", f"下载失败：文件路径无效 - {file_path}"
            else:
                error_msg = result.get('error', '下载失败')
                return False, "", error_msg
                
        except Exception as e:
            logger.error(f"❌ 下载过程出错: {e}")
            return False, "", str(e)
    
    async def cleanup(self):
        """清理资源"""
        if self.exporter:
            await self.exporter.cleanup()
            self.exporter = None

# ==================== 智能文件选择器 ====================
class SmartFileSelector:
    """智能文件选择器 - 优先真实文档"""
    
    @staticmethod
    def categorize_files(files: List[str]) -> Dict[str, List[str]]:
        """智能文件分类"""
        real_docs = []
        test_docs = []
        
        test_keywords = ['test', '测试', 'demo', 'sample', 'temp', '临时', 'example']
        
        for file_path in files:
            basename = os.path.basename(file_path).lower()
            is_test = any(keyword in basename for keyword in test_keywords)
            
            if is_test:
                test_docs.append(file_path)
            else:
                real_docs.append(file_path)
        
        return {
            'real_docs': real_docs,
            'test_docs': test_docs,
            'total': len(files)
        }
    
    @staticmethod
    def select_best_file(files: List[str], prefer_real: bool = True) -> Tuple[str, str]:
        """
        从文件列表中选择最佳文件
        
        Returns:
            (selected_file, selection_reason)
        """
        if not files:
            return None, "文件列表为空"
        
        categorized = SmartFileSelector.categorize_files(files)
        
        if prefer_real and categorized['real_docs']:
            selected = categorized['real_docs'][0]
            reason = f"选择真实文档 ({len(categorized['real_docs'])}个真实文档可选)"
            logger.info(f"✅ {reason}: {os.path.basename(selected)}")
            return selected, reason
        
        elif categorized['test_docs']:
            selected = categorized['test_docs'][0] 
            reason = f"选择测试文档 ({len(categorized['test_docs'])}个测试文档可选)"
            if prefer_real:
                logger.warning(f"⚠️ {reason}: {os.path.basename(selected)}")
            else:
                logger.info(f"📋 {reason}: {os.path.basename(selected)}")
            return selected, reason
        
        else:
            # 如果分类失败，选择第一个
            selected = files[0]
            reason = "默认选择第一个文件"
            logger.info(f"📋 {reason}: {os.path.basename(selected)}")
            return selected, reason

# ==================== 生产环境对比器 ====================
class ProductionCSVComparator:
    """项目正式CSV对比器 - 统一标准版"""
    
    def __init__(self):
        # 只使用统一的对比接口
        try:
            from unified_csv_comparator import UnifiedCSVComparator
            self.comparator = UnifiedCSVComparator()
            logger.info("✅ 成功初始化 UnifiedCSVComparator（唯一标准）")
        except ImportError as e:
            logger.error(f"❌ 无法导入 UnifiedCSVComparator: {e}")
            # 降级到简化版
            try:
                from simplified_csv_comparator import SimplifiedCSVComparator
                self.comparator = SimplifiedCSVComparator()
                logger.warning("⚠️ 降级使用 SimplifiedCSVComparator")
            except ImportError:
                self.comparator = None
                logger.error("❌ 对比器初始化失败")
        
        # 添加文件选择器
        self.file_selector = SmartFileSelector()
    
    def compare_files(self, baseline_path: str, target_path: str) -> Dict[str, Any]:
        """
        使用项目统一对比标准
        
        Args:
            baseline_path: 基线文件路径
            target_path: 目标文件路径
            
        Returns:
            对比结果字典（简化格式）
        """
        try:
            if not self.comparator:
                return {
                    'error': '对比器未初始化',
                    'success': False,
                    'total_changes': 0,
                    'similarity_score': 0,
                    'details': {}
                }
            
            logger.info("🔍 使用 UnifiedCSVComparator 进行对比（项目唯一标准）")
            
            # 执行对比
            result = self.comparator.compare(baseline_path, target_path)
            
            # 确保返回格式兼容
            if 'statistics' in result:
                result['total_changes'] = result['statistics'].get('total_modifications', 0)
                result['similarity_score'] = result['statistics'].get('similarity', 0)
            
            if 'success' not in result:
                result['success'] = True
            
            return result
                
        except Exception as e:
            logger.error(f"❌ 文件对比失败: {e}")
            return {
                'error': str(e),
                'success': False,
                'total_changes': 0,
                'similarity_score': 0,
                'details': {}
            }
    
    def _adaptive_compare(self, baseline_path: str, target_path: str) -> Dict[str, Any]:
        """使用自适应对比器 - 增强日志版本"""
        try:
            logger.info("🔬 启动AdaptiveTableComparator高级对比算法...")
            
            # 检查pandas依赖
            if not HAS_PANDAS:
                logger.warning("⚠️ Pandas库不可用，自动降级至SimpleComparison")
                logger.info("📋 降级原因: 缺少pandas依赖，无法使用DataFrame高级功能")
                return self._simple_compare(baseline_path, target_path)
            
            logger.info("✅ Pandas依赖检查通过，开始读取CSV文件...")
            
            # 文件读取和预处理
            read_start_time = time.time()
            try:
                baseline_df = pd.read_csv(baseline_path, encoding='utf-8')
                target_df = pd.read_csv(target_path, encoding='utf-8')
                read_duration = time.time() - read_start_time
                
                logger.info(f"📊 文件读取完成 (耗时: {read_duration:.2f}秒)")
                logger.info(f"   📄 基线文件: {os.path.basename(baseline_path)}")
                logger.info(f"      数据形状: {baseline_df.shape} (行×列)")
                logger.info(f"      内存占用: {baseline_df.memory_usage(deep=True).sum() / 1024:.1f} KB")
                logger.info(f"   📄 目标文件: {os.path.basename(target_path)}")
                logger.info(f"      数据形状: {target_df.shape} (行×列)")
                logger.info(f"      内存占用: {target_df.memory_usage(deep=True).sum() / 1024:.1f} KB")
                
            except Exception as read_error:
                logger.error(f"❌ CSV文件读取失败: {read_error}")
                logger.error("🔄 尝试使用简单对比器作为备选...")
                return self._simple_compare(baseline_path, target_path)
            
            # 数据质量检查
            logger.info("🔍 执行数据质量检查...")
            
            # 检查1: 相同文件路径
            if baseline_path == target_path:
                logger.warning("⚠️ 检测到相同文件路径!")
                logger.warning("   这可能表示下载过程中的问题")
                return {
                    'error': '基线文件和目标文件路径相同，可能是下载模块的问题',
                    'total_changes': 0,
                    'similarity_score': 1.0,
                    'details': {
                        'issue_type': 'same_file_path',
                        'file_path': baseline_path,
                        'detection_reason': '文件路径完全相同'
                    }
                }
            
            # 检查2: 数据内容相同
            try:
                content_identical = baseline_df.equals(target_df)
                if content_identical:
                    logger.warning("⚠️ 检测到相同文件内容!")
                    logger.warning("   虽然路径不同，但数据内容完全一致")
                    logger.info("   这可能表示:")
                    logger.info("     - 数据在时间段内无变化（正常）")
                    logger.info("     - 下载了相同版本的文件（异常）")
                    return {
                        'error': '基线文件和目标文件内容完全相同',
                        'total_changes': 0,
                        'similarity_score': 1.0,
                        'details': {
                            'issue_type': 'identical_content',
                            'baseline_shape': baseline_df.shape,
                            'target_shape': target_df.shape,
                            'detection_reason': '数据内容完全相同'
                        }
                    }
            except Exception as compare_error:
                logger.warning(f"⚠️ 内容比较检查失败: {compare_error}")
                logger.info("继续执行详细对比...")
            
            # 检查3: 数据结构兼容性
            if list(baseline_df.columns) != list(target_df.columns):
                logger.warning("⚠️ 检测到列结构不匹配!")
                logger.info(f"   基线文件列: {list(baseline_df.columns)}")
                logger.info(f"   目标文件列: {list(target_df.columns)}")
                logger.info("   对比器将尝试智能匹配...")
            
            logger.info("✅ 数据质量检查完成，开始执行高级对比算法...")
            
            # 执行自适应对比
            comparison_start = time.time()
            try:
                # This branch should not be reached anymore
                comparison_result = None
                comparison_duration = time.time() - comparison_start
                
                logger.info(f"🎯 高级对比算法执行完成 (耗时: {comparison_duration:.2f}秒)")
                logger.info(f"   总变更数: {comparison_result.get('total_changes', 0)}")
                logger.info(f"   相似度: {(comparison_result.get('similarity_score', 0) * 100):.2f}%")
                logger.info(f"   算法类型: AdaptiveTableComparator")
                
                return comparison_result
                
            except Exception as comp_error:
                logger.error(f"❌ 自适应对比算法执行失败: {comp_error}")
                logger.info("🔄 降级使用简单对比算法...")
                return self._simple_compare(baseline_path, target_path)
            
        except Exception as e:
            logger.error(f"❌ 自适应对比器总体异常: {e}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.info("🔄 最终降级至简单对比算法...")
            return self._simple_compare(baseline_path, target_path)
    
    def _simple_compare(self, baseline_path: str, target_path: str) -> Dict[str, Any]:
        """使用简单对比器 - 增强日志版本"""
        logger.info("🔧 启动SimpleComparison标准对比算法...")
        
        # 检查模块可用性
        if not MODULES_STATUS['simple_comparison']:
            logger.error("❌ SimpleComparison模块不可用!")
            logger.error("   缺少simple_comparison_handler模块")
            return {
                'error': '对比模块不可用',
                'total_changes': 0,
                'similarity_score': 0,
                'details': {
                    'issue_type': 'module_unavailable',
                    'missing_module': 'simple_comparison_handler'
                }
            }
        
        logger.info("✅ SimpleComparison模块检查通过")
        
        # 文件基本信息记录
        try:
            baseline_size = os.path.getsize(baseline_path)
            target_size = os.path.getsize(target_path)
            
            logger.info("📋 文件信息统计:")
            logger.info(f"   📄 基线文件: {os.path.basename(baseline_path)} ({baseline_size/1024:.1f} KB)")
            logger.info(f"   📄 目标文件: {os.path.basename(target_path)} ({target_size/1024:.1f} KB)")
            
        except Exception as size_error:
            logger.warning(f"⚠️ 文件大小获取失败: {size_error}")
        
        # 执行简单对比
        try:
            comparison_start = time.time()
            logger.info("⚙️ 开始执行SimpleCSVCompare算法...")
            
            result = simple_csv_compare(baseline_path, target_path)
            comparison_duration = time.time() - comparison_start
            
            logger.info(f"🎯 标准对比算法执行完成 (耗时: {comparison_duration:.2f}秒)")
            logger.info(f"   总变更数: {result.get('total_changes', 0)}")
            logger.info(f"   相似度: {(result.get('similarity_score', 0) * 100):.2f}%")
            logger.info(f"   算法类型: SimpleComparison")
            
            # 为结果添加执行时间信息
            if isinstance(result, dict):
                result['execution_time'] = comparison_duration
                result['comparison_method'] = 'UnifiedCSVComparator'
            
            return result
            
        except Exception as comp_error:
            logger.error(f"❌ 简单对比算法执行失败: {comp_error}")
            logger.error(f"异常类型: {type(comp_error).__name__}")
            
            # 返回错误但保持系统稳定
            return {
                'error': f'简单对比执行失败: {str(comp_error)}',
                'total_changes': 0,
                'similarity_score': 0,
                'details': {
                    'issue_type': 'comparison_execution_failed',
                    'error_type': type(comp_error).__name__,
                    'baseline_file': os.path.basename(baseline_path),
                    'target_file': os.path.basename(target_path)
                }
            }
    
    def save_result(self, result: Dict[str, Any]) -> str:
        """保存对比结果到项目正式目录"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 尝试从结果元数据中提取文档名称
        baseline_doc_name = None
        target_doc_name = None
        
        if 'metadata' in result:
            baseline_doc_name = result['metadata'].get('baseline_doc_name')
            target_doc_name = result['metadata'].get('target_doc_name')
            logger.info(f"📋 从metadata提取文档名: baseline={baseline_doc_name}, target={target_doc_name}")
        else:
            logger.warning("⚠️ 结果中没有metadata")
        
        # 如果有文档名称且有FileNamingService，使用语义化命名
        if HAS_SHARE_PARSER and baseline_doc_name and target_doc_name:
            try:
                naming_service = FileNamingService()
                filename = naming_service.generate_comparison_filename(
                    baseline_doc_name,
                    target_doc_name,
                    timestamp
                )
                result_file = COMPARISON_RESULTS_DIR / filename
                logger.info(f"✅ 使用语义化命名: {filename}")
            except Exception as e:
                # 回退到默认命名
                logger.warning(f"⚠️ 语义化命名失败，使用默认命名: {e}")
                result_file = COMPARISON_RESULTS_DIR / f"simplified_comparison_{timestamp}.json"
        else:
            # 使用默认命名
            reasons = []
            if not HAS_SHARE_PARSER:
                reasons.append("ShareLinkParser未导入")
            if not baseline_doc_name:
                reasons.append("基线文档名为空")
            if not target_doc_name:
                reasons.append("目标文档名为空")
            logger.info(f"ℹ️ 使用默认命名，原因: {', '.join(reasons)}")
            result_file = COMPARISON_RESULTS_DIR / f"simplified_comparison_{timestamp}.json"
        
        try:
            # 更新元数据（保留已有的metadata，而不是覆盖）
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata'].update({
                'timestamp': timestamp,
                'system_version': '3.0.0',
                'comparison_method': 'UnifiedCSVComparator'
            })
            
            if MODULES_STATUS['simple_comparison']:
                success = save_comparison_result(result, str(result_file))
                if success:
                    logger.info(f"✅ 对比结果已保存: {result_file}")
                    return str(result_file)
            
            # 备用保存方法
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 对比结果已保存: {result_file}")
            return str(result_file)
            
        except Exception as e:
            logger.error(f"❌ 保存对比结果失败: {e}")
            return ""

# ==================== 全局状态管理 ====================
@dataclass
class SystemStatus:
    """系统状态"""
    is_busy: bool = False
    current_task: str = ""
    last_operation: str = ""
    operation_count: int = 0
    error_count: int = 0
    start_time: datetime = None
    last_config_update: datetime = None

# 全局状态
system_status = SystemStatus()
downloader = ProductionDocumentDownloader()
comparator = ProductionCSVComparator()

# ==================== HTML模板 ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档管理系统 - 智能CSV对比平台 v4.0 - 规范化版本</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        
        .header .version {
            font-size: 0.9rem;
            opacity: 0.8;
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 15px;
            display: inline-block;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.4rem;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e1e1;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-group textarea {
            height: 100px;
            resize: vertical;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
            margin-bottom: 10px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.6;
            transform: none;
            cursor: not-allowed;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online { background-color: #28a745; }
        .status-offline { background-color: #dc3545; }
        .status-warning { background-color: #ffc107; }
        
        .module-status {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .module-item {
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
        }
        
        .module-available {
            background-color: #d4edda;
            color: #155724;
        }
        
        .module-unavailable {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        .log-container {
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            height: 300px;
            overflow-y: auto;
            margin-bottom: 15px;
        }
        
        .path-info {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .path-info h4 {
            color: #495057;
            margin-bottom: 10px;
        }
        
        .path-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 5px 0;
            border-bottom: 1px solid #e9ecef;
        }
        
        .path-item:last-child {
            border-bottom: none;
        }
        
        .path-label {
            font-weight: 500;
            color: #6c757d;
        }
        
        .path-value {
            font-family: monospace;
            color: #495057;
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        .comparison-result {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .result-metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        
        .result-metric .label {
            font-weight: 500;
        }
        
        .result-metric .value {
            color: #007bff;
            font-weight: bold;
        }
        
        .full-width {
            grid-column: span 3;
        }
        
        .two-thirds {
            grid-column: span 2;
        }
        
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            color: #e74c3c;
        }
        
        table {
            border-spacing: 0;
        }
        
        table th {
            font-weight: 600;
        }
        
        table td, table th {
            border-bottom: 1px solid #dee2e6;
        }
        
        table tbody tr:hover {
            background-color: #f8f9fa !important;
        }
        
        @media (max-width: 1200px) {
            .main-grid {
                grid-template-columns: 1fr 1fr;
            }
            .full-width {
                grid-column: span 2;
            }
            .two-thirds {
                grid-column: span 2;
            }
        }
        
        @media (max-width: 768px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
            .full-width, .two-thirds {
                grid-column: span 1;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 标题区域 -->
        <div class="header">
            <h1>📊 腾讯文档智能CSV对比系统</h1>
            <div class="subtitle">规范化工作流程与自动对比平台</div>
            <div class="version">Version 4.0.0 - 端口: 8094 | 遵循CSV对比规范 v1.0</div>
        </div>
        
        <!-- 系统规范概览 -->
        <div class="card full-width" style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); margin-bottom: 20px;">
            <h2 style="color: #2c3e50; border-bottom: 3px solid #3498db;">🔬 系统核心规范与工作流程</h2>
            
            <!-- 时间规则表 -->
            <div style="margin: 20px 0;">
                <h3 style="color: #34495e; margin-bottom: 15px;">⏰ 时间节点规则</h3>
                <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
                    <thead>
                        <tr style="background: #3498db; color: white;">
                            <th style="padding: 12px; text-align: left;">时间段</th>
                            <th style="padding: 12px; text-align: left;">定义</th>
                            <th style="padding: 12px; text-align: left;">文件存储规则</th>
                            <th style="padding: 12px; text-align: left;">查找策略</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="background: #ecf0f1;">
                            <td style="padding: 10px; font-weight: bold;">周二基线时间</td>
                            <td style="padding: 10px;">周二 12:00-13:00</td>
                            <td style="padding: 10px; color: #e74c3c;">→ baseline文件夹 (单文件规则)</td>
                            <td style="padding: 10px;">作为基准对比文件</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold;">周中工作时间</td>
                            <td style="padding: 10px;">周二 13:01 - 周五 23:59</td>
                            <td style="padding: 10px; color: #27ae60;">→ midweek文件夹</td>
                            <td style="padding: 10px;">作为目标对比文件</td>
                        </tr>
                        <tr style="background: #ecf0f1;">
                            <td style="padding: 10px; font-weight: bold;">周末时间</td>
                            <td style="padding: 10px;">周六 00:00 - 周日 23:59</td>
                            <td style="padding: 10px; color: #9b59b6;">→ weekend文件夹</td>
                            <td style="padding: 10px;">作为周末版本文件</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold;">新周开始</td>
                            <td style="padding: 10px;">周一 00:00 - 周二 11:59</td>
                            <td style="padding: 10px; color: #3498db;">使用上周数据</td>
                            <td style="padding: 10px;">查找上周W[N-1]文件</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- 文件存储规范 -->
            <div style="margin: 20px 0;">
                <h3 style="color: #34495e; margin-bottom: 15px;">📁 文件存储规范路径</h3>
                <div style="background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 8px; font-family: monospace;">
                    <div style="margin-bottom: 10px;">
                        <strong style="color: #3498db;">根目录:</strong> /root/projects/tencent-doc-manager/csv_versions/
                    </div>
                    <div style="margin-left: 20px; line-height: 1.8;">
                        <div>├── 2025_W36/  <span style="color: #95a5a6;">← 周编号文件夹 (年份_W周号)</span></div>
                        <div>│   ├── baseline/  <span style="color: #e74c3c;">← 基线文件 (仅1个文件，自动清理旧文件)</span></div>
                        <div>│   ├── midweek/   <span style="color: #27ae60;">← 周中文件 (可多个)</span></div>
                        <div>│   └── weekend/   <span style="color: #9b59b6;">← 周末文件 (可多个)</span></div>
                        <div>└── 2025_W37/</div>
                    </div>
                    <div style="margin-top: 15px; padding: 10px; background: rgba(231, 76, 60, 0.2); border-radius: 5px;">
                        <strong>🔒 基线文件夹单文件规则:</strong> baseline文件夹内只保留最新的一个文件，新文件保存时自动删除旧文件
                    </div>
                </div>
            </div>
            
            <!-- 核心程序文件 -->
            <div style="margin: 20px 0;">
                <h3 style="color: #34495e; margin-bottom: 15px;">⚙️ 核心程序文件与功能</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db;">
                        <h4 style="color: #2c3e50; margin-bottom: 10px;">下载与存储模块</h4>
                        <ul style="list-style: none; padding: 0;">
                            <li style="padding: 5px 0;">📄 <code>tencent_export_automation.py</code></li>
                            <li style="padding-left: 20px; color: #7f8c8d;">• determine_version_type() - 判断文件版本类型</li>
                            <li style="padding-left: 20px; color: #7f8c8d;">• 基线单文件规则实现 (165-177行)</li>
                            <li style="padding: 5px 0;">📄 <code>week_version_manager.py</code></li>
                            <li style="padding-left: 20px; color: #7f8c8d;">• get_current_week_info() - 获取周信息</li>
                        </ul>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #27ae60;">
                        <h4 style="color: #2c3e50; margin-bottom: 10px;">对比算法模块</h4>
                        <ul style="list-style: none; padding: 0;">
                            <li style="padding: 5px 0;">📄 <code>enhanced_csv_comparison.py</code></li>
                            <li style="padding-left: 20px; color: #7f8c8d;">• 单元格级别对比 (92.6%准确率)</li>
                            <li style="padding-left: 20px; color: #7f8c8d;">• 列数自适应处理</li>
                            <li style="padding: 5px 0;">📄 <code>baseline_manager.py</code></li>
                            <li style="padding-left: 20px; color: #7f8c8d;">• find_baseline_files() - 查找基线</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- 对比算法规则 -->
            <div style="margin: 20px 0;">
                <h3 style="color: #34495e; margin-bottom: 15px;">🔬 CSV对比算法规则</h3>
                <div style="background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #bdc3c7;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                        <div style="text-align: center;">
                            <div style="font-size: 2em; color: #3498db; font-weight: bold;">60%</div>
                            <div style="color: #7f8c8d; margin-top: 5px;">单元格内容相似度</div>
                            <div style="font-size: 0.9em; color: #95a5a6; margin-top: 5px;">逐个比对每个单元格值</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 2em; color: #27ae60; font-weight: bold;">30%</div>
                            <div style="color: #7f8c8d; margin-top: 5px;">结构相似度</div>
                            <div style="font-size: 0.9em; color: #95a5a6; margin-top: 5px;">列数匹配度评分</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 2em; color: #e74c3c; font-weight: bold;">10%</div>
                            <div style="color: #7f8c8d; margin-top: 5px;">行数相似度</div>
                            <div style="font-size: 0.9em; color: #95a5a6; margin-top: 5px;">行数差异评分</div>
                        </div>
                    </div>
                    <div style="margin-top: 20px; padding: 15px; background: #ecf0f1; border-radius: 5px;">
                        <strong>核心算法特性:</strong>
                        <ul style="margin-top: 10px; padding-left: 20px;">
                            <li>✅ 自动处理不同列数的表格（取最小列数对比）</li>
                            <li>✅ 使用difflib.SequenceMatcher进行智能行匹配</li>
                            <li>✅ 支持增删改行的精确识别</li>
                            <li>✅ 生成详细的对比报告JSON文件</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- 输出文件位置 -->
            <div style="margin: 20px 0;">
                <h3 style="color: #34495e; margin-bottom: 15px;">📤 输出文件位置</h3>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #bdc3c7;">
                    <div style="font-family: monospace; line-height: 1.8;">
                        <div><strong>对比结果:</strong> /root/projects/tencent-doc-manager/comparison_results/</div>
                        <div style="margin-left: 20px; color: #7f8c8d;">
                            └── comparison_[timestamp].json <span style="color: #95a5a6;">← 包含完整对比详情</span>
                        </div>
                        <div style="margin-top: 10px;"><strong>快速对比缓存:</strong> /root/projects/tencent-doc-manager/comparison_results/</div>
                        <div style="margin-left: 20px; color: #7f8c8d;">
                            └── quick_comparison_[timestamp].json <span style="color: #95a5a6;">← 8095端口快速对比结果</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 主功能区域 -->
        <div class="main-grid">
            <!-- Cookie配置卡片 -->
            <!-- 工作流程图 -->
            <div class="card full-width" style="background: #fff; margin-bottom: 20px;">
                <h2 style="color: #2c3e50;">🔄 系统工作流程</h2>
                <div style="display: flex; align-items: center; justify-content: space-around; padding: 20px; flex-wrap: wrap;">
                    <div style="text-align: center; flex: 1; min-width: 150px;">
                        <div style="background: #3498db; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                            <strong>步骤 1</strong><br/>URL输入
                        </div>
                        <div style="font-size: 0.9em; color: #7f8c8d;">用户提供文档URL</div>
                    </div>
                    <div style="font-size: 2em; color: #95a5a6;">→</div>
                    <div style="text-align: center; flex: 1; min-width: 150px;">
                        <div style="background: #27ae60; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                            <strong>步骤 2</strong><br/>文档下载
                        </div>
                        <div style="font-size: 0.9em; color: #7f8c8d;">Playwright自动化下载</div>
                    </div>
                    <div style="font-size: 2em; color: #95a5a6;">→</div>
                    <div style="text-align: center; flex: 1; min-width: 150px;">
                        <div style="background: #e67e22; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                            <strong>步骤 3</strong><br/>版本判断
                        </div>
                        <div style="font-size: 0.9em; color: #7f8c8d;">基线/周中/周末分类</div>
                    </div>
                    <div style="font-size: 2em; color: #95a5a6;">→</div>
                    <div style="text-align: center; flex: 1; min-width: 150px;">
                        <div style="background: #9b59b6; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                            <strong>步骤 4</strong><br/>文件存储
                        </div>
                        <div style="font-size: 0.9em; color: #7f8c8d;">规范化存储到周文件夹</div>
                    </div>
                    <div style="font-size: 2em; color: #95a5a6;">→</div>
                    <div style="text-align: center; flex: 1; min-width: 150px;">
                        <div style="background: #e74c3c; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                            <strong>步骤 5</strong><br/>智能对比
                        </div>
                        <div style="font-size: 0.9em; color: #7f8c8d;">单元格级别精确对比</div>
                    </div>
                </div>
            </div>
            
            <!-- Cookie配置卡片 -->
            <div class="card">
                <h2>🔐 Cookie 配置</h2>
                <div class="form-group">
                    <label>Cookie 字符串 (与项目配置同步)</label>
                    <textarea id="cookie" placeholder="粘贴完整的Cookie字符串..."></textarea>
                </div>
                <button class="btn btn-success" onclick="saveCookieConfig()">保存到项目配置</button>
                <button class="btn" onclick="loadCookieConfig()">从项目配置加载</button>
                <div style="margin-top: 15px; font-size: 0.9rem; color: #6c757d;">
                    <strong>配置文件路径:</strong><br>
                    主配置: /root/projects/tencent-doc-manager/config.json<br>
                    备用: /root/projects/tencent-doc-manager/auto_download_config.json
                </div>
            </div>
            
            <!-- 文档对比卡片 -->
            <div class="card">
                <h2>📊 文档对比测试</h2>
                <div class="form-group">
                    <label>基线文档URL</label>
                    <input type="text" id="baseline-url" placeholder="https://docs.qq.com/sheet/...">
                </div>
                <div class="form-group">
                    <label>目标文档URL</label>
                    <input type="text" id="target-url" placeholder="https://docs.qq.com/sheet/...">
                </div>
                <div class="form-group">
                    <label>对比标准</label>
                    <div style="padding: 12px; background: #f0f8ff; border-radius: 8px; border: 1px solid #4a90e2;">
                        <strong style="color: #2c5282;">📊 统一标准格式</strong>
                        <p style="margin: 5px 0 0 0; color: #555; font-size: 14px;">
                            使用项目唯一对比标准（SimplifiedCSVComparator）<br>
                            输出格式：简化版（2.6KB）- 包含修改列、修改单元格、统计信息
                        </p>
                    </div>
                </div>
                <button class="btn" onclick="startComparison()" id="compare-btn">开始对比</button>
                <button class="btn btn-danger" onclick="cancelComparison()" id="cancel-btn" style="display: none;">取消对比</button>
                <button class="btn btn-success" onclick="viewResults()" style="background: linear-gradient(135deg, #17a2b8 0%, #6f42c1 100%);">查看结果</button>
                <div style="margin-top: 15px; padding: 10px; background: #f0f8ff; border-left: 4px solid #007bff; font-size: 0.9rem;">
                    <strong>📁 文件管理规范说明 (符合02/03规范文档):</strong><br>
                    <br><strong>🔍 文件查找策略:</strong><br>
                    <b>基线文件查找规则:</b><br>
                    • 周一全天+周二12点前 → 查找<span style="color: #dc3545;">上周</span> baseline文件夹<br>
                    • 周二12点后至周日 → 查找<span style="color: #28a745;">本周</span> baseline文件夹<br>
                    • 找不到基线文件将<span style="color: #dc3545;">严格报错</span>，不降级查找<br>
                    <br><b>目标文件查找规则:</b><br>
                    • 周六19点后 → 查找 weekend 文件夹<br>
                    • 其他时间 → 查找 midweek 文件夹<br>
                    • 目标文件可以为空（正常情况）<br>
                    <br><strong>📝 文件存储规范:</strong><br>
                    • 命名: <code>tencent_{文件名}_csv_{YYYYMMDD_HHMM}_{版本类型}_W{周数}.csv</code><br>
                    • 路径: <code>csv_versions/{年份}_W{周数}/{版本类型}/</code><br>
                    • 版本类型: <span style="color: #007bff;">baseline</span>(周二自动) | <span style="color: #17a2b8;">midweek</span>(手动/测试) | <span style="color: #6f42c1;">weekend</span>(周六自动)<br>
                    <br><span style="color: #dc3545;">⚠️ 重要: baseline文件夹仅限自动化任务使用，所有手动下载存入midweek</span>
                </div>
            </div>
            
            <!-- 系统状态卡片 -->
            <div class="card">
                <h2>📈 系统状态</h2>
                <div class="module-status" id="module-status">
                    <!-- 动态加载 -->
                </div>
                <div style="margin-top: 15px;">
                    <div class="result-metric">
                        <span class="label">系统状态:</span>
                        <span class="value" id="system-status">就绪</span>
                    </div>
                    <div class="result-metric">
                        <span class="label">操作计数:</span>
                        <span class="value" id="operation-count">0</span>
                    </div>
                    <div class="result-metric">
                        <span class="label">错误计数:</span>
                        <span class="value" id="error-count">0</span>
                    </div>
                </div>
                <button class="btn" onclick="refreshStatus()">刷新状态</button>
            </div>
            
            <!-- 路径信息面板 -->
            <div class="card full-width">
                <h2>📁 项目路径信息</h2>
                <div class="path-info">
                    <h4>核心目录结构 (项目正式路径)</h4>
                    <div class="path-item">
                        <span class="path-label">项目根目录:</span>
                        <span class="path-value">/root/projects/tencent-doc-manager</span>
                    </div>
                    <div class="path-item">
                        <span class="path-label">正式下载目录:</span>
                        <span class="path-value">/root/projects/tencent-doc-manager/downloads</span>
                    </div>
                    <div class="path-item">
                        <span class="path-label">对比结果目录:</span>
                        <span class="path-value">/root/projects/tencent-doc-manager/comparison_results</span>
                    </div>
                    <div class="path-item">
                        <span class="path-label">主配置文件:</span>
                        <span class="path-value">/root/projects/tencent-doc-manager/config.json</span>
                    </div>
                    <div class="path-item">
                        <span class="path-label">备用配置文件:</span>
                        <span class="path-value">/root/projects/tencent-doc-manager/auto_download_config.json</span>
                    </div>
                </div>
                
                <div class="path-info">
                    <h4>文件命名规则 (严格遵循规范)</h4>
                    <div class="path-item">
                        <span class="path-label">CSV文件标准格式:</span>
                        <span class="path-value">tencent_{文件名}_csv_{YYYYMMDD_HHMM}_{版本类型}_W{周数}.csv</span>
                    </div>
                    <div class="path-item">
                        <span class="path-label">版本目录结构:</span>
                        <span class="path-value">csv_versions/{年份}_W{周数}/{baseline|midweek|weekend}/</span>
                    </div>
                    <div class="path-item">
                        <span class="path-label">对比结果格式:</span>
                        <span class="path-value">simplified_comparison_{YYYYMMDD_HHMMSS}.json</span>
                    </div>
                    <div class="path-item">
                        <span class="path-label">错误码规范:</span>
                        <span class="path-value">E001:基线缺失 | E002:目标缺失 | E003:格式错误 | E004:权限不足 | E005:未知错误</span>
                    </div>
                </div>
                
                <div style="margin-top: 15px;">
                    <button class="btn" onclick="openFileManager()">打开文件管理器</button>
                    <button class="btn" onclick="downloadLogs()" style="background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%);">下载日志</button>
                </div>
            </div>
            
            <!-- 实时日志 -->
            <div class="card two-thirds">
                <h2>📝 实时日志</h2>
                <div class="log-container" id="log-container">
                    <div style="color: #68d391;">系统启动完成，等待操作...</div>
                </div>
                <button class="btn" onclick="clearLogs()">清空日志</button>
            </div>
            
            <!-- 最新对比结果 -->
            <div class="card">
                <h2>📊 最新对比结果</h2>
                <div id="latest-result">
                    <div style="text-align: center; color: #6c757d; padding: 20px;">
                        暂无对比结果
                    </div>
                </div>
                <button class="btn" onclick="loadLatestResult()">刷新结果</button>
            </div>
        </div>
    </div>

    <script>
        // 全局变量
        let isTaskRunning = false;
        let logMessages = [];
        let currentController = null; // 用于存储当前请求的AbortController
        
        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {
            loadCookieConfig();
            refreshStatus();
            loadLatestResult();
            
            // 定期刷新状态
            setInterval(refreshStatus, 10000);
        });
        
        // 日志函数
        function addLog(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString();
            const colors = {
                info: '#e2e8f0',
                success: '#68d391',
                error: '#f56565',
                warning: '#f6e05e'
            };
            
            const logEntry = `<div style="color: ${colors[type]};">[${timestamp}] ${message}</div>`;
            logMessages.push(logEntry);
            
            // 保持最新50条日志
            if (logMessages.length > 50) {
                logMessages = logMessages.slice(-50);
            }
            
            const container = document.getElementById('log-container');
            container.innerHTML = logMessages.join('');
            container.scrollTop = container.scrollHeight;
        }
        
        // Cookie配置相关函数
        function saveCookieConfig() {
            const cookie = document.getElementById('cookie').value.trim();
            if (!cookie) {
                addLog('Cookie不能为空', 'error');
                return;
            }
            
            addLog('正在保存Cookie配置到项目配置文件...', 'info');
            
            fetch('/api/save-cookie', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    cookie: cookie
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('✅ Cookie配置已保存到项目配置文件', 'success');
                    // 同时保存到localStorage
                    localStorage.setItem('tencent_cookie', cookie);
                } else {
                    addLog(`❌ Cookie保存失败: ${data.error}`, 'error');
                }
            })
            .catch(error => {
                addLog(`❌ Cookie保存出错: ${error}`, 'error');
            });
        }
        
        function loadCookieConfig() {
            addLog('正在从项目配置文件加载Cookie...', 'info');
            
            fetch('/api/load-cookie')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.cookie) {
                    document.getElementById('cookie').value = data.cookie;
                    addLog('✅ Cookie已从项目配置文件加载', 'success');
                    // 同时保存到localStorage
                    localStorage.setItem('tencent_cookie', data.cookie);
                } else {
                    // 尝试从localStorage加载
                    const localCookie = localStorage.getItem('tencent_cookie');
                    if (localCookie) {
                        document.getElementById('cookie').value = localCookie;
                        addLog('✅ Cookie已从本地存储加载', 'success');
                    } else {
                        addLog('⚠️ 未找到Cookie配置', 'warning');
                    }
                }
            })
            .catch(error => {
                addLog(`❌ Cookie加载出错: ${error}`, 'error');
                // 尝试从localStorage加载
                const localCookie = localStorage.getItem('tencent_cookie');
                if (localCookie) {
                    document.getElementById('cookie').value = localCookie;
                    addLog('✅ Cookie已从本地存储加载 (fallback)', 'success');
                }
            });
        }
        
        // 对比功能
        function startComparison() {
            if (isTaskRunning) {
                addLog('⚠️ 任务正在运行中，请等待完成', 'warning');
                return;
            }
            
            const baselineUrl = document.getElementById('baseline-url').value.trim();
            const targetUrl = document.getElementById('target-url').value.trim();
            const cookie = document.getElementById('cookie').value.trim();
            
            if (!baselineUrl || !targetUrl) {
                addLog('❌ 请填写基线和目标文档URL', 'error');
                return;
            }
            
            if (!cookie) {
                addLog('❌ 请先配置Cookie', 'error');
                return;
            }
            
            isTaskRunning = true;
            document.getElementById('compare-btn').disabled = true;
            document.getElementById('compare-btn').textContent = '对比进行中...';
            document.getElementById('cancel-btn').style.display = 'inline-block';
            
            addLog('🚀 开始文档对比流程...', 'info');
            addLog(`📄 基线文档: ${baselineUrl}`, 'info');
            addLog(`📄 目标文档: ${targetUrl}`, 'info');
            addLog(`📊 对比标准: 统一简化格式 (UnifiedCSVComparator)`, 'info');
            addLog('⏱️ 预计耗时: 45-60秒 (已优化并行下载)', 'info');
            addLog('💡 提示: 可随时点击"取消对比"按钮中断操作', 'info');
            
            // 保存URL到localStorage
            localStorage.setItem('baseline_url', baselineUrl);
            localStorage.setItem('target_url', targetUrl);
            
            // 创建AbortController用于取消请求
            const controller = new AbortController();
            currentController = controller;
            const timeoutId = setTimeout(() => {
                controller.abort();
                addLog('❌ 请求超时，已自动取消', 'error');
            }, 300000); // 5分钟超时
            
            fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    baseline_url: baselineUrl,
                    target_url: targetUrl,
                    cookie: cookie
                }),
                signal: controller.signal
            })
            .then(response => {
                clearTimeout(timeoutId);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // 重置UI状态
                isTaskRunning = false;
                currentController = null;
                document.getElementById('compare-btn').disabled = false;
                document.getElementById('compare-btn').textContent = '开始对比';
                document.getElementById('cancel-btn').style.display = 'none';
                
                if (data.success) {
                    addLog('✅ 文档对比完成!', 'success');
                    addLog(`📊 总变更数: ${data.result.total_changes}`, 'info');
                    addLog(`📈 相似度: ${(data.result.similarity_score * 100).toFixed(2)}%`, 'info');
                    addLog(`💾 结果文件: ${data.result_file}`, 'info');
                    
                    // 显示结果
                    displayComparisonResult(data.result);
                    loadLatestResult();
                } else {
                    addLog(`❌ 对比失败: ${data.error}`, 'error');
                }
            })
            .catch(error => {
                clearTimeout(timeoutId);
                // 重置UI状态
                isTaskRunning = false;
                currentController = null;
                document.getElementById('compare-btn').disabled = false;
                document.getElementById('compare-btn').textContent = '开始对比';
                document.getElementById('cancel-btn').style.display = 'none';
                
                if (error.name === 'AbortError') {
                    addLog('⚠️ 对比操作已取消', 'warning');
                } else {
                    addLog(`❌ 对比请求出错: ${error.message || error}`, 'error');
                }
            });
        }
        
        // 取消对比功能
        function cancelComparison() {
            if (currentController && isTaskRunning) {
                addLog('⚠️ 正在取消对比操作...', 'warning');
                currentController.abort();
                
                // 重置UI状态
                isTaskRunning = false;
                currentController = null;
                document.getElementById('compare-btn').disabled = false;
                document.getElementById('compare-btn').textContent = '开始对比';
                document.getElementById('cancel-btn').style.display = 'none';
            }
        }
        
        // 显示对比结果
        function displayComparisonResult(result) {
            const resultDiv = document.getElementById('latest-result');
            if (!result) {
                resultDiv.innerHTML = '<div style="text-align: center; color: #6c757d; padding: 20px;">暂无对比结果</div>';
                return;
            }
            
            const html = `
                <div class="comparison-result">
                    <div class="result-metric">
                        <span class="label">总变更数:</span>
                        <span class="value">${result.total_changes}</span>
                    </div>
                    <div class="result-metric">
                        <span class="label">新增行:</span>
                        <span class="value" style="color: #28a745;">${result.added_rows}</span>
                    </div>
                    <div class="result-metric">
                        <span class="label">删除行:</span>
                        <span class="value" style="color: #dc3545;">${result.deleted_rows}</span>
                    </div>
                    <div class="result-metric">
                        <span class="label">修改行:</span>
                        <span class="value" style="color: #ffc107;">${result.modified_rows || 0}</span>
                    </div>
                    <div class="result-metric">
                        <span class="label">相似度:</span>
                        <span class="value">${((result.similarity_score || 0) * 100).toFixed(2)}%</span>
                    </div>
                </div>
            `;
            resultDiv.innerHTML = html;
        }
        
        // 其他功能函数
        function refreshStatus() {
            fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                // 更新模块状态
                const moduleStatusDiv = document.getElementById('module-status');
                let moduleHtml = '';
                for (const [module, status] of Object.entries(data.modules)) {
                    const statusClass = status ? 'module-available' : 'module-unavailable';
                    const indicator = status ? '✅' : '❌';
                    moduleHtml += `<div class="module-item ${statusClass}">${indicator} ${module}</div>`;
                }
                moduleStatusDiv.innerHTML = moduleHtml;
                
                // 更新系统状态
                document.getElementById('system-status').textContent = data.status.current_task || '就绪';
                document.getElementById('operation-count').textContent = data.status.operation_count;
                document.getElementById('error-count').textContent = data.status.error_count;
            })
            .catch(error => {
                addLog(`❌ 状态刷新失败: ${error}`, 'error');
            });
        }
        
        function loadLatestResult() {
            fetch('/api/latest-result')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayComparisonResult(data.result);
                }
            })
            .catch(error => {
                addLog(`❌ 加载最新结果失败: ${error}`, 'error');
            });
        }
        
        function viewResults() {
            window.open('/results', '_blank');
        }
        
        function clearLogs() {
            logMessages = [];
            document.getElementById('log-container').innerHTML = 
                '<div style="color: #68d391;">日志已清空</div>';
        }
        
        function openFileManager() {
            addLog('📂 在新窗口打开文件管理器...', 'info');
            window.open('/files', '_blank');
        }
        
        function downloadLogs() {
            window.location.href = '/api/download-logs';
        }
        
        // 从localStorage恢复URL输入
        if (localStorage.getItem('baseline_url')) {
            document.addEventListener('DOMContentLoaded', function() {
                document.getElementById('baseline-url').value = localStorage.getItem('baseline_url');
                document.getElementById('target-url').value = localStorage.getItem('target_url') || '';
            });
        }
    </script>
</body>
</html>
'''

# ==================== API路由 ====================
@app.route('/')
def index():
    """主页面"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    """获取系统状态"""
    try:
        return jsonify({
            'success': True,
            'modules': MODULES_STATUS,
            'status': {
                'is_busy': system_status.is_busy,
                'current_task': system_status.current_task,
                'operation_count': system_status.operation_count,
                'error_count': system_status.error_count,
                'last_operation': system_status.last_operation
            }
        })
    except Exception as e:
        logger.error(f"❌ 获取状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-cookie', methods=['POST'])
def api_save_cookie():
    """保存Cookie到项目配置文件"""
    try:
        data = request.json
        cookie = data.get('cookie', '')
        
        if not cookie:
            return jsonify({'success': False, 'error': 'Cookie不能为空'})
        
        # 加载当前配置
        config = config_manager.load_config()
        config['cookie'] = cookie
        
        # 保存到项目正式配置文件
        success = config_manager.save_config(config)
        
        if success:
            system_status.last_config_update = datetime.now()
            logger.info("✅ Cookie配置已保存")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '配置保存失败'})
            
    except Exception as e:
        logger.error(f"❌ 保存Cookie失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/load-cookie')
def api_load_cookie():
    """从项目配置文件加载Cookie"""
    try:
        config = config_manager.load_config()
        cookie = config.get('cookie', '')
        
        logger.info("✅ Cookie配置已加载")
        return jsonify({'success': True, 'cookie': cookie})
        
    except Exception as e:
        logger.error(f"❌ 加载Cookie失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """执行文档对比 - 增强版，详细8步骤日志模式"""
    try:
        if system_status.is_busy:
            return jsonify({'success': False, 'error': '系统正忙，请稍后再试'})
        
        # 更新系统状态
        system_status.is_busy = True
        system_status.current_task = "执行CSV对比"
        system_status.operation_count += 1
        
        data = request.json
        baseline_url = data.get('baseline_url', '')
        target_url = data.get('target_url', '')
        cookie = data.get('cookie', '')
        
        # 如果请求中没有提供cookie，从配置文件加载
        if not cookie:
            try:
                config_file = BASE_DIR / 'config.json'
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        cookie = config.get('cookie', '')
                        if cookie:
                            logger.info(f"📥 从配置文件加载Cookie，长度: {len(cookie)}")
            except Exception as e:
                logger.warning(f"⚠️ 加载配置文件Cookie失败: {e}")
        
        # 尝试解析分享链接格式以提取文档名
        baseline_doc_name = None
        target_doc_name = None
        
        if HAS_SHARE_PARSER:
            share_parser = ShareLinkParser()
            try:
                # 尝试解析基线URL
                baseline_info = share_parser.parse_share_link(baseline_url)
                baseline_doc_name = baseline_info.get('doc_name')
                logger.info(f"📝 解析基线文档名: {baseline_doc_name}")
                # 如果是默认生成的名称（如"表格_DWEFNU25"），则置为None
                if baseline_doc_name and baseline_doc_name.startswith('表格_'):
                    logger.info(f"⚠️ 基线文档名是默认生成的，将从文件路径提取")
                    baseline_doc_name = None
            except Exception as e:
                logger.debug(f"⚠️ 基线URL解析失败: {e}")
            
            try:
                # 尝试解析目标URL
                target_info = share_parser.parse_share_link(target_url)
                target_doc_name = target_info.get('doc_name')
                logger.info(f"📝 解析目标文档名: {target_doc_name}")
                # 如果是默认生成的名称（如"表格_DWEFNU25"），则置为None
                if target_doc_name and target_doc_name.startswith('表格_'):
                    logger.info(f"⚠️ 目标文档名是默认生成的，将从文件路径提取")
                    target_doc_name = None
            except Exception as e:
                logger.debug(f"⚠️ 目标URL解析失败: {e}")
        else:
            logger.warning("⚠️ ShareLinkParser未导入，将使用默认命名")
        
        # 启动增强型8步骤对比流程
        logger.info("=" * 80)
        logger.info("🔬 【真实下载对比系统 v4.0】启动 - 6步骤真实下载模式")
        logger.info("=" * 80)
        logger.info(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🌐 基线URL: {baseline_url[:50]}..." if len(baseline_url) > 50 else f"🌐 基线URL: {baseline_url}")
        logger.info(f"🌐 目标URL: {target_url[:50]}..." if len(target_url) > 50 else f"🌐 目标URL: {target_url}")
        logger.info(f"📊 对比标准: UnifiedCSVComparator（项目唯一标准）")
        logger.info(f"🍪 Cookie长度: {len(cookie)}字符")
        logger.info("=" * 80)
        
        # ========== 步骤1/8: URL验证和下载准备 ==========
        logger.info("\n" + "="*70)
        logger.info("🔗 【步骤1/8】: URL验证和下载准备")
        logger.info("="*70)
        
        # 验证输入URL
        if not baseline_url or not target_url:
            logger.error("❌ URL验证失败: 缺少必要的URL参数")
            logger.error(f"   baseline_url: {'✓' if baseline_url else '❌ 缺失'}")
            logger.error(f"   target_url: {'✓' if target_url else '❌ 缺失'}")
            system_status.is_busy = False
            system_status.error_count += 1
            return jsonify({
                'success': False,
                'error': 'E001: URL参数缺失',
                'details': 'baseline_url和target_url都是必需参数'
            })
        
        # 验证Cookie
        if not cookie:
            logger.warning("⚠️ 未提供Cookie，可能影响下载成功率")
        else:
            logger.info(f"✅ Cookie验证通过，长度: {len(cookie)}字符")
        
        logger.info(f"✅ 步骤1完成: URL验证和下载准备完毕")
        
        # ========== 步骤2/8: 真实下载基线文档 ==========
        logger.info("\n" + "="*70)
        logger.info("📥 【步骤2/8】: 真实下载基线文档")
        logger.info("="*70)
        
        logger.info(f"📥 开始下载基线文档...")
        logger.info(f"🔗 基线URL: {baseline_url[:100]}{'...' if len(baseline_url) > 100 else ''}")
        
        baseline_download_start = time.time()
        try:
            baseline_success, baseline_file_path, baseline_error = downloader.download_document(
                baseline_url, cookie, "csv"
            )
            baseline_download_time = time.time() - baseline_download_start
            
            if not baseline_success:
                logger.error(f"❌ 基线文档下载失败: {baseline_error}")
                logger.error(f"⏱️ 下载耗时: {baseline_download_time:.2f}秒")
                system_status.is_busy = False
                system_status.error_count += 1
                return jsonify({
                    'success': False,
                    'error': 'E002: 基线文档下载失败',
                    'details': baseline_error
                })
            
            logger.info(f"✅ 基线文档下载成功")
            logger.info(f"📁 文件路径: {baseline_file_path}")
            logger.info(f"⏱️ 下载耗时: {baseline_download_time:.2f}秒")
            
            if os.path.exists(baseline_file_path):
                baseline_size = os.path.getsize(baseline_file_path)
                logger.info(f"📊 文件大小: {baseline_size:,} bytes ({baseline_size/1024:.1f} KB)")
                
        except Exception as e:
            logger.error(f"❌ 基线文档下载异常: {e}")
            system_status.is_busy = False
            system_status.error_count += 1
            return jsonify({
                'success': False,
                'error': 'E003: 基线文档下载异常',
                'details': str(e)
            })
        
        logger.info(f"✅ 步骤2完成: 基线文档下载完毕")
        
        # ========== 步骤3/8: 真实下载目标文档 ==========
        logger.info("\n" + "="*70)
        logger.info("📥 【步骤3/8】: 真实下载目标文档")
        logger.info("="*70)
        
        logger.info(f"📥 开始下载目标文档...")
        logger.info(f"🔗 目标URL: {target_url[:100]}{'...' if len(target_url) > 100 else ''}")
        
        target_download_start = time.time()
        try:
            target_success, target_file_path, target_error = downloader.download_document(
                target_url, cookie, "csv"
            )
            target_download_time = time.time() - target_download_start
            
            if not target_success:
                logger.error(f"❌ 目标文档下载失败: {target_error}")
                logger.error(f"⏱️ 下载耗时: {target_download_time:.2f}秒")
                system_status.is_busy = False
                system_status.error_count += 1
                return jsonify({
                    'success': False,
                    'error': 'E004: 目标文档下载失败',
                    'details': target_error
                })
            
            logger.info(f"✅ 目标文档下载成功")
            logger.info(f"📁 文件路径: {target_file_path}")
            logger.info(f"⏱️ 下载耗时: {target_download_time:.2f}秒")
            
            if os.path.exists(target_file_path):
                target_size = os.path.getsize(target_file_path)
                logger.info(f"📊 文件大小: {target_size:,} bytes ({target_size/1024:.1f} KB)")
                
        except Exception as e:
            logger.error(f"❌ 目标文档下载异常: {e}")
            system_status.is_busy = False
            system_status.error_count += 1
            return jsonify({
                'success': False,
                'error': 'E005: 目标文档下载异常',
                'details': str(e)
            })
        
        logger.info(f"✅ 步骤3完成: 目标文档下载完毕")
        
        # ========== 步骤4/8: 文件验证和预处理 ==========
        logger.info("\n" + "="*70)
        logger.info("🔍 【步骤4/8】: 文件验证和预处理")
        logger.info("="*70)
        
        # 验证下载的文件
        baseline_file = baseline_file_path
        target_file = target_file_path
        
        # 验证基线文件
        if not os.path.exists(baseline_file):
            logger.error("❌ 基线文件验证失败: 文件不存在")
            system_status.is_busy = False
            system_status.error_count += 1
            return jsonify({'success': False, 'error': 'E006: 下载的基线文件不存在'})
        
        # 验证目标文件
        if not os.path.exists(target_file):
            logger.error("❌ 目标文件验证失败: 文件不存在")
            system_status.is_busy = False
            system_status.error_count += 1
            return jsonify({'success': False, 'error': 'E007: 下载的目标文件不存在'})
        
        # 文件统计信息
        baseline_size = os.path.getsize(baseline_file)
        target_size = os.path.getsize(target_file)
        
        logger.info(f"📄 基线文件验证: {os.path.basename(baseline_file)}")
        logger.info(f"   文件大小: {baseline_size:,} bytes ({baseline_size/1024:.1f} KB)")
        logger.info(f"   ✅ 基线文件验证通过")
        
        logger.info(f"📄 目标文件验证: {os.path.basename(target_file)}")
        logger.info(f"   文件大小: {target_size:,} bytes ({target_size/1024:.1f} KB)")
        logger.info(f"   ✅ 目标文件验证通过")
        
        # 文件相似性预检
        if baseline_file == target_file:
            logger.warning("⚠️ 检测到相同文件路径!")
            logger.warning("   这可能表示下载过程中的问题")
        
        logger.info(f"✅ 步骤4完成: 文件验证和预处理完毕")
        
        
        
        
        
        
        
        # ========== 步骤5/8: 执行CSV对比分析 ==========
        logger.info("\n" + "="*70)
        logger.info("📊 【步骤5/8】: 执行CSV对比分析")
        logger.info("="*70)
        
        # 提取文档名称用于显示（如果没有从分享链接解析到名称，则从文件路径提取）
        if not baseline_doc_name:
            baseline_doc_name = os.path.basename(baseline_file).split('_csv_')[0].replace('tencent_', '')
        if not target_doc_name:
            target_doc_name = os.path.basename(target_file).split('_csv_')[0].replace('tencent_', '')
        
        logger.info(f"🔄 启动CSV对比引擎...")
        logger.info(f"   基线: {os.path.basename(baseline_file)} ({baseline_size/1024:.1f} KB)")
        logger.info(f"   目标: {os.path.basename(target_file)} ({target_size/1024:.1f} KB)")
        logger.info(f"   基线文档: {baseline_doc_name}")
        logger.info(f"   目标文档: {target_doc_name}")
        
        # 使用统一对比器
        logger.info("🔧 对比引擎: UnifiedCSVComparator")
        logger.info("📊 输出格式: 简化版 (2.6KB级别)")
        
        # 执行对比
        comparison_start_time = time.time()
        logger.info("⚙️ 开始执行对比算法...")
        
        try:
            result = comparator.compare_files(baseline_file, target_file)
            comparison_duration = time.time() - comparison_start_time
            
            logger.info(f"⚙️ 对比算法执行完成")
            logger.info(f"⏱️ 对比耗时: {comparison_duration:.2f}秒")
            logger.info(f"📊 对比结果统计:")
            logger.info(f"   总变更数: {result.get('total_changes', 0)}")
            logger.info(f"   相似度: {(result.get('similarity_score', 0) * 100):.2f}%")
            logger.info(f"   新增行: {result.get('added_rows', 0)}")
            logger.info(f"   删除行: {result.get('deleted_rows', 0)}")
            logger.info(f"   修改行: {result.get('modified_rows', 0)}")
            
        except Exception as e:
            logger.error(f"❌ 对比算法执行失败: {e}")
            system_status.is_busy = False
            system_status.error_count += 1
            return jsonify({'success': False, 'error': f'E005: 对比执行失败 - {str(e)}'})
        
        logger.info(f"✅ 步骤5完成: CSV对比分析完毕")
        
        # ========== 步骤6/8: 结果保存和报告生成 ==========
        logger.info("\n" + "="*70)
        logger.info("💾 【步骤6/8】: 结果保存和报告生成")
        logger.info("="*70)
        
        logger.info("💾 开始保存对比结果...")
        save_start_time = time.time()
        
        # 真实下载结果信息
        
        # 确保元数据包含文档名称（用于语义化命名）
        result['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'system_version': '4.0.0_real_download',
            'comparison_method': 'UnifiedCSVComparator',
            'format_version': 'simplified_v1.0',
            'baseline_file': baseline_file,
            'target_file': target_file,
            'baseline_url': baseline_url,
            'target_url': target_url,
            'baseline_doc_name': baseline_doc_name,  # 这里包含了从分享链接解析的名称
            'target_doc_name': target_doc_name,      # 这里包含了从分享链接解析的名称
            'baseline_download_time': baseline_download_time,
            'target_download_time': target_download_time,
            'comparison_duration': comparison_duration,
            'baseline_size': baseline_size,
            'target_size': target_size
        }
        
        try:
            result_file = comparator.save_result(result)
            save_duration = time.time() - save_start_time
            
            logger.info(f"💾 结果保存完成")
            logger.info(f"⏱️ 保存耗时: {save_duration:.2f}秒")
            logger.info(f"📁 结果文件: {os.path.basename(result_file)}")
            logger.info(f"📁 完整路径: {result_file}")
            
            if os.path.exists(result_file):
                result_size = os.path.getsize(result_file)
                logger.info(f"📁 文件大小: {result_size:,} bytes ({result_size/1024:.1f} KB)")
            
        except Exception as e:
            logger.error(f"❌ 结果保存失败: {e}")
            result_file = "保存失败"
        
        logger.info(f"✅ 步骤6完成: 结果保存和报告生成完毕")
        
        # 最终成功报告
        total_duration = time.time() - comparison_start_time
        logger.info("\n" + "="*80)
        logger.info("✅ 【6步骤真实下载对比流程完成】- 所有步骤执行成功")
        logger.info("="*80)
        logger.info(f"📥 基线下载: {baseline_doc_name} ({baseline_download_time:.2f}秒)")
        logger.info(f"📥 目标下载: {target_doc_name} ({target_download_time:.2f}秒)")
        logger.info(f"⏱️ 总耗时: {total_duration:.2f}秒")
        logger.info(f"📊 对比效果: {(result.get('similarity_score', 0) * 100):.2f}% 相似度")
        logger.info(f"📁 结果保存: {os.path.basename(result_file)}")
        logger.info("🔧 对比引擎: UnifiedCSVComparator")
        logger.info("="*80)
        
        # 更新系统状态
        system_status.is_busy = False
        system_status.current_task = ""
        system_status.last_operation = f"真实下载对比完成: {baseline_doc_name} vs {target_doc_name}"
        
        return jsonify({
            'success': True,
            'result': result,
            'result_file': result_file,
            'baseline_file': baseline_file,
            'target_file': target_file,
            'baseline_url': baseline_url,
            'target_url': target_url,
            'baseline_doc_name': baseline_doc_name,
            'target_doc_name': target_doc_name,
            'comparison_method': 'UnifiedCSVComparator',
            'baseline_download_time': baseline_download_time,
            'target_download_time': target_download_time,
            'comparison_duration': comparison_duration,
            'total_duration': total_duration,
            'mode': 'real_download_6_step',
            'system_version': '4.0.0_real_download'
        })
        
    except FileNotFoundError as e:
        logger.error(f"❌ 文件未找到异常: {e}")
        system_status.is_busy = False
        system_status.error_count += 1
        return jsonify({'success': False, 'error': str(e), 'error_code': 'E001'})
    except Exception as e:
        logger.error(f"❌ 步骤执行异常: {e}")
        logger.error(f"异常类型: {type(e).__name__}")
        import traceback
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        system_status.is_busy = False
        system_status.error_count += 1
        return jsonify({'success': False, 'error': f'E005: {str(e)}'})
        
    except Exception as e:
        logger.error(f"❌ API总体异常: {e}")
        logger.error(f"异常类型: {type(e).__name__}")
        import traceback
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        
        # 确保系统状态重置
        system_status.is_busy = False
        system_status.current_task = ""
        system_status.error_count += 1
        
        logger.info("="*80)
        logger.error("❌ 【8步骤CSV对比流程异常终止】")
        logger.info("="*80)
        
        return jsonify({
            'success': False, 
            'error': str(e),
            'error_type': type(e).__name__,
            'system_status': 'error_recovered'
        })

@app.route('/api/latest-result')
def api_latest_result():
    """获取最新对比结果"""
    try:
        # 支持两种前缀：新的simplified_和旧的comparison_result_
        result_files = list(COMPARISON_RESULTS_DIR.glob("simplified_*.json")) + \
                      list(COMPARISON_RESULTS_DIR.glob("comparison_result_*.json"))
        if not result_files:
            return jsonify({'success': False, 'error': '暂无对比结果'})
        
        # 获取最新的结果文件
        latest_file = max(result_files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        return jsonify({'success': True, 'result': result, 'file': str(latest_file)})
        
    except Exception as e:
        logger.error(f"❌ 获取最新结果失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download-logs')
def api_download_logs():
    """下载日志文件"""
    try:
        log_files = list(LOG_DIR.glob("*.log"))
        if log_files:
            latest_log = max(log_files, key=os.path.getctime)
            return send_file(latest_log, as_attachment=True)
        else:
            return "未找到日志文件", 404
    except Exception as e:
        logger.error(f"❌ 下载日志失败: {e}")
        return f"下载失败: {e}", 500

@app.route('/results')
def results_page():
    """结果展示页面"""
    try:
        # 支持两种前缀：新的simplified_和旧的comparison_result_
        result_files = list(COMPARISON_RESULTS_DIR.glob("simplified_*.json")) + \
                      list(COMPARISON_RESULTS_DIR.glob("comparison_result_*.json"))
        results = []
        
        for file in sorted(result_files, key=os.path.getctime, reverse=True)[:10]:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                results.append({
                    'file': file.name,
                    'timestamp': file.name.replace('simplified_comparison_', '').replace('comparison_result_', '').replace('.json', ''),
                    'result': result
                })
            except Exception as e:
                logger.warning(f"⚠️ 读取结果文件失败 {file}: {e}")
        
        html = f'''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>对比结果 - 腾讯文档管理系统</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; }}
                .result-card {{ background: #f8f9fa; padding: 20px; margin-bottom: 20px; border-radius: 8px; }}
                .result-header {{ font-size: 1.2rem; font-weight: bold; margin-bottom: 15px; }}
                .metric {{ display: flex; justify-content: space-between; margin-bottom: 5px; }}
                .metric .value {{ font-weight: bold; color: #007bff; }}
            </style>
        </head>
        <body>
            <h1>📊 对比结果历史</h1>
            <p>最新的10个对比结果 | 结果目录: {COMPARISON_RESULTS_DIR}</p>
        '''
        
        for item in results:
            result = item['result']
            html += f'''
            <div class="result-card">
                <div class="result-header">📄 {item['file']}</div>
                <div class="metric">
                    <span>总变更数:</span>
                    <span class="value">{result.get('total_changes', 0)}</span>
                </div>
                <div class="metric">
                    <span>新增行数:</span>
                    <span class="value" style="color: #28a745;">{result.get('added_rows', 0)}</span>
                </div>
                <div class="metric">
                    <span>删除行数:</span>
                    <span class="value" style="color: #dc3545;">{result.get('deleted_rows', 0)}</span>
                </div>
                <div class="metric">
                    <span>相似度:</span>
                    <span class="value">{((result.get('similarity_score', 0)) * 100):.2f}%</span>
                </div>
                <div class="metric">
                    <span>基线行数:</span>
                    <span class="value">{result.get('details', {}).get('baseline_total_rows', 0)}</span>
                </div>
                <div class="metric">
                    <span>目标行数:</span>
                    <span class="value">{result.get('details', {}).get('target_total_rows', 0)}</span>
                </div>
            </div>
            '''
        
        html += '''
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        logger.error(f"❌ 结果页面生成失败: {e}")
        return f"页面生成失败: {e}", 500

@app.route('/files')
def files_page():
    """文件管理页面"""
    try:
        html = f'''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>文件管理 - 腾讯文档管理系统</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; }}
                .directory {{ background: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 8px; }}
                .directory h3 {{ color: #495057; margin-bottom: 10px; }}
                .file-list {{ list-style: none; padding: 0; }}
                .file-item {{ padding: 5px 10px; border-bottom: 1px solid #dee2e6; }}
                .file-item:hover {{ background: #e9ecef; }}
                .file-size {{ color: #6c757d; font-size: 0.9rem; }}
            </style>
        </head>
        <body>
            <h1>📁 项目文件管理</h1>
            <p>项目根目录: {BASE_DIR}</p>
        '''
        
        # 显示各个重要目录的文件
        directories = {
            "下载文件": DOWNLOAD_DIR,
            "对比结果": COMPARISON_RESULTS_DIR,
            "日志文件": LOG_DIR
        }
        
        # 添加CSV版本目录（按规范管理的版本文件）
        # 获取最近的几个周文件夹
        try:
            from production.core_modules.week_time_manager import week_time_manager
            week_info = week_time_manager.get_current_week_info()
            current_week = week_info["week_number"]
            current_year = week_info["year"]
            
            # 显示当前周和前两周的版本文件夹
            for week_offset in range(0, -3, -1):
                week_num = current_week + week_offset
                if week_num > 0:
                    week_dir = CSV_VERSIONS_DIR / f"{current_year}_W{week_num:02d}"
                    if week_dir.exists():
                        # 添加每周的子目录
                        for version_type in ["baseline", "midweek", "weekend"]:
                            sub_dir = week_dir / version_type
                            if sub_dir.exists():
                                dir_label = f"W{week_num:02d} {version_type}版本"
                                if week_offset == 0:
                                    dir_label = f"本周 {dir_label}"
                                elif week_offset == -1:
                                    dir_label = f"上周 {dir_label}"
                                directories[dir_label] = sub_dir
        except Exception as e:
            logger.warning(f"无法加载周版本目录: {e}")
        
        for dir_name, dir_path in directories.items():
            html += f'''
            <div class="directory">
                <h3>{dir_name} ({dir_path})</h3>
                <ul class="file-list">
            '''
            
            try:
                # 只显示CSV文件和特定规范文件，避免glob("*")的安全风险
                csv_files = list(dir_path.glob("*.csv"))
                temp_files = list(dir_path.glob("temp_*.csv"))
                tencent_files = list(dir_path.glob("tencent_*.csv"))
                files = list(set(csv_files + temp_files + tencent_files))
                files = sorted(files, key=os.path.getctime, reverse=True)[:20]  # 最新20个文件
                
                if not files:
                    html += '<li class="file-item">📂 目录为空</li>'
                else:
                    for file in files:
                        if file.is_file():
                            size = file.stat().st_size
                            size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/(1024*1024):.1f} MB"
                            mtime = datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                            html += f'''
                            <li class="file-item">
                                📄 {file.name}
                                <span class="file-size">({size_str} - {mtime})</span>
                            </li>
                            '''
            except Exception as e:
                html += f'<li class="file-item">❌ 读取目录失败: {e}</li>'
            
            html += '</ul></div>'
        
        html += '''
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        logger.error(f"❌ 文件页面生成失败: {e}")
        return f"页面生成失败: {e}", 500

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'version': '3.0.0',
        'system': 'Production Integrated Test System',
        'modules': MODULES_STATUS,
        'directories': {
            'download_dir': str(DOWNLOAD_DIR),
            'results_dir': str(COMPARISON_RESULTS_DIR),
            'config_file': str(CONFIG_PATH)
        },
        'timestamp': datetime.now().isoformat()
    })

# ==================== 启动配置 ====================
if __name__ == '__main__':
    logger.info("🚀 腾讯文档管理系统 - 生产环境集成测试系统 v3.0.0 启动")
    logger.info(f"📁 项目根目录: {BASE_DIR}")
    logger.info(f"📁 下载目录: {DOWNLOAD_DIR}")
    logger.info(f"📁 结果目录: {COMPARISON_RESULTS_DIR}")
    logger.info(f"📄 配置文件: {CONFIG_PATH}")
    logger.info(f"🔧 模块状态: {MODULES_STATUS}")
    
    system_status.start_time = datetime.now()
    
    try:
        app.run(
            host='0.0.0.0',
            port=8094,
            debug=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"❌ 系统启动失败: {e}")
    finally:
        # 清理资源
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(downloader.cleanup())
        except:
            pass
        logger.info("🔄 系统已关闭")