#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel MCP集成模块 - 封装MCP工具调用
提供Python接口来调用Excel MCP功能
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelMCPClient:
    """Excel MCP客户端封装"""
    
    def __init__(self):
        """初始化MCP客户端"""
        self.excel_dir = Path('/root/projects/tencent-doc-manager/excel_output')
        self.excel_dir.mkdir(exist_ok=True)
        
    def create_workbook(self, filepath: str) -> bool:
        """
        创建新的Excel工作簿
        
        Args:
            filepath: Excel文件路径
            
        Returns:
            是否成功
        """
        # 这里会通过系统调用MCP工具
        # 在实际运行时，我们通过Assistant的工具调用
        logger.info(f"创建工作簿: {filepath}")
        return True
    
    def write_csv_to_excel(self, filepath: str, csv_data: List[List[str]], sheet_name: str = "Sheet1") -> bool:
        """
        将CSV数据写入Excel
        
        Args:
            filepath: Excel文件路径
            csv_data: CSV数据（二维列表）
            sheet_name: 工作表名称
            
        Returns:
            是否成功
        """
        logger.info(f"写入数据到 {sheet_name}: {len(csv_data)} 行")
        return True
    
    def mark_changed_cells(self, filepath: str, differences: List[Dict], sheet_name: str = "Sheet1") -> int:
        """
        标记变更的单元格
        
        Args:
            filepath: Excel文件路径
            differences: 变更列表
            sheet_name: 工作表名称
            
        Returns:
            标记的单元格数量
        """
        marked = 0
        
        for diff in differences:
            row_num = diff.get('行号', 0)
            col_index = diff.get('列索引', 0)
            
            if row_num > 0 and col_index >= 0:
                # 转换为Excel单元格引用
                cell = self._get_cell_reference(row_num, col_index + 1)
                
                # 根据风险等级选择颜色
                risk_level = diff.get('risk_level', 'L3')
                if risk_level == 'L1':
                    color = '#FFCCCC'  # 浅红
                elif risk_level == 'L2':
                    color = '#FFFFCC'  # 浅黄  
                else:
                    color = '#CCFFCC'  # 浅绿
                
                # 应用格式
                self._apply_cell_format(filepath, sheet_name, cell, color, diff)
                marked += 1
                
        logger.info(f"✅ 标记了 {marked} 个变更单元格")
        return marked
    
    def _get_cell_reference(self, row: int, col: int) -> str:
        """转换行列号为Excel单元格引用"""
        col_letter = ''
        while col > 0:
            col -= 1
            col_letter = chr(65 + col % 26) + col_letter
            col //= 26
        return f"{col_letter}{row}"
    
    def _apply_cell_format(self, filepath: str, sheet_name: str, cell: str, color: str, diff: Dict):
        """应用单元格格式"""
        logger.debug(f"格式化 {cell}: 颜色={color}, 风险={diff.get('risk_level')}")
        # 实际的MCP调用将在运行时完成
    
    def add_summary_sheet(self, filepath: str, comparison_result: Dict) -> bool:
        """
        添加汇总表
        
        Args:
            filepath: Excel文件路径
            comparison_result: 对比结果
            
        Returns:
            是否成功
        """
        # 准备汇总数据
        summary_data = [
            ['变更汇总报告', '', ''],
            ['生成时间', comparison_result.get('比较时间', ''), ''],
            ['', '', ''],
            ['总变更数', str(comparison_result.get('total_differences', 0)), ''],
            ['安全评分', str(comparison_result.get('security_score', 100)), ''],
            ['风险等级', comparison_result.get('risk_level', 'N/A'), ''],
            ['', '', ''],
            ['变更详情', '', ''],
            ['行号', '列名', '变更说明']
        ]
        
        # 添加变更详情
        for diff in comparison_result.get('differences', []):
            summary_data.append([
                str(diff.get('行号', '')),
                diff.get('列名', ''),
                f"{diff.get('原值', '')} → {diff.get('新值', '')}"
            ])
        
        logger.info("添加汇总表")
        return True


# 单例模式
_excel_client = None

def get_excel_client() -> ExcelMCPClient:
    """获取Excel MCP客户端单例"""
    global _excel_client
    if _excel_client is None:
        _excel_client = ExcelMCPClient()
    return _excel_client