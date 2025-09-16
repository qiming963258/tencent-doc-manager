#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实文档加载器 - 只加载用户配置的真实腾讯文档
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealDocumentLoader:
    """只加载真实腾讯文档的加载器"""
    
    def __init__(self):
        self.base_path = Path('/root/projects/tencent-doc-manager')
        self.config_path = self.base_path / 'production' / 'config' / 'real_documents.json'
        self.comparison_path = self.base_path / 'csv_versions' / 'comparison'
        self.real_docs = self._load_real_documents()
        
    def _load_real_documents(self) -> List[Dict]:
        """加载真实文档配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config['documents']
        except Exception as e:
            logger.error(f"加载文档配置失败: {e}")
            # 返回默认的3个文档
            return [
                {
                    "name": "测试版本-回国销售计划表",
                    "doc_id": "DRFppYm15RGZ2WExN",
                    "csv_pattern": "realtest"
                },
                {
                    "name": "副本-测试版本-出国销售计划表",
                    "doc_id": "DWEFNU25TemFnZXJN",
                    "csv_pattern": "test"
                },
                {
                    "name": "第三个测试文档",
                    "doc_id": "DRHZrS1hOS3pwRGZB",
                    "csv_pattern": "test_data"
                }
            ]
    
    def get_real_csv_files(self) -> List[Dict]:
        """获取所有真实文档的CSV文件（动态数量）"""
        real_files = []
        
        # 处理配置中的所有真实文档（不限制数量）
        for doc in self.real_docs:
            pattern = doc['csv_pattern']
            
            # 查找匹配的CSV文件对
            previous_files = list(self.comparison_path.glob(f'previous_{pattern}*.csv'))
            current_files = list(self.comparison_path.glob(f'current_{pattern}*.csv'))
            
            if previous_files and current_files:
                # 取最新的一对文件
                prev_file = sorted(previous_files)[-1] if previous_files else None
                curr_file = sorted(current_files)[-1] if current_files else None
                
                if prev_file and curr_file:
                    real_files.append({
                        'id': len(real_files),
                        'name': doc['name'],  # 使用真实的腾讯文档名称
                        'doc_id': doc['doc_id'],
                        'url': f"https://docs.qq.com/sheet/{doc['doc_id']}",
                        'previous_file': str(prev_file),
                        'current_file': str(curr_file),
                        'has_comparison': True
                    })
                    logger.info(f"✅ 加载真实文档: {doc['name']}")
        
        # 不再限制文档数量，支持动态行数
        # if len(real_files) > 3:
        #     real_files = real_files[:3]
        
        logger.info(f"✅ 加载了 {len(real_files)} 个真实腾讯文档")
        return real_files
    
    def parse_pasted_content(self, content: str) -> Dict:
        """解析用户粘贴的腾讯文档内容
        格式：【腾讯文档】文档名称
              https://docs.qq.com/sheet/xxxxx
        """
        lines = content.strip().split('\n')
        if len(lines) >= 2:
            # 提取文档名称
            name_line = lines[0]
            if '【腾讯文档】' in name_line:
                name = name_line.replace('【腾讯文档】', '').strip()
            else:
                name = name_line.strip()
            
            # 提取URL和文档ID
            url = lines[1].strip()
            doc_id = url.split('/')[-1] if '/' in url else ''
            
            return {
                'name': name,
                'url': url,
                'doc_id': doc_id
            }
        return None
    
    def load_comparison_result(self, previous_file: str, current_file: str) -> Dict:
        """加载两个CSV文件的对比结果"""
        try:
            # 读取previous文件
            previous_data = []
            with open(previous_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                previous_data = list(reader)
            
            # 读取current文件
            current_data = []
            with open(current_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                current_data = list(reader)
            
            # 计算差异
            differences = []
            max_rows = max(len(previous_data), len(current_data))
            max_cols = max(
                len(previous_data[0]) if previous_data else 0,
                len(current_data[0]) if current_data else 0
            )
            
            for row_idx in range(max_rows):
                for col_idx in range(max_cols):
                    old_value = ''
                    new_value = ''
                    
                    if row_idx < len(previous_data) and col_idx < len(previous_data[row_idx]):
                        old_value = previous_data[row_idx][col_idx]
                    if row_idx < len(current_data) and col_idx < len(current_data[row_idx]):
                        new_value = current_data[row_idx][col_idx]
                    
                    if old_value != new_value:
                        differences.append({
                            'row': row_idx,
                            'col': col_idx,
                            'old_value': old_value,
                            'new_value': new_value
                        })
            
            return {
                'total_differences': len(differences),
                'differences': differences
            }
            
        except Exception as e:
            logger.error(f"加载对比结果失败: {e}")
            return {'total_differences': 0, 'differences': []}

# 单例实例
real_doc_loader = RealDocumentLoader()

if __name__ == "__main__":
    # 测试加载器
    loader = RealDocumentLoader()
    files = loader.get_real_csv_files()
    print(f"找到 {len(files)} 个真实文档:")
    for f in files:
        print(f"  - {f['name']}: {f['url']}")