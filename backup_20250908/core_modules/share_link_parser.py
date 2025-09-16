#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档分享链接解析器
支持解析腾讯文档的分享链接格式，提取文档名称和URL
"""

import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs


class ShareLinkParser:
    """腾讯文档分享链接解析器"""
    
    def __init__(self):
        """初始化解析器"""
        # 支持的URL模式
        self.url_patterns = {
            'sheet': r'/sheet/([A-Za-z0-9]+)',
            'doc': r'/doc/([A-Za-z0-9]+)',
            'form': r'/form/([A-Za-z0-9]+)',
            'slide': r'/slide/([A-Za-z0-9]+)'
        }
    
    def parse_share_link(self, input_text: str) -> Dict[str, str]:
        """
        解析腾讯文档分享链接
        
        支持的格式：
        1. 分享链接格式（推荐）：
           【腾讯文档】副本-测试版本-出国销售计划表
           https://docs.qq.com/sheet/DWHpOdVVKU0VmSXJv?tab=BB08J2
           
        2. 纯URL格式：
           https://docs.qq.com/sheet/DWHpOdVVKU0VmSXJv?tab=BB08J2
        
        Args:
            input_text: 输入的文本，可以是分享链接或URL
            
        Returns:
            {
                'doc_name': '文档名称',
                'url': '完整URL',
                'doc_id': '文档ID',
                'doc_type': '文档类型(sheet/doc/form/slide)'
            }
        """
        lines = input_text.strip().split('\n')
        
        doc_name = None
        url = None
        
        # 解析分享链接格式
        if len(lines) >= 2 and lines[0].startswith('【腾讯文档】'):
            # 提取文档名
            doc_name = lines[0].replace('【腾讯文档】', '').strip()
            # 提取URL（第二行）
            url = lines[1].strip()
        elif len(lines) == 1:
            # 纯URL格式
            url = lines[0].strip()
        else:
            # 尝试找到URL行
            for line in lines:
                if line.startswith('http'):
                    url = line.strip()
                    break
        
        if not url:
            raise ValueError("无法从输入中提取URL")
        
        # 解析URL获取文档信息
        doc_info = self._parse_url(url)
        
        # 如果没有从分享链接获取到文档名，尝试生成默认名称
        if not doc_name:
            doc_name = self._generate_default_name(doc_info)
        
        # 清理文档名中的特殊字符
        doc_name = self._sanitize_doc_name(doc_name)
        
        return {
            'doc_name': doc_name,
            'url': url,
            'doc_id': doc_info['doc_id'],
            'doc_type': doc_info['doc_type']
        }
    
    def parse_comparison_urls(self, baseline_input: str, target_input: str) -> Dict[str, Dict[str, str]]:
        """
        解析对比的两个文档URL
        
        Args:
            baseline_input: 基线文档输入
            target_input: 目标文档输入
            
        Returns:
            {
                'baseline': {doc_name, url, doc_id, doc_type},
                'target': {doc_name, url, doc_id, doc_type}
            }
        """
        baseline_info = self.parse_share_link(baseline_input)
        target_info = self.parse_share_link(target_input)
        
        return {
            'baseline': baseline_info,
            'target': target_info
        }
    
    def _parse_url(self, url: str) -> Dict[str, str]:
        """
        解析URL提取文档信息
        
        Args:
            url: 腾讯文档URL
            
        Returns:
            {
                'doc_id': '文档ID',
                'doc_type': '文档类型'
            }
        """
        # 标准化URL
        if not url.startswith('http'):
            url = 'https://' + url
        
        # 解析URL路径
        parsed = urlparse(url)
        path = parsed.path
        
        # 检测文档类型和ID
        doc_type = None
        doc_id = None
        
        for type_name, pattern in self.url_patterns.items():
            match = re.search(pattern, path)
            if match:
                doc_type = type_name
                doc_id = match.group(1)
                break
        
        if not doc_id:
            raise ValueError(f"无法从URL提取文档ID: {url}")
        
        return {
            'doc_id': doc_id,
            'doc_type': doc_type or 'unknown'
        }
    
    def _generate_default_name(self, doc_info: Dict[str, str]) -> str:
        """
        生成默认文档名称
        
        Args:
            doc_info: 文档信息
            
        Returns:
            默认文档名称
        """
        doc_type_names = {
            'sheet': '表格',
            'doc': '文档',
            'form': '表单',
            'slide': '幻灯片',
            'unknown': '文档'
        }
        
        type_name = doc_type_names.get(doc_info['doc_type'], '文档')
        return f"{type_name}_{doc_info['doc_id'][:8]}"
    
    def _sanitize_doc_name(self, name: str) -> str:
        """
        清理文档名中的特殊字符
        
        Args:
            name: 原始文档名
            
        Returns:
            清理后的文档名
        """
        # 替换文件系统不允许的字符
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r', '\t']
        for char in invalid_chars:
            name = name.replace(char, '-')
        
        # 移除多余空格
        name = ' '.join(name.split())
        
        # 处理超长名称（保留前40字符+...+后10字符）
        if len(name) > 60:
            name = name[:40] + '...' + name[-10:]
        
        return name.strip()
    
    def extract_doc_name_from_url(self, url: str) -> Optional[str]:
        """
        尝试从URL参数中提取文档名称
        某些情况下URL参数可能包含文档名称信息
        
        Args:
            url: 腾讯文档URL
            
        Returns:
            文档名称或None
        """
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            # 检查常见的名称参数
            for param_name in ['title', 'name', 'docname']:
                if param_name in params:
                    return params[param_name][0]
            
            return None
        except:
            return None


class FileNamingService:
    """文件命名服务"""
    
    def __init__(self):
        """初始化命名服务"""
        self.parser = ShareLinkParser()
    
    def generate_comparison_filename(
        self,
        baseline_doc_name: str,
        target_doc_name: str,
        timestamp: str
    ) -> str:
        """
        生成对比结果文件名
        
        格式: simplified_{基线文档名}_vs_{目标文档名}_{时间戳}.json
        
        Args:
            baseline_doc_name: 基线文档名称
            target_doc_name: 目标文档名称
            timestamp: 时间戳 (YYYYMMDD_HHMMSS)
            
        Returns:
            规范化的文件名
        """
        # 清理文档名
        baseline_name = self.parser._sanitize_doc_name(baseline_doc_name)
        target_name = self.parser._sanitize_doc_name(target_doc_name)
        
        # 构建文件名
        filename = f"simplified_{baseline_name}_vs_{target_name}_{timestamp}.json"
        
        # 确保总长度不超过255字符（文件系统限制）
        if len(filename) > 255:
            # 缩短文档名部分
            max_doc_length = (255 - len("simplified__vs__.json") - len(timestamp)) // 2
            baseline_name = baseline_name[:max_doc_length]
            target_name = target_name[:max_doc_length]
            filename = f"simplified_{baseline_name}_vs_{target_name}_{timestamp}.json"
        
        return filename
    
    def extract_doc_names_from_filename(self, filename: str) -> Tuple[str, str]:
        """
        从文件名中提取文档名称
        
        Args:
            filename: 对比结果文件名
            
        Returns:
            (基线文档名, 目标文档名)
        """
        # 移除前缀和后缀
        if filename.startswith('simplified_'):
            filename = filename[11:]  # 移除 'simplified_'
        
        if filename.endswith('.json'):
            filename = filename[:-5]  # 移除 '.json'
        
        # 找到最后的时间戳部分（格式：_YYYYMMDD_HHMMSS）
        import re
        timestamp_pattern = r'_\d{8}_\d{6}$'
        match = re.search(timestamp_pattern, filename)
        
        if match:
            # 移除时间戳
            filename = filename[:match.start()]
        
        # 分割 _vs_
        parts = filename.split('_vs_')
        
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            return filename, ""


# 测试代码
if __name__ == "__main__":
    parser = ShareLinkParser()
    naming_service = FileNamingService()
    
    # 测试分享链接解析
    test_input = """【腾讯文档】副本-测试版本-出国销售计划表
https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"""
    
    result = parser.parse_share_link(test_input)
    print("解析结果:")
    print(f"  文档名: {result['doc_name']}")
    print(f"  URL: {result['url']}")
    print(f"  文档ID: {result['doc_id']}")
    print(f"  文档类型: {result['doc_type']}")
    
    # 测试文件命名
    filename = naming_service.generate_comparison_filename(
        "副本-测试版本-出国销售计划表",
        "副本-副本-测试版本-出国销售计划表",
        "20250906_195349"
    )
    print(f"\n生成的文件名: {filename}")
    
    # 测试文件名解析
    doc1, doc2 = naming_service.extract_doc_names_from_filename(filename)
    print(f"\n从文件名提取:")
    print(f"  基线文档: {doc1}")
    print(f"  目标文档: {doc2}")