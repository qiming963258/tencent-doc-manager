#!/usr/bin/env python3
"""
全表格发现器 - 发现所有配置的表格（包括未修改的）
用于综合打分系统和热力图显示
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AllTablesDiscoverer:
    """发现所有配置表格的简单模块"""
    
    def __init__(self):
        self.base_path = Path('/root/projects/tencent-doc-manager')
        self.config_path = self.base_path / 'production' / 'config' / 'real_documents.json'
        self.comparison_result_path = self.base_path / 'csv_versions' / 'comparison' / 'comparison_result.json'
        
    def get_all_configured_tables(self) -> List[Dict]:
        """
        获取所有配置的表格（从8089 UI监控设置的源头）
        
        Returns:
            所有配置表格的列表
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                documents = config.get('documents', [])
                
                logger.info(f"从配置文件发现 {len(documents)} 个表格")
                
                # 返回标准化的表格信息
                all_tables = []
                for doc in documents:
                    all_tables.append({
                        'table_name': doc['name'],
                        'table_url': doc.get('url', ''),
                        'doc_id': doc.get('doc_id', ''),
                        'description': doc.get('description', '')
                    })
                
                return all_tables
                
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            return []
    
    def get_modified_tables(self) -> Set[str]:
        """
        获取有修改的表格名称集合
        
        Returns:
            修改过的表格名称集合
        """
        modified_tables = set()
        
        try:
            # 从对比结果中提取修改的表格
            if self.comparison_result_path.exists():
                with open(self.comparison_result_path, 'r', encoding='utf-8') as f:
                    comparison = json.load(f)
                    
                    # 从差异中提取表格名（这里简化处理，实际可能需要更复杂的逻辑）
                    # 比如从文件路径或元数据中提取
                    if 'metadata' in comparison:
                        # 尝试从文件信息中提取表格名
                        for key in ['file1_info', 'file2_info']:
                            if key in comparison['metadata']:
                                # 这里需要根据实际的文件命名规则提取表格名
                                pass
                    
                    # 简单起见，假设所有有差异的都是已修改的
                    if comparison.get('total_differences', 0) > 0:
                        # 从实际的详细打分文件中获取表格名
                        scoring_path = self.base_path / 'scoring_results' / 'detailed'
                        if scoring_path.exists():
                            for file in scoring_path.glob('detailed_score_*.json'):
                                try:
                                    with open(file, 'r', encoding='utf-8') as f:
                                        score_data = json.load(f)
                                        table_name = score_data.get('metadata', {}).get('table_name')
                                        if table_name:
                                            modified_tables.add(table_name)
                                except:
                                    continue
                    
        except Exception as e:
            logger.warning(f"获取修改表格失败: {e}")
        
        return modified_tables
    
    def discover_all_tables_with_status(self) -> Dict:
        """
        发现所有表格并标记修改状态
        
        Returns:
            包含所有表格及其状态的字典
        """
        # 获取所有配置的表格
        all_tables = self.get_all_configured_tables()
        
        # 获取已修改的表格
        modified_tables = self.get_modified_tables()
        
        # 构建结果
        result = {
            'total_tables': len(all_tables),
            'modified_count': len(modified_tables),
            'unmodified_count': len(all_tables) - len(modified_tables),
            'tables': []
        }
        
        # 为每个表格标记状态
        for table in all_tables:
            table_name = table['table_name']
            is_modified = table_name in modified_tables
            
            table_info = {
                'table_name': table_name,
                'table_url': table['table_url'],
                'doc_id': table['doc_id'],
                'is_modified': is_modified,
                'status': 'MODIFIED' if is_modified else 'UNMODIFIED',
                'modifications_count': 1 if is_modified else 0,  # 简化处理
                'aggregated_score': None if is_modified else 0.0  # 未修改的表格分数为0
            }
            
            result['tables'].append(table_info)
        
        logger.info(f"发现总表格数: {result['total_tables']}, "
                   f"已修改: {result['modified_count']}, "
                   f"未修改: {result['unmodified_count']}")
        
        return result
    
    def get_unmodified_tables(self) -> List[Dict]:
        """
        仅获取未修改的表格列表
        
        Returns:
            未修改表格的列表
        """
        discovery = self.discover_all_tables_with_status()
        return [t for t in discovery['tables'] if not t['is_modified']]
    
    def save_discovery_report(self, output_path: str = None) -> str:
        """
        保存表格发现报告
        
        Args:
            output_path: 输出路径
            
        Returns:
            保存的文件路径
        """
        if not output_path:
            output_path = str(self.base_path / 'scoring_results' / 'table_discovery_report.json')
        
        discovery = self.discover_all_tables_with_status()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(discovery, f, ensure_ascii=False, indent=2)
        
        logger.info(f"表格发现报告已保存: {output_path}")
        return output_path


def main():
    """测试函数"""
    discoverer = AllTablesDiscoverer()
    
    # 发现所有表格
    result = discoverer.discover_all_tables_with_status()
    
    print(f"\n📊 表格发现结果:")
    print(f"总表格数: {result['total_tables']}")
    print(f"已修改: {result['modified_count']}")
    print(f"未修改: {result['unmodified_count']}")
    
    print(f"\n📋 表格列表:")
    for table in result['tables']:
        status_icon = "✏️" if table['is_modified'] else "✅"
        print(f"{status_icon} {table['table_name']} - {table['status']}")
    
    # 保存报告
    output_file = discoverer.save_discovery_report()
    print(f"\n💾 报告已保存: {output_file}")


if __name__ == '__main__':
    main()