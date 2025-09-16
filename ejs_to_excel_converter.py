#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EJS格式转Excel转换器
解析腾讯文档的EJS格式，转换为标准Excel文件
"""

import json
import base64
import urllib.parse
import re
import os
from pathlib import Path
import logging
import pandas as pd
import openpyxl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EJSToExcelConverter:
    """EJS格式转Excel转换器"""
    
    def __init__(self):
        self.output_dir = Path("/root/projects/tencent-doc-manager/converted_excel")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def parse_ejs_file(self, ejs_file_path: str) -> dict:
        """解析EJS文件"""
        logger.info(f"解析EJS文件: {ejs_file_path}")
        
        with open(ejs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return self.parse_ejs_content(content)
        
    def parse_ejs_content(self, content: str) -> dict:
        """解析EJS内容"""
        try:
            # 方法1：尝试直接JSON解析
            if content.startswith('{'):
                data = json.loads(content)
                logger.info("✅ 直接JSON解析成功")
                return data
        except:
            pass
            
        try:
            # 方法2：查找JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                logger.info("✅ 提取JSON部分成功")
                return data
        except:
            pass
            
        # 方法3：处理特殊格式
        return self.parse_special_format(content)
        
    def parse_special_format(self, content: str) -> dict:
        """处理特殊的EJS格式"""
        result = {
            'metadata': {},
            'workbook': None,
            'raw_data': []
        }
        
        # 查找workbook数据
        workbook_patterns = [
            r'workbook["\']?\s*:\s*["\']([^"\']+)',
            r'data["\']?\s*:\s*["\']([^"\']+)',
            r'content["\']?\s*:\s*["\']([^"\']+)'
        ]
        
        for pattern in workbook_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                workbook_data = match.group(1)
                result['workbook'] = self.decode_workbook(workbook_data)
                break
                
        # 查找表格数据
        if not result['workbook']:
            result['raw_data'] = self.extract_table_data(content)
            
        return result
        
    def decode_workbook(self, workbook_str: str) -> str:
        """解码workbook数据"""
        try:
            # URL解码
            decoded = urllib.parse.unquote(workbook_str)
            
            # Base64解码
            if self.is_base64(decoded):
                decoded = base64.b64decode(decoded).decode('utf-8')
                
            return decoded
        except Exception as e:
            logger.error(f"解码workbook失败: {e}")
            return workbook_str
            
    def is_base64(self, s: str) -> bool:
        """检查是否为base64编码"""
        try:
            return base64.b64encode(base64.b64decode(s)).decode() == s
        except:
            return False
            
    def extract_table_data(self, content: str) -> list:
        """提取表格数据"""
        data = []
        
        # 查找各种可能的数据格式
        patterns = [
            r'<td[^>]*>(.*?)</td>',  # HTML表格
            r'"value"\s*:\s*"([^"]+)"',  # JSON值
            r'\[([^\]]+)\]',  # 数组格式
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                data.extend(matches)
                
        return data
        
    def convert_to_excel(self, ejs_data: dict, output_filename: str = None) -> str:
        """转换为Excel文件"""
        if not output_filename:
            output_filename = f"converted_{os.getpid()}.xlsx"
            
        output_path = self.output_dir / output_filename
        
        try:
            # 方法1：如果有结构化数据
            if 'sheets' in ejs_data:
                self.create_excel_from_sheets(ejs_data['sheets'], output_path)
                
            # 方法2：如果有workbook数据
            elif ejs_data.get('workbook'):
                self.create_excel_from_workbook(ejs_data['workbook'], output_path)
                
            # 方法3：如果有原始数据
            elif ejs_data.get('raw_data'):
                self.create_excel_from_raw_data(ejs_data['raw_data'], output_path)
                
            else:
                # 创建包含所有数据的Excel
                self.create_debug_excel(ejs_data, output_path)
                
            logger.info(f"✅ Excel文件已创建: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"创建Excel失败: {e}")
            # 保存原始数据以供调试
            debug_path = output_path.with_suffix('.json')
            with open(debug_path, 'w', encoding='utf-8') as f:
                json.dump(ejs_data, f, ensure_ascii=False, indent=2)
            logger.info(f"原始数据已保存: {debug_path}")
            return None
            
    def create_excel_from_sheets(self, sheets_data: list, output_path: Path):
        """从sheets数据创建Excel"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for i, sheet in enumerate(sheets_data):
                sheet_name = sheet.get('name', f'Sheet{i+1}')
                
                # 获取数据
                if 'data' in sheet:
                    df = pd.DataFrame(sheet['data'])
                elif 'cells' in sheet:
                    df = self.cells_to_dataframe(sheet['cells'])
                else:
                    df = pd.DataFrame()
                    
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
    def create_excel_from_workbook(self, workbook_data: str, output_path: Path):
        """从workbook数据创建Excel"""
        try:
            # 尝试解析为JSON
            if isinstance(workbook_data, str):
                workbook_data = json.loads(workbook_data)
                
            # 提取表格数据
            if isinstance(workbook_data, dict):
                if 'sheets' in workbook_data:
                    self.create_excel_from_sheets(workbook_data['sheets'], output_path)
                else:
                    # 创建单个sheet
                    df = pd.DataFrame(workbook_data)
                    df.to_excel(output_path, index=False)
            else:
                # 尝试解析为CSV格式
                lines = workbook_data.split('\n')
                data = [line.split(',') for line in lines if line]
                df = pd.DataFrame(data[1:], columns=data[0] if data else [])
                df.to_excel(output_path, index=False)
                
        except Exception as e:
            logger.error(f"解析workbook失败: {e}")
            # 保存原始数据
            df = pd.DataFrame({'原始数据': [workbook_data]})
            df.to_excel(output_path, index=False)
            
    def create_excel_from_raw_data(self, raw_data: list, output_path: Path):
        """从原始数据创建Excel"""
        # 尝试组织数据为表格
        if raw_data and isinstance(raw_data[0], (list, tuple)):
            df = pd.DataFrame(raw_data)
        else:
            # 单列数据
            df = pd.DataFrame({'数据': raw_data})
            
        df.to_excel(output_path, index=False)
        
    def create_debug_excel(self, ejs_data: dict, output_path: Path):
        """创建调试Excel，包含所有数据"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet1: 元数据
            if ejs_data.get('metadata'):
                df_meta = pd.DataFrame([ejs_data['metadata']])
                df_meta.to_excel(writer, sheet_name='元数据', index=False)
                
            # Sheet2: 原始数据
            df_raw = pd.DataFrame({'内容': [json.dumps(ejs_data, ensure_ascii=False)]})
            df_raw.to_excel(writer, sheet_name='原始数据', index=False)
            
            # Sheet3: 解析的数据
            if ejs_data.get('raw_data'):
                df_data = pd.DataFrame({'数据': ejs_data['raw_data']})
                df_data.to_excel(writer, sheet_name='解析数据', index=False)
                
    def cells_to_dataframe(self, cells: list) -> pd.DataFrame:
        """将cells格式转换为DataFrame"""
        max_row = max(cell.get('row', 0) for cell in cells) + 1
        max_col = max(cell.get('col', 0) for cell in cells) + 1
        
        # 创建空矩阵
        matrix = [['' for _ in range(max_col)] for _ in range(max_row)]
        
        # 填充数据
        for cell in cells:
            row = cell.get('row', 0)
            col = cell.get('col', 0)
            value = cell.get('value', '')
            matrix[row][col] = value
            
        return pd.DataFrame(matrix)
        
    def batch_convert(self, ejs_dir: str):
        """批量转换目录中的所有EJS文件"""
        ejs_files = list(Path(ejs_dir).glob("*.ejs"))
        ejs_files.extend(Path(ejs_dir).glob("*.txt"))
        ejs_files.extend(Path(ejs_dir).glob("*.json"))
        
        results = []
        for ejs_file in ejs_files:
            logger.info(f"\n处理文件: {ejs_file}")
            try:
                ejs_data = self.parse_ejs_file(str(ejs_file))
                excel_path = self.convert_to_excel(
                    ejs_data, 
                    f"{ejs_file.stem}.xlsx"
                )
                results.append({
                    'source': str(ejs_file),
                    'output': excel_path,
                    'success': excel_path is not None
                })
            except Exception as e:
                logger.error(f"处理失败: {e}")
                results.append({
                    'source': str(ejs_file),
                    'error': str(e),
                    'success': False
                })
                
        # 生成报告
        report_path = self.output_dir / 'conversion_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        logger.info(f"\n转换完成！报告已保存: {report_path}")
        return results

def main():
    """主函数"""
    converter = EJSToExcelConverter()
    
    # 检查下载目录
    download_dirs = [
        "/root/projects/tencent-doc-manager/downloads",
        "/root/projects/tencent-doc-manager/test_downloads",
        "/tmp"
    ]
    
    for download_dir in download_dirs:
        if os.path.exists(download_dir):
            files = list(Path(download_dir).glob("*"))
            if files:
                logger.info(f"在 {download_dir} 找到 {len(files)} 个文件")
                
                for file_path in files:
                    if file_path.suffix in ['.ejs', '.txt', '.json'] or 'doc_' in file_path.name:
                        logger.info(f"\n转换文件: {file_path}")
                        try:
                            ejs_data = converter.parse_ejs_file(str(file_path))
                            excel_path = converter.convert_to_excel(
                                ejs_data,
                                f"{file_path.stem}.xlsx"
                            )
                            if excel_path:
                                logger.info(f"✅ 成功转换为: {excel_path}")
                        except Exception as e:
                            logger.error(f"转换失败: {e}")

if __name__ == "__main__":
    main()