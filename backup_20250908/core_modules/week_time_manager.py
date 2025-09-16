#!/usr/bin/env python3
"""
时间管理和文件版本控制模块
基于 /docs/specifications/02-时间管理和文件版本规格.md 实现
"""

import datetime
import glob
import os
import re
from pathlib import Path
from typing import Tuple, List, Dict, Any


class WeekTimeManager:
    """时间管理核心类 - 严格按照技术规格实现"""
    
    def __init__(self, base_dir: str = "/root/projects/tencent-doc-manager"):
        self.base_dir = Path(base_dir)
        self.csv_versions_dir = self.base_dir / "csv_versions"
        
        # 确保基础目录存在
        self.csv_versions_dir.mkdir(exist_ok=True)
    
    def get_current_week_info(self) -> Dict[str, Any]:
        """
        获取当周信息
        
        Returns:
            dict: 包含当周开始、结束时间和周数信息
        """
        now = datetime.datetime.now()
        monday = now - datetime.timedelta(days=now.weekday())  # 本周一00:00
        saturday = monday + datetime.timedelta(
            days=5, hours=23, minutes=59, seconds=59
        )  # 本周六23:59:59
        
        week_number = monday.isocalendar()[1]  # ISO周数
        
        return {
            "week_start": monday,
            "week_end": saturday,
            "week_number": week_number,
            "year": monday.year,
            "current_time": now
        }
    
    def get_baseline_strategy(self) -> Tuple[str, str, int]:
        """
        严格的基准版选择策略
        
        Returns:
            tuple: (策略类型, 说明文字, 目标周数)
        """
        now = datetime.datetime.now()
        weekday = now.weekday()  # 0=周一, 1=周二...
        hour = now.hour
        week_info = now.isocalendar()  # (year, week, weekday)
        
        if weekday < 1 or (weekday == 1 and hour < 12):
            # 周一全天 OR 周二12点前
            target_week = week_info[1] - 1  # 上周
            return "previous_week", f"使用上周W{target_week}基准版", target_week
        else:
            # 周二12点后 OR 周三到周六
            target_week = week_info[1]  # 本周
            return "current_week", f"使用本周W{target_week}基准版", target_week
    
    def get_week_directory(self, year: int, week_number: int) -> Path:
        """获取指定周的目录路径"""
        week_dir = self.csv_versions_dir / f"{year}_W{week_number:02d}"
        return week_dir
    
    def create_week_structure(self, year: int, week_number: int) -> Dict[str, Path]:
        """创建周目录结构"""
        week_dir = self.get_week_directory(year, week_number)
        
        directories = {
            "week_root": week_dir,
            "baseline": week_dir / "baseline",
            "midweek": week_dir / "midweek", 
            "weekend": week_dir / "weekend"
        }
        
        # 创建所有目录
        for dir_path in directories.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        return directories
    
    def validate_file_naming(self, filename: str) -> bool:
        """
        验证文件命名规范 - 严格遵守规格文档
        
        格式: tencent_{文件名}_csv_{YYYYMMDD_HHMM}_{版本类型}_W{周数}.csv
        """
        pattern = r'^tencent_(.+?)_csv_(\d{8})_(\d{4})_(baseline|midweek|weekend)_W\d{1,2}\.csv$'
        return re.match(pattern, filename) is not None
    
    def generate_filename(self, file_time: datetime.datetime, 
                         version_type: str, week_number: int, 
                         doc_name: str = "未命名文档") -> str:
        """
        生成标准文件名 - 严格遵守规格文档
        
        Args:
            file_time: 文件时间
            version_type: baseline/midweek/weekend
            week_number: 周数
            doc_name: 文档名称
            
        Returns:
            str: 标准格式的文件名
        """
        # 清理文档名称
        import re
        doc_name = re.sub(r'\.(csv|xlsx|xls)$', '', doc_name, flags=re.IGNORECASE)
        doc_name = re.sub(r'[<>:"/\\|?*]', '', doc_name)  # 移除非法字符
        
        timestamp = file_time.strftime("%Y%m%d_%H%M")
        # 格式：tencent_{文件名}_csv_{YYYYMMDD_HHMM}_{版本类型}_W{周数}.csv
        return f"tencent_{doc_name}_csv_{timestamp}_{version_type}_W{week_number:02d}.csv"
    
    def find_baseline_files(self) -> Tuple[List[str], str]:
        """
        严格查找基准版文件 - 找不到就报错
        
        Returns:
            tuple: (基准版文件列表, 策略说明)
            
        Raises:
            FileNotFoundError: 基准版文件不存在时
        """
        strategy, description, target_week = self.get_baseline_strategy()
        current_year = datetime.datetime.now().year
        
        week_dir = self.get_week_directory(current_year, target_week)
        baseline_dir = week_dir / "baseline"
        
        # 查找基准版文件
        pattern = f"*_baseline_W{target_week:02d}.csv"
        baseline_files = glob.glob(str(baseline_dir / pattern))
        
        if not baseline_files:
            if strategy == "current_week":
                raise FileNotFoundError(
                    f"❌ 本周基准版不存在: {baseline_dir}\n"
                    f"预期文件格式: {pattern}\n"
                    f"请检查周二12:00定时下载任务是否正常执行"
                )
            else:  # previous_week
                raise FileNotFoundError(
                    f"❌ 上周基准版不存在: {baseline_dir}\n"
                    f"预期文件格式: {pattern}\n"
                    f"请检查历史数据完整性或手动补充基准版"
                )
        
        return baseline_files, description
    
    def find_latest_files(self, version_type: str = "current") -> List[str]:
        """
        查找最新文件（旧版本，保留兼容性）
        
        Args:
            version_type: current/midweek/weekend
            
        Returns:
            list: 最新文件列表
        """
        if version_type == "current":
            # 使用新的目标文件查找逻辑
            return self.find_target_files()
        else:
            # 查找指定版本类型的最新文件
            week_info = self.get_current_week_info()
            week_dir = self.get_week_directory(week_info["year"], week_info["week_number"])
            version_dir = week_dir / version_type
            pattern = str(version_dir / f"*_{version_type}_*.csv")
            files = glob.glob(pattern)
        
        # 按修改时间排序，返回最新的
        if files:
            files.sort(key=os.path.getmtime, reverse=True)
        
        return files
    
    def find_target_files(self, doc_name: str = None) -> List[str]:
        """
        查找目标文件 - 根据当前时间动态选择版本类型
        符合03-CSV对比文件查找规范
        
        Args:
            doc_name: 可选的文档名称过滤
            
        Returns:
            目标文件路径列表（按时间倒序）
        """
        now = datetime.datetime.now()
        weekday = now.weekday()  # 0=周一, 1=周二...5=周六
        hour = now.hour
        week_info = now.isocalendar()
        
        # 确定使用哪一周的数据
        if weekday < 1 or (weekday == 1 and hour < 12):
            # 周一全天 OR 周二12点前 → 使用上周
            target_week = week_info[1] - 1
        else:
            # 周二12点后 至 周日 → 使用本周
            target_week = week_info[1]
        
        # 确定查找哪个版本文件夹
        if weekday == 5 and hour >= 19:  # 周六晚上7点后
            version_type = "weekend"
        else:  # 其他所有时间默认查找midweek
            version_type = "midweek"
        
        # 构建查找路径
        week_dir = self.get_week_directory(week_info[0], target_week)
        search_folder = week_dir / version_type
        
        # 查找文件
        if doc_name:
            pattern = str(search_folder / f"*{doc_name}*_{version_type}_W{target_week}.csv")
        else:
            pattern = str(search_folder / f"*_{version_type}_W{target_week}.csv")
        
        files = glob.glob(pattern)
        
        if not files:
            # 目标文件可以为空（表示还没有新数据）
            # 注：目标文件缺失不是错误，这是正常情况
            return []
        
        # 按修改时间倒序排序，返回最新的
        files.sort(key=os.path.getmtime, reverse=True)
        
        return files
    
    def get_comparison_cache_path(self, week_number: int, 
                                 comparison_type: str = "vs_baseline") -> Path:
        """获取比对结果缓存路径"""
        cache_dir = self.csv_versions_dir / "comparison_cache"
        cache_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        cache_file = f"comparison_W{week_number:02d}_{comparison_type}_{timestamp}.json"
        
        return cache_dir / cache_file
    
    def create_current_week_link(self) -> None:
        """创建指向当周目录的软链接"""
        week_info = self.get_current_week_info()
        current_week_dir = self.get_week_directory(
            week_info["year"], week_info["week_number"]
        )
        
        # 确保当周目录存在
        self.create_week_structure(week_info["year"], week_info["week_number"])
        
        # 创建current_week软链接
        current_link = self.csv_versions_dir / "current_week"
        
        # 删除旧链接
        if current_link.is_symlink():
            current_link.unlink()
        elif current_link.exists():
            current_link.rmdir()
        
        # 创建新链接
        current_link.symlink_to(current_week_dir.name)
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取当前状态信息"""
        try:
            week_info = self.get_current_week_info()
            strategy, description, target_week = self.get_baseline_strategy()
            baseline_files, _ = self.find_baseline_files()
            latest_files = self.find_latest_files()
            
            return {
                "success": True,
                "current_week": week_info["week_number"],
                "strategy": strategy,
                "description": description,
                "target_week": target_week,
                "baseline_files_count": len(baseline_files),
                "latest_files_count": len(latest_files),
                "baseline_files": baseline_files,
                "latest_files": latest_files[:5],  # 只显示前5个
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }


# 全局实例
week_time_manager = WeekTimeManager()