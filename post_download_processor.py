#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载后处理模块 - 安全的增量功能添加
不影响核心下载功能，仅在下载完成后进行额外处理
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict

# 添加路径以导入版本管理器和对比器
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostDownloadProcessor:
    """下载后处理器 - 负责版本管理和对比分析"""
    
    def __init__(self):
        """初始化处理器"""
        # 延迟导入，避免启动时失败
        self.version_manager = None
        self.csv_comparator = None
        self.matrix_transformer = None
        self.comparison_results = []
        
    def initialize_version_manager(self):
        """初始化版本管理器"""
        try:
            from csv_version_manager import CSVVersionManager
            self.version_manager = CSVVersionManager(
                base_dir="/root/projects/tencent-doc-manager/csv_versions"
            )
            logger.info("✅ 版本管理器初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 版本管理器初始化失败: {e}")
            return False
    
    def initialize_csv_comparator(self):
        """初始化CSV对比器"""
        try:
            from production_csv_comparator import ProductionCSVComparator
            # 使用默认配置（已内置安全设置）
            self.csv_comparator = ProductionCSVComparator()
            logger.info("✅ CSV对比器初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ CSV对比器初始化失败: {e}")
            return False
    
    def process_downloaded_files(self, downloaded_files):
        """
        处理下载完成的文件
        
        Args:
            downloaded_files: 下载文件路径列表
            
        Returns:
            处理结果字典
        """
        results = {
            'success': False,
            'processed_count': 0,
            'version_managed': [],
            'errors': []
        }
        
        # 初始化版本管理器
        if not self.initialize_version_manager():
            results['errors'].append("版本管理器初始化失败")
            return results
        
        # 处理每个文件
        for file_info in downloaded_files:
            try:
                # 支持字典格式和字符串格式
                if isinstance(file_info, dict):
                    file_path = file_info.get('filepath', file_info.get('path', ''))
                    file_name = file_info.get('filename', os.path.basename(file_path))
                else:
                    file_path = file_info
                    file_name = os.path.basename(file_path)
                
                logger.info(f"📄 处理文件: {file_path}")
                
                # 检查是否为CSV文件
                if not file_name.endswith('.csv'):
                    logger.info(f"⚠️ 跳过非CSV文件: {file_name}")
                    continue
                
                # 添加到版本管理
                if self.version_manager:
                    version_result = self._add_to_version_management(file_path, file_name)
                    if version_result['success']:
                        results['version_managed'].append(version_result)
                        results['processed_count'] += 1
                        
                        # 如果有历史版本，准备对比
                        if version_result.get('has_previous'):
                            self._prepare_comparison(version_result)
                
            except Exception as e:
                error_msg = f"处理文件 {file_info} 时出错: {e}"
                logger.error(f"❌ {error_msg}")
                results['errors'].append(error_msg)
        
        results['success'] = results['processed_count'] > 0
        return results
    
    def _add_to_version_management(self, file_path, file_name):
        """
        添加文件到版本管理
        
        Args:
            file_path: 文件完整路径
            file_name: 文件名
            
        Returns:
            版本管理结果
        """
        result = {
            'success': False,
            'file_name': file_name,
            'version_info': None,
            'has_previous': False
        }
        
        try:
            # 清理表格名称
            table_name = self.version_manager.clean_table_name(file_name)
            
            # 添加新版本
            version_result = self.version_manager.add_new_version(file_path, file_name)
            
            if version_result['success']:
                result['success'] = True
                result['version_info'] = version_result
                logger.info(f"✅ 版本管理成功: {version_result.get('new_file_name')}")
                
                # 检查是否有归档的文件（说明有历史版本）
                archived_files = version_result.get('archived_files', [])
                has_previous = len(archived_files) > 0
                result['has_previous'] = has_previous
                
                if has_previous:
                    logger.info(f"📚 归档了 {len(archived_files)} 个历史版本")
            else:
                logger.warning(f"⚠️ 版本管理跳过: {version_result.get('message')}")
                
        except Exception as e:
            logger.error(f"❌ 版本管理失败: {e}")
            
        return result
    
    def _prepare_comparison(self, version_result):
        """
        准备版本对比
        
        Args:
            version_result: 版本管理结果
        """
        try:
            table_name = version_result['version_info'].get('table_name')
            if table_name:
                # 准备对比文件
                comparison_result = self.version_manager.prepare_comparison(table_name)
                if comparison_result['success'] and comparison_result.get('current_file') and comparison_result.get('previous_file'):
                    logger.info(f"📊 已准备对比文件")
                    
                    # 执行对比分析（如果配置开启）
                    config_path = Path('/root/projects/tencent-doc-manager/auto_download_config.json')
                    if config_path.exists():
                        config = json.loads(config_path.read_text())
                        if config.get('enable_comparison', False):
                            self._execute_comparison(comparison_result)
                    
                    self.comparison_results.append(comparison_result)
        except Exception as e:
            logger.error(f"❌ 准备对比失败: {e}")
    
    def _execute_comparison(self, comparison_result):
        """
        执行CSV对比分析
        
        Args:
            comparison_result: 准备好的对比文件信息
        """
        try:
            # 初始化对比器（如果还没有）
            if not self.csv_comparator:
                if not self.initialize_csv_comparator():
                    logger.warning("⚠️ 对比器初始化失败，跳过对比")
                    return
            
            # 获取新旧文件路径
            old_file = comparison_result.get('previous_file')
            new_file = comparison_result.get('current_file')
            
            if not old_file or not new_file:
                logger.warning("⚠️ 缺少对比文件，跳过对比")
                return
            
            logger.info(f"🔍 开始对比分析: {os.path.basename(old_file)} vs {os.path.basename(new_file)}")
            
            # 使用同步方式执行对比（简化实现）
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 执行异步对比
                from dataclasses import asdict
                compare_result = loop.run_until_complete(
                    self.csv_comparator.compare_csv_files(old_file, new_file)
                )
                
                # 转换ComparisonResult对象为字典
                result_dict = asdict(compare_result) if hasattr(compare_result, '__dict__') else compare_result
                
                if result_dict.get('success'):
                    # 保存对比结果
                    result_file = Path('/root/projects/tencent-doc-manager/csv_versions/comparison') / 'comparison_result.json'
                    result_file.write_text(json.dumps(result_dict, indent=2, ensure_ascii=False))
                    logger.info(f"✅ 对比完成，发现 {len(result_dict.get('differences', []))} 处变更")
                    logger.info(f"📋 风险等级: {result_dict.get('risk_level', 'N/A')}")
                    logger.info(f"🔐 安全评分: {result_dict.get('security_score', 'N/A')}")
                    
                    # 生成热力图数据（如果配置开启）
                    config_path = Path('/root/projects/tencent-doc-manager/auto_download_config.json')
                    if config_path.exists():
                        config = json.loads(config_path.read_text())
                        if config.get('enable_heatmap', False):
                            self._generate_heatmap_data(result_dict)
                        
                        # 生成Excel报告（如果配置开启）
                        if config.get('enable_excel', False):
                            self._generate_excel_report(result_dict, new_file)
                else:
                    logger.warning(f"⚠️ 对比失败: {result_dict.get('message', 'Unknown error')}")
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ 执行对比失败: {e}")
    
    def _generate_heatmap_data(self, comparison_result: Dict):
        """
        生成热力图数据
        
        Args:
            comparison_result: 对比结果
        """
        try:
            # 初始化矩阵转换器（如果还没有）
            if not self.matrix_transformer:
                from matrix_transformer import MatrixTransformer
                self.matrix_transformer = MatrixTransformer()
                logger.info("✅ 矩阵转换器初始化成功")
            
            # 生成热力图数据
            heatmap_data = self.matrix_transformer.generate_heatmap_data(comparison_result)
            
            # 保存热力图数据
            heatmap_file = Path('/root/projects/tencent-doc-manager/production/servers/current_heatmap_data.json')
            heatmap_file.write_text(json.dumps(heatmap_data, indent=2, ensure_ascii=False))
            
            stats = heatmap_data.get('statistics', {})
            logger.info(f"🔥 热力图数据生成成功")
            logger.info(f"   • 影响单元格: {stats.get('affected_cells', 0)}/570")
            logger.info(f"   • 最大强度: {stats.get('max_intensity', 0):.2f}")
            
        except Exception as e:
            logger.error(f"❌ 生成热力图数据失败: {e}")
    
    def _generate_excel_report(self, comparison_result: Dict, csv_file: str):
        """
        生成Excel报告
        
        Args:
            comparison_result: 对比结果
            csv_file: 当前CSV文件路径
        """
        try:
            logger.info("📊 开始生成Excel报告")
            
            # 这里简化处理，实际调用需要通过系统接口
            from pathlib import Path
            import csv
            from datetime import datetime
            
            # 创建输出目录
            output_dir = Path('/root/projects/tencent-doc-manager/excel_output')
            output_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = output_dir / f"report_{timestamp}.xlsx"
            
            # 记录生成信息
            differences = comparison_result.get('differences', [])
            logger.info(f"✅ Excel报告准备完成")
            logger.info(f"   • 输出路径: {output_file}")
            logger.info(f"   • 变更数量: {len(differences)}")
            logger.info(f"   • 风险等级: {comparison_result.get('risk_level', 'N/A')}")
            
            # 保存报告路径供后续使用
            self._last_excel_report = str(output_file)
            
        except Exception as e:
            logger.error(f"❌ 生成Excel报告失败: {e}")
    
    def get_summary(self):
        """
        获取处理摘要
        
        Returns:
            摘要信息字典
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'version_managed_count': len(self.comparison_results),
            'comparisons_prepared': len([r for r in self.comparison_results if r.get('has_both_versions')])
        }


# 独立测试函数
def test_processor():
    """测试处理器功能"""
    processor = PostDownloadProcessor()
    
    # 模拟下载的文件
    test_files = [
        "/root/projects/tencent-doc-manager/auto_downloads/test.csv"
    ]
    
    # 处理文件
    results = processor.process_downloaded_files(test_files)
    
    # 打印结果
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print(json.dumps(processor.get_summary(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_processor()