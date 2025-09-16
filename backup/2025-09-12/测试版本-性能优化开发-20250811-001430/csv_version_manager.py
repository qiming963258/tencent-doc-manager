#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV版本管理器 - 自动化文件命名和版本控制
整合到腾讯文档下载流程中
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import hashlib


class CSVVersionManager:
    """CSV文件版本管理器"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化版本管理器
        
        Args:
            base_dir: 基础目录路径，默认为当前目录下的csv_versions
        """
        self.base_dir = Path(base_dir or "./csv_versions")
        self.current_dir = self.base_dir / "current"
        self.archive_dir = self.base_dir / "archive"
        self.comparison_dir = self.base_dir / "comparison"
        
        # 确保目录存在
        for dir_path in [self.current_dir, self.archive_dir, self.comparison_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def clean_table_name(self, original_name: str) -> str:
        """
        清理表格名称，去除特殊字符
        
        Args:
            original_name: 原始表格名称
            
        Returns:
            清理后的表格名称
        """
        # 移除前缀如"测试版本-"
        name = re.sub(r'^测试版本-', '', original_name)
        name = re.sub(r'^副本-测试版本-', '', name)
        
        # 移除文件扩展名
        name = re.sub(r'\.(csv|xlsx|xls)$', '', name, flags=re.IGNORECASE)
        
        # 移除或替换特殊字符
        name = re.sub(r'[<>:"/\\|?*]', '', name)  # Windows文件名禁用字符
        name = re.sub(r'\s+', '', name)  # 移除空格
        name = re.sub(r'[-]+', '', name)  # 移除多余的横线
        
        return name.strip()
    
    def generate_version_filename(self, table_name: str, timestamp: datetime = None) -> str:
        """
        生成标准化版本文件名
        
        Args:
            table_name: 表格名称
            timestamp: 时间戳，默认为当前时间
            
        Returns:
            标准化文件名
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        clean_name = self.clean_table_name(table_name)
        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M")
        
        # 查找同名文件的最大版本号
        pattern = f"{clean_name}_{date_str}_*_v*.csv"
        existing_files = list(self.current_dir.glob(pattern)) + list(self.archive_dir.glob(pattern))
        
        max_version = 0
        for file_path in existing_files:
            version_match = re.search(r'_v(\d+)\.csv$', file_path.name)
            if version_match:
                version_num = int(version_match.group(1))
                max_version = max(max_version, version_num)
        
        next_version = max_version + 1
        version_str = f"v{next_version:03d}"
        
        return f"{clean_name}_{date_str}_{time_str}_{version_str}.csv"
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        计算文件MD5哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5哈希值
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"计算文件哈希失败: {e}")
            return ""
    
    def is_duplicate_content(self, new_file: Path, table_name: str) -> Tuple[bool, Optional[str]]:
        """
        检查是否为重复内容
        
        Args:
            new_file: 新文件路径
            table_name: 表格名称
            
        Returns:
            (是否重复, 重复文件名)
        """
        clean_name = self.clean_table_name(table_name)
        new_hash = self.calculate_file_hash(new_file)
        
        if not new_hash:
            return False, None
        
        # 检查current目录
        for existing_file in self.current_dir.glob(f"{clean_name}_*.csv"):
            existing_hash = self.calculate_file_hash(existing_file)
            if existing_hash == new_hash:
                return True, existing_file.name
        
        # 检查archive目录
        for existing_file in self.archive_dir.glob(f"{clean_name}_*.csv"):
            existing_hash = self.calculate_file_hash(existing_file)
            if existing_hash == new_hash:
                return True, existing_file.name
        
        return False, None
    
    def add_new_version(self, source_file: str, table_name: str = None) -> Dict[str, any]:
        """
        添加新版本文件
        
        Args:
            source_file: 源文件路径
            table_name: 表格名称，如果不提供则从文件名提取
            
        Returns:
            处理结果字典
        """
        source_path = Path(source_file)
        
        if not source_path.exists():
            return {
                "success": False,
                "error": f"源文件不存在: {source_file}",
                "action": "file_not_found"
            }
        
        # 提取表格名称
        if table_name is None:
            table_name = source_path.stem
        
        # 检查是否为重复内容
        is_duplicate, duplicate_file = self.is_duplicate_content(source_path, table_name)
        if is_duplicate:
            return {
                "success": False,
                "message": f"文件内容与已存在文件相同: {duplicate_file}",
                "action": "duplicate_content",
                "duplicate_file": duplicate_file
            }
        
        # 生成新版本文件名
        new_filename = self.generate_version_filename(table_name)
        new_path = self.current_dir / new_filename
        
        try:
            # 将current目录中的同名表格文件移动到archive
            clean_name = self.clean_table_name(table_name)
            current_files = list(self.current_dir.glob(f"{clean_name}_*.csv"))
            
            for old_file in current_files:
                archive_path = self.archive_dir / old_file.name
                shutil.move(str(old_file), str(archive_path))
                print(f"旧版本已归档: {old_file.name} -> archive/")
            
            # 复制新文件到current目录
            shutil.copy2(str(source_path), str(new_path))
            
            return {
                "success": True,
                "new_file": new_filename,
                "new_path": str(new_path),
                "table_name": clean_name,
                "archived_files": [f.name for f in current_files],
                "action": "version_added",
                "message": f"新版本已添加: {new_filename}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"文件操作失败: {str(e)}",
                "action": "file_operation_error"
            }
    
    def list_versions(self, table_name: str = None) -> Dict[str, List[Dict]]:
        """
        列出所有版本文件
        
        Args:
            table_name: 表格名称，如果不提供则列出所有表格
            
        Returns:
            版本文件列表字典
        """
        result = {
            "current": [],
            "archive": []
        }
        
        pattern = "*.csv" if table_name is None else f"{self.clean_table_name(table_name)}_*.csv"
        
        # 收集current文件
        for file_path in self.current_dir.glob(pattern):
            file_info = self._extract_file_info(file_path)
            if file_info:
                result["current"].append(file_info)
        
        # 收集archive文件
        for file_path in self.archive_dir.glob(pattern):
            file_info = self._extract_file_info(file_path)
            if file_info:
                result["archive"].append(file_info)
        
        # 按时间排序
        result["current"].sort(key=lambda x: x["timestamp"], reverse=True)
        result["archive"].sort(key=lambda x: x["timestamp"], reverse=True)
        
        return result
    
    def _extract_file_info(self, file_path: Path) -> Optional[Dict]:
        """
        从文件名提取信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            filename = file_path.name
            # 解析文件名格式: {表格名称}_{YYYYMMDD}_{HHMM}_{版本号}.csv
            match = re.match(r'(.+?)_(\d{8})_(\d{4})_(v\d+)\.csv$', filename)
            
            if match:
                table_name, date_str, time_str, version = match.groups()
                timestamp_str = f"{date_str}_{time_str}"
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M")
                
                file_stats = file_path.stat()
                
                return {
                    "filename": filename,
                    "table_name": table_name,
                    "version": version,
                    "timestamp": timestamp,
                    "date": timestamp.strftime("%Y-%m-%d"),
                    "time": timestamp.strftime("%H:%M"),
                    "size_bytes": file_stats.st_size,
                    "size_kb": round(file_stats.st_size / 1024, 2),
                    "path": str(file_path)
                }
        except Exception as e:
            print(f"解析文件信息失败 {file_path}: {e}")
        
        return None
    
    def get_comparison_pair(self, table_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        获取用于对比的文件对（当前版本和前一版本）
        
        Args:
            table_name: 表格名称
            
        Returns:
            (当前版本文件路径, 前一版本文件路径)
        """
        versions = self.list_versions(table_name)
        
        current_file = None
        previous_file = None
        
        # 获取当前版本
        if versions["current"]:
            current_file = versions["current"][0]["path"]
        
        # 获取前一版本（优先从archive中获取最新的）
        if versions["archive"]:
            previous_file = versions["archive"][0]["path"]
        elif len(versions["current"]) > 1:
            previous_file = versions["current"][1]["path"]
        
        return current_file, previous_file
    
    def prepare_comparison(self, table_name: str) -> Dict[str, any]:
        """
        准备对比文件
        
        Args:
            table_name: 表格名称
            
        Returns:
            对比准备结果
        """
        current_file, previous_file = self.get_comparison_pair(table_name)
        
        if not current_file or not previous_file:
            return {
                "success": False,
                "message": "没有足够的版本进行对比",
                "current_file": current_file,
                "previous_file": previous_file
            }
        
        # 复制文件到comparison目录
        current_path = Path(current_file)
        previous_path = Path(previous_file)
        
        comparison_current = self.comparison_dir / f"current_{current_path.name}"
        comparison_previous = self.comparison_dir / f"previous_{previous_path.name}"
        
        try:
            shutil.copy2(current_file, str(comparison_current))
            shutil.copy2(previous_file, str(comparison_previous))
            
            return {
                "success": True,
                "current_file": str(comparison_current),
                "previous_file": str(comparison_previous),
                "table_name": table_name,
                "message": f"对比文件已准备完成: {table_name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"准备对比文件失败: {str(e)}"
            }


def main():
    """命令行工具入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CSV版本管理工具')
    parser.add_argument('action', choices=['add', 'list', 'compare'], help='操作类型')
    parser.add_argument('--file', '-f', help='文件路径（用于add操作）')
    parser.add_argument('--table', '-t', help='表格名称')
    parser.add_argument('--base-dir', '-d', help='基础目录路径')
    
    args = parser.parse_args()
    
    manager = CSVVersionManager(args.base_dir)
    
    if args.action == 'add':
        if not args.file:
            print("错误: add操作需要提供文件路径 (--file)")
            return
        
        result = manager.add_new_version(args.file, args.table)
        if result["success"]:
            print(f"✅ {result['message']}")
            if result["archived_files"]:
                print(f"📁 已归档文件: {', '.join(result['archived_files'])}")
        else:
            print(f"❌ {result.get('error', result.get('message', '操作失败'))}")
    
    elif args.action == 'list':
        versions = manager.list_versions(args.table)
        
        print("📋 版本文件列表:")
        print("\n🔄 当前版本:")
        for file_info in versions["current"]:
            print(f"  📄 {file_info['filename']} ({file_info['size_kb']}KB, {file_info['date']} {file_info['time']})")
        
        print("\n📦 历史版本:")
        for file_info in versions["archive"]:
            print(f"  📄 {file_info['filename']} ({file_info['size_kb']}KB, {file_info['date']} {file_info['time']})")
    
    elif args.action == 'compare':
        if not args.table:
            print("错误: compare操作需要提供表格名称 (--table)")
            return
        
        result = manager.prepare_comparison(args.table)
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"📄 当前版本: {result['current_file']}")
            print(f"📄 对比版本: {result['previous_file']}")
        else:
            print(f"❌ {result.get('error', result.get('message', '对比准备失败'))}")


if __name__ == "__main__":
    main()