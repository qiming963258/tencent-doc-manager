#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的腾讯文档CSV导出工具
基于现有的 tencent_doc_api_tester.py 简化改造
"""

import requests
import json
import csv
import re
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import argparse
import base64
import gzip
import urllib.parse


class TencentDocCSVExporter:
    """腾讯文档CSV导出工具"""
    
    def __init__(self, cookies=None):
        self.base_url = "https://docs.qq.com/dop-api/opendoc"
        self.session = requests.Session()
        
        # 设置基本headers
        self.session.headers.update({
            'authority': 'docs.qq.com',
            'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://docs.qq.com/'
        })
        
        # 如果提供了cookies，添加到session
        if cookies:
            if isinstance(cookies, dict):
                self.session.cookies.update(cookies)
            elif isinstance(cookies, str):
                # 如果是字符串格式的cookie
                self._parse_cookie_string(cookies)
    
    def _parse_cookie_string(self, cookie_string):
        """解析cookie字符串"""
        for cookie in cookie_string.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                self.session.cookies[name] = value
    
    def extract_doc_info(self, url):
        """从腾讯文档URL中提取文档ID和表格ID"""
        try:
            # 提取文档ID
            doc_id_match = re.search(r'/(?:sheet|doc)/([A-Za-z0-9]+)', url)
            if not doc_id_match:
                return None, None
            
            doc_id = doc_id_match.group(1)
            
            # 提取表格tab ID（如果有）
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            sheet_id = query_params.get('tab', ['BB08J2'])[0]  # 默认值
            
            return doc_id, sheet_id
        except Exception as e:
            print(f"URL解析错误: {e}")
            return None, None
    
    def get_document_data(self, doc_url):
        """获取文档数据"""
        doc_id, sheet_id = self.extract_doc_info(doc_url)
        if not doc_id:
            raise ValueError(f"无法解析文档URL: {doc_url}")
        
        # 构造API请求
        params = {
            'tab': sheet_id,
            'id': doc_id,
            'outformat': 1,
            'normal': 1
        }
        
        try:
            print(f"正在获取文档数据: {doc_id}, 表格: {sheet_id}")
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'clientVars' in data and 'collab_client_vars' in data['clientVars']:
                return data['clientVars']['collab_client_vars']
            else:
                raise ValueError("响应数据格式不正确")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"请求失败: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析失败: {e}")
    
    def _decode_workbook_data(self, encoded_data):
        """解码工作簿数据"""
        try:
            # 解码base64
            decoded_bytes = base64.b64decode(encoded_data)
            
            # 尝试zlib解压缩
            try:
                import zlib
                decompressed_data = zlib.decompress(decoded_bytes)
            except:
                # 如果zlib失败，尝试gzip
                try:
                    decompressed_data = gzip.decompress(decoded_bytes)
                except:
                    print("无法解压数据，返回原始数据")
                    return decoded_bytes.decode('utf-8', errors='ignore')
            
            # 解压后的数据转换为字符串
            data_str = decompressed_data.decode('utf-8', errors='ignore')
            
            # 尝试解析为JSON
            try:
                workbook_data = json.loads(data_str)
                return workbook_data
            except:
                # 如果不是JSON，返回原始字符串
                return data_str
                
        except Exception as e:
            print(f"数据解码失败: {e}")
            return None
    
    def _parse_workbook_to_table(self, workbook_data):
        """从工作簿数据中解析表格"""
        try:
            # 腾讯文档的工作簿数据似乎是特殊格式
            if isinstance(workbook_data, str):
                # 尝试解析腾讯文档的专有格式
                lines = workbook_data.strip().split('\n')
                table_data = []
                current_row = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # 尝试识别数据模式
                    # 从解压的数据看，似乎有特定的分隔符
                    if '"' in line and '*' in line:
                        # 可能是单元格数据
                        parts = line.split('*')
                        for part in parts:
                            if part.strip():
                                # 清理引号等特殊字符
                                cell_value = part.strip('"').strip()
                                if cell_value and not cell_value.startswith('BB08J2') and not cell_value.startswith('ez6e97'):
                                    current_row.append(cell_value)
                        
                        # 如果这行结束了，添加到表格
                        if current_row and len(current_row) >= 2:
                            table_data.append(current_row[:])
                            current_row = []
                    
                    # 其他可能的行处理...
                    elif '\t' in line:
                        row = line.split('\t')
                        if len(row) > 1:
                            table_data.append([col.strip() for col in row if col.strip()])
                    elif ',' in line and len(line.split(',')) > 2:
                        row = line.split(',')
                        if len(row) > 1:
                            table_data.append([col.strip() for col in row if col.strip()])
                
                # 如果解析到了数据
                if table_data:
                    return table_data
                
                # 如果上面都失败了，尝试简单的行分割
                simple_data = []
                for line in lines[:20]:  # 只取前20行避免输出过长
                    if line.strip() and len(line.strip()) > 1:
                        simple_data.append([line.strip()])
                
                return simple_data if simple_data else None
                        
            elif isinstance(workbook_data, dict):
                # 如果是字典格式，尝试找表格数据
                if 'sheets' in workbook_data:
                    sheets = workbook_data['sheets']
                    if len(sheets) > 0:
                        sheet = sheets[0]
                        if 'data' in sheet:
                            return sheet['data']
                elif 'data' in workbook_data:
                    return workbook_data['data']
                elif 'cells' in workbook_data:
                    return workbook_data['cells']
                        
        except Exception as e:
            print(f"表格解析失败: {e}")
        
        return None
    
    def convert_to_csv(self, data, output_file):
        """将数据转换为CSV格式"""
        try:
            # 尝试解析表格数据结构
            if 'initialAttributedText' in data and 'text' in data['initialAttributedText']:
                text_data = data['initialAttributedText']['text']
                
                # 检查是否有工作簿数据
                if isinstance(text_data, list) and len(text_data) > 0:
                    first_item = text_data[0]
                    if isinstance(first_item, dict) and 'workbook' in first_item:
                        # 尝试解码工作簿数据
                        workbook_encoded = first_item['workbook']
                        print("正在解码工作簿数据...")
                        
                        workbook_data = self._decode_workbook_data(workbook_encoded)
                        if workbook_data:
                            print("工作簿数据解码成功，正在解析表格...")
                            table_data = self._parse_workbook_to_table(workbook_data)
                            
                            if table_data and isinstance(table_data, list):
                                # 将表格数据写入CSV
                                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                                    writer = csv.writer(csvfile)
                                    for row in table_data:
                                        if isinstance(row, list):
                                            writer.writerow(row)
                                        else:
                                            writer.writerow([str(row)])
                                print(f"成功解析 {len(table_data)} 行数据")
                                return True
                            else:
                                print("无法解析表格数据，使用原始格式...")
                        else:
                            print("工作簿数据解码失败，使用原始格式...")
                    
                    elif isinstance(first_item, list):
                        # 直接是表格数据格式
                        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile)
                            for row in text_data:
                                if isinstance(row, list):
                                    writer.writerow(row)
                                else:
                                    writer.writerow([str(row)])
                        return True
            
            # 备用方案：输出基本信息
            print("警告: 无法识别标准表格格式，输出基本结构信息...")
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['数据类型', '内容'])
                
                # 输出主要的表格相关信息
                if 'maxRow' in data:
                    writer.writerow(['最大行数', data['maxRow']])
                if 'maxCol' in data:
                    writer.writerow(['最大列数', data['maxCol']])
                if 'header' in data:
                    writer.writerow(['表格头信息', str(data['header'])[:200]])
                
                # 输出其他关键信息
                for key, value in data.items():
                    if key not in ['initialAttributedText', 'header'] and not key.startswith('_'):
                        writer.writerow([key, str(value)[:100]])
            
            return True
            
        except Exception as e:
            print(f"CSV转换失败: {e}")
            return False
    
    def export_to_csv(self, doc_url, output_path=None):
        """导出文档为CSV"""
        try:
            # 生成输出文件名
            if not output_path:
                doc_id, sheet_id = self.extract_doc_info(doc_url)
                output_path = f"tencent_doc_{doc_id}_{sheet_id}.csv"
            
            # 获取文档数据
            data = self.get_document_data(doc_url)
            
            # 转换为CSV
            if self.convert_to_csv(data, output_path):
                print("[SUCCESS] 成功导出到: {}".format(output_path))
                return output_path
            else:
                print("[ERROR] CSV转换失败")
                return None
                
        except Exception as e:
            print("[ERROR] 导出失败: {}".format(e))
            return None


def main():
    parser = argparse.ArgumentParser(description='腾讯文档CSV导出工具')
    parser.add_argument('url', help='腾讯文档URL')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-c', '--cookies', help='登录Cookie (格式: "name1=value1; name2=value2")')
    
    args = parser.parse_args()
    
    # 创建导出器
    exporter = TencentDocCSVExporter(cookies=args.cookies)
    
    # 执行导出
    result = exporter.export_to_csv(args.url, args.output)
    
    if result:
        print(f"导出完成: {result}")
    else:
        print("导出失败")
        exit(1)


if __name__ == "__main__":
    main()