#!/usr/bin/env python3
"""
智能基准版管理模块
集成时间管理和CSV对比功能，实现自动化基准版管理
"""

import csv
import datetime
import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from .week_time_manager import week_time_manager
from .adaptive_table_comparator import AdaptiveTableComparator


class BaselineManager:
    """智能基准版管理器"""
    
    def __init__(self, base_dir: str = "/root/projects/tencent-doc-manager"):
        self.base_dir = Path(base_dir)
        self.time_manager = week_time_manager
        self.comparator = AdaptiveTableComparator()
        
        # 初始化目录结构
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self):
        """确保目录结构存在"""
        week_info = self.time_manager.get_current_week_info()
        self.time_manager.create_week_structure(
            week_info["year"], week_info["week_number"]
        )
        self.time_manager.create_current_week_link()
    
    def read_csv_files_from_directory(self, directory_path: Path) -> List[Dict[str, Any]]:
        """
        读取目录中的所有CSV文件
        
        Args:
            directory_path: 目录路径
            
        Returns:
            list: 表格数据列表
        """
        csv_files = directory_path.glob("*.csv")
        tables = []
        
        for csv_file in csv_files:
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    data = list(reader)
                    if data:  # 确保文件不为空
                        table_name = csv_file.stem
                        tables.append({
                            "name": table_name,
                            "data": data,
                            "source_file": str(csv_file),
                            "file_size": csv_file.stat().st_size,
                            "modified_time": datetime.datetime.fromtimestamp(
                                csv_file.stat().st_mtime
                            ).isoformat()
                        })
            except Exception as e:
                print(f"读取CSV文件失败 {csv_file}: {e}")
        
        return tables
    
    def get_baseline_tables(self) -> List[Dict[str, Any]]:
        """
        获取基准版表格数据
        
        Returns:
            list: 基准版表格列表
            
        Raises:
            FileNotFoundError: 基准版不存在时
        """
        baseline_files, description = self.time_manager.find_baseline_files()
        
        if not baseline_files:
            return []
        
        # 获取基准版目录
        strategy, _, target_week = self.time_manager.get_baseline_strategy()
        current_year = datetime.datetime.now().year
        week_dir = self.time_manager.get_week_directory(current_year, target_week)
        baseline_dir = week_dir / "baseline"
        
        return self.read_csv_files_from_directory(baseline_dir)
    
    def get_latest_tables(self) -> List[Dict[str, Any]]:
        """
        获取最新下载的CSV文件
        
        Returns:
            list: 最新表格列表
        """
        latest_files = self.time_manager.find_latest_files("current")
        
        if not latest_files:
            return []
        
        # 读取最新文件所在目录的所有CSV
        latest_dir = Path(latest_files[0]).parent
        return self.read_csv_files_from_directory(latest_dir)
    
    def save_as_baseline(self, source_files: List[str], version_type: str = "baseline") -> Dict[str, Any]:
        """
        将指定文件保存为基准版
        
        Args:
            source_files: 源文件列表
            version_type: 版本类型 (baseline/midweek/weekend)
            
        Returns:
            dict: 操作结果
        """
        try:
            week_info = self.time_manager.get_current_week_info()
            week_dirs = self.time_manager.create_week_structure(
                week_info["year"], week_info["week_number"]
            )
            
            target_dir = week_dirs[version_type]
            copied_files = []
            
            for source_file in source_files:
                source_path = Path(source_file)
                if not source_path.exists():
                    continue
                
                # 生成标准文件名
                file_time = datetime.datetime.fromtimestamp(source_path.stat().st_mtime)
                standard_filename = self.time_manager.generate_filename(
                    file_time, version_type, week_info["week_number"]
                )
                
                target_path = target_dir / standard_filename
                
                # 复制文件
                shutil.copy2(source_path, target_path)
                copied_files.append(standard_filename)
            
            return {
                "success": True,
                "message": f"{version_type}版本保存成功",
                "copied_files": copied_files,
                "target_directory": str(target_dir),
                "version_type": version_type,
                "week_number": week_info["week_number"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"保存{version_type}版本失败: {str(e)}"
            }
    
    def auto_save_current_as_baseline(self) -> Dict[str, Any]:
        """
        自动将当前最新文件保存为基准版
        
        Returns:
            dict: 操作结果
        """
        try:
            latest_files = self.time_manager.find_latest_files("current")
            
            if not latest_files:
                return {
                    "success": False,
                    "error": "未找到最新CSV文件，请先执行下载操作"
                }
            
            return self.save_as_baseline(latest_files, "baseline")
            
        except Exception as e:
            return {
                "success": False,
                "error": f"自动保存基准版失败: {str(e)}"
            }
    
    def compare_with_baseline(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        与基准版进行对比分析
        
        Args:
            force_refresh: 是否强制刷新
            
        Returns:
            dict: 对比结果
        """
        try:
            # 获取当前表格和基准版表格
            current_tables = self.get_latest_tables()
            if not current_tables:
                return {
                    "success": False,
                    "error": "未找到最新下载的CSV文件，请先执行下载操作"
                }
            
            baseline_tables = self.get_baseline_tables()
            if not baseline_tables:
                return {
                    "success": False,
                    "error": "未找到基准版CSV文件，请先设置基准版"
                }
            
            # 执行对比分析
            comparison_result = self.comparator.adaptive_compare_tables(
                current_tables=current_tables,
                reference_tables=baseline_tables
            )
            
            # 保存对比结果
            week_info = self.time_manager.get_current_week_info()
            cache_path = self.time_manager.get_comparison_cache_path(
                week_info["week_number"], "vs_baseline"
            )
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(comparison_result, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "comparison_result": comparison_result,
                "statistics": {
                    "current_tables_count": len(current_tables),
                    "baseline_tables_count": len(baseline_tables),
                    "cache_file": str(cache_path),
                    "processing_time": comparison_result.get("processing_stats", {}).get("total_processing_time", 0),
                    "week_number": week_info["week_number"]
                },
                "message": f"成功完成对比分析：{len(current_tables)} 个当前表格 vs {len(baseline_tables)} 个基准版表格"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"对比分析失败: {str(e)}"
            }
    
    def get_latest_comparison_result(self) -> Dict[str, Any]:
        """
        获取最新的对比结果
        
        Returns:
            dict: 最新对比结果
        """
        try:
            cache_dir = self.time_manager.csv_versions_dir / "comparison_cache"
            if not cache_dir.exists():
                return {
                    "success": False,
                    "error": "未找到对比结果缓存目录"
                }
            
            # 查找最新的对比结果文件
            cache_files = list(cache_dir.glob("comparison_*.json"))
            if not cache_files:
                return {
                    "success": False,
                    "error": "未找到对比结果缓存文件，请先执行对比操作"
                }
            
            # 获取最新文件
            latest_file = max(cache_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            return {
                "success": True,
                "comparison_result": result,
                "file_info": {
                    "cache_file": str(latest_file),
                    "created_time": datetime.datetime.fromtimestamp(
                        latest_file.stat().st_mtime
                    ).isoformat(),
                    "file_size": latest_file.stat().st_size
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取对比结果失败: {str(e)}"
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态信息
        
        Returns:
            dict: 系统状态
        """
        try:
            time_status = self.time_manager.get_status_info()
            
            status = {
                "time_management": time_status,
                "directories": {},
                "file_counts": {},
                "last_update": datetime.datetime.now().isoformat()
            }
            
            # 检查目录状态
            week_info = self.time_manager.get_current_week_info()
            week_dirs = self.time_manager.create_week_structure(
                week_info["year"], week_info["week_number"]
            )
            
            for dir_type, dir_path in week_dirs.items():
                status["directories"][dir_type] = {
                    "path": str(dir_path),
                    "exists": dir_path.exists(),
                    "file_count": len(list(dir_path.glob("*.csv"))) if dir_path.exists() else 0
                }
            
            # 文件计数
            status["file_counts"] = {
                "latest_files": len(self.time_manager.find_latest_files("current")),
                "comparison_cache": len(list((self.time_manager.csv_versions_dir / "comparison_cache").glob("*.json"))) if (self.time_manager.csv_versions_dir / "comparison_cache").exists() else 0
            }
            
            return status
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取系统状态失败: {str(e)}",
                "timestamp": datetime.datetime.now().isoformat()
            }


# 全局实例
baseline_manager = BaselineManager()