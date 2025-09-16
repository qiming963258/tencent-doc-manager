#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件版本管理器 - 按照《时间管理和文件版本规格说明书》实现
实现规范的文件命名、目录结构和查找策略
"""

import os
import re
import hashlib
import glob
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import urllib.parse


class FileVersionManager:
    """
    文件版本管理器 - 严格按照规范实现
    
    功能：
    1. 规范文件命名：tencent_{文件名}_{YYYYMMDD_HHMM}_{版本类型}_W{周数}.{扩展名}
    2. 规范目录结构：csv_versions/2025_W36/baseline/
    3. 时间策略查找：根据当前时间智能选择基准版
    4. 并行下载支持：通过临时文件名和文件锁防止冲突
    """
    
    def __init__(self, base_dir: str = None):
        """
        初始化版本管理器
        
        Args:
            base_dir: 基础目录，默认为当前目录下的csv_versions
        """
        self.base_dir = Path(base_dir or "./csv_versions")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 版本类型定义
        self.version_types = {
            'baseline': '基准版',
            'midweek': '周中版', 
            'weekend': '周末版'
        }
    
    def get_time_strategy(self) -> Tuple[str, str, int]:
        """
        严格时间判断算法 - 核心规格实现
        
        Returns:
            tuple: (策略类型, 说明文字, 周数信息)
        """
        now = datetime.now()
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
    
    def extract_filename_from_url(self, url: str) -> str:
        """
        从腾讯文档URL中提取文件名
        
        Args:
            url: 腾讯文档URL
            
        Returns:
            提取的文件名
        """
        # 如果URL中包含标题参数，优先尝试提取
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.fragment:
            # 检查fragment中是否包含标题信息
            fragment_match = re.search(r'title=([^&]+)', parsed_url.fragment)
            if fragment_match:
                title = urllib.parse.unquote(fragment_match.group(1))
                return title
        
        # 提取文档ID用作默认名称（不再添加"腾讯文档_"前缀，避免搜索失败）
        doc_id_match = re.search(r'/(?:sheet|doc|slide)/([A-Za-z0-9]+)', url)
        if doc_id_match:
            doc_id = doc_id_match.group(1)
            return f"doc_{doc_id}"  # 使用简洁的doc_前缀，避免中文字符
        
        # 默认名称
        return "unnamed_doc"  # 使用英文，避免路径问题
    
    def get_standard_filename(self, url: str, filename: str = None, version_type: str = 'baseline', file_extension: str = 'csv') -> str:
        """
        生成规范文件名 - 支持动态扩展名
        
        Args:
            url: 腾讯文档URL
            filename: 原始文件名（可选）
            version_type: 版本类型
            file_extension: 文件扩展名（默认csv）
            
        Returns:
            规范文件名
        """
        # 确定文件名和扩展名
        if filename:
            # 提取原始扩展名
            ext_match = re.search(r'\.(csv|xlsx|xls|xlsm)$', filename, flags=re.IGNORECASE)
            if ext_match:
                file_extension = ext_match.group(1).lower()
            # 清理原始文件名
            doc_name = re.sub(r'\.(csv|xlsx|xls|xlsm)$', '', filename, flags=re.IGNORECASE)
            doc_name = re.sub(r'[<>:"/\\|?*]', '', doc_name)  # 移除非法字符
        else:
            doc_name = self.extract_filename_from_url(url)
        
        # 获取当前时间信息
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")
        week_info = now.isocalendar()
        week_str = f"W{week_info[1]}"
        
        # 生成规范文件名 - 新格式，支持动态扩展名
        # 格式：tencent_{文件名}_{YYYYMMDD_HHMM}_{版本类型}_W{周数}.{扩展名}
        return f"tencent_{doc_name}_{date_str}_{time_str}_{version_type}_{week_str}.{file_extension}"
    
    def get_temp_filename(self, url: str) -> str:
        """
        生成临时文件名用于下载过程，防止并行冲突
        
        Args:
            url: 腾讯文档URL
            
        Returns:
            临时文件名
        """
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 临时文件名不指定扩展名，因为下载时还不知道实际格式
        return f"temp_download_{url_hash}_{timestamp}.tmp"
    
    def get_save_directory(self, version_type: str = 'baseline') -> Path:
        """
        获取规范保存目录
        
        Args:
            version_type: 版本类型
            
        Returns:
            保存目录路径
        """
        now = datetime.now()
        week_info = now.isocalendar()
        week_dir = f"{week_info[0]}_W{week_info[1]}"
        
        save_dir = self.base_dir / week_dir / version_type
        save_dir.mkdir(parents=True, exist_ok=True)
        
        return save_dir
    
    def find_file_by_strategy(self, url: str, doc_name: str = None) -> Optional[str]:
        """
        按时间策略查找文件 - 智能多策略查找
        
        Args:
            url: 腾讯文档URL（用于提取文档信息）
            doc_name: 文档名称（可选）
            
        Returns:
            找到的文件路径，未找到返回None
        """
        strategy, description, target_week = self.get_time_strategy()
        
        print(f"🎯 查找策略: {description}")
        
        # 构建查找路径
        now = datetime.now()
        if strategy == "current_week":
            week_dir = f"{now.year}_W{target_week}"
        else:  # previous_week
            # 上周可能跨年，需要特殊处理
            if target_week == 0:  # 如果是第0周，实际是去年最后一周
                week_dir = f"{now.year-1}_W52"  # 简化处理，假设去年有52周
            else:
                week_dir = f"{now.year}_W{target_week}"
        
        baseline_dir = self.base_dir / week_dir / "baseline"
        
        if not baseline_dir.exists():
            print(f"❌ 基准版目录不存在: {baseline_dir}")
            return None
        
        # 智能多策略查找 - 解决文件名不匹配问题
        baseline_files = []
        search_patterns = []
        
        # 策略1: 如果提供了doc_name，优先使用
        if doc_name:
            # 支持新旧两种格式和多种扩展名
            for ext in ['csv', 'xlsx', 'xls']:
                # 新格式
                pattern1 = f"tencent_{doc_name}_*_baseline_W{target_week}.{ext}"
                pattern2 = f"tencent_*{doc_name}*_*_baseline_W{target_week}.{ext}"
                # 旧格式（向后兼容）
                pattern3 = f"tencent_{doc_name}_csv_*_baseline_W{target_week}.csv"
                pattern4 = f"tencent_*{doc_name}*_csv_*_baseline_W{target_week}.csv"
                search_patterns.extend([pattern1, pattern2, pattern3, pattern4])
        
        # 策略2: 从URL提取文档ID进行查找
        doc_id_match = re.search(r'/(?:sheet|doc|slide)/([A-Za-z0-9]+)', url)
        if doc_id_match:
            doc_id = doc_id_match.group(1)
            # 直接按文档ID查找，支持多种扩展名
            for ext in ['csv', 'xlsx', 'xls']:
                pattern_new = f"tencent_*_*_baseline_W{target_week}.{ext}"
                pattern_old = f"tencent_*_csv_*_baseline_W{target_week}.csv"
                search_patterns.extend([pattern_new, pattern_old])
        
        # 策略3: 通用模式查找，适用于任何符合格式的基准版文件
        for ext in ['csv', 'xlsx', 'xls']:
            fallback_pattern_new = f"tencent_*_*_baseline_W{target_week}.{ext}"
            fallback_pattern_old = f"tencent_*_csv_*_baseline_W{target_week}.csv"
            if fallback_pattern_new not in search_patterns:
                search_patterns.append(fallback_pattern_new)
            if fallback_pattern_old not in search_patterns:
                search_patterns.append(fallback_pattern_old)
        
        # 执行查找
        for i, pattern in enumerate(search_patterns, 1):
            files = list(baseline_dir.glob(pattern))
            if files:
                baseline_files = files
                print(f"✅ 策略{i}找到{len(files)}个文件，模式: {pattern}")
                break
            else:
                print(f"🔍 策略{i}未找到文件，模式: {pattern}")
        
        if not baseline_files:
            print(f"❌ 所有策略都未找到基准版文件，目录: {baseline_dir}")
            return None
        
        # 策略4: 如果找到多个文件且有URL中的文档ID，优先选择包含该ID的文件
        if len(baseline_files) > 1 and doc_id_match:
            doc_id = doc_id_match.group(1)
            id_matched_files = [f for f in baseline_files if doc_id in f.name]
            if id_matched_files:
                baseline_files = id_matched_files
                print(f"✅ 文档ID匹配过滤后剩余{len(baseline_files)}个文件")
        
        # 选择最新的文件
        latest_file = max(baseline_files, key=lambda x: x.stat().st_mtime)
        print(f"✅ 最终选择文件: {latest_file.name}")
        
        return str(latest_file)
    
    def get_baseline_file(self, url: str, doc_name: str = None, strict: bool = True) -> str:
        """
        获取基准版文件 - 严格模式
        
        Args:
            url: 腾讯文档URL
            doc_name: 文档名称
            strict: 是否严格模式（找不到时报错）
            
        Returns:
            基准版文件路径
            
        Raises:
            FileNotFoundError: 严格模式下找不到基准版时抛出
        """
        baseline_file = self.find_file_by_strategy(url, doc_name)
        
        if baseline_file is None and strict:
            strategy, description, target_week = self.get_time_strategy()
            raise FileNotFoundError(
                f"❌ {description}不存在\n"
                f"请检查基准版文件是否已生成或手动补充基准版"
            )
        
        return baseline_file
    
    def find_files_by_url_info(self, url: str, download_dir: str, max_age_seconds: int = 300) -> List[str]:
        """
        基于URL信息查找下载文件 - 不依赖URL哈希
        
        Args:
            url: 腾讯文档URL
            download_dir: 下载目录
            max_age_seconds: 最大文件年龄（秒）
            
        Returns:
            匹配的文件路径列表
        """
        import time
        
        download_path = Path(download_dir)
        if not download_path.exists():
            return []
        
        current_time = time.time()
        matched_files = []
        
        # 1. 首先查找临时文件（用于下载过程中）
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
        for file_path in download_path.glob(f"temp_download_{url_hash}_*.csv"):
            if current_time - file_path.stat().st_mtime <= max_age_seconds:
                matched_files.append(str(file_path))
        
        # 2. 基于URL提取文档信息进行匹配
        doc_name = self.extract_filename_from_url(url)
        doc_id_match = re.search(r'/(?:sheet|doc|slide)/([A-Za-z0-9]+)', url)
        
        if doc_id_match:
            doc_id = doc_id_match.group(1)
            # 查找包含文档ID的规范文件
            for file_path in download_path.glob("tencent_*.csv"):
                if doc_id in file_path.name and current_time - file_path.stat().st_mtime <= max_age_seconds:
                    matched_files.append(str(file_path))
        
        # 3. 最后按修改时间排序
        matched_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
        
        return matched_files
    
    def organize_downloaded_file(self, downloaded_file: str, url: str, version_type: str = 'baseline') -> Dict[str, any]:
        """
        整理下载的文件到规范目录结构
        
        Args:
            downloaded_file: 下载的文件路径
            url: 原始URL
            version_type: 版本类型
            
        Returns:
            整理结果
        """
        try:
            source_path = Path(downloaded_file)
            if not source_path.exists():
                return {
                    'success': False,
                    'error': f'源文件不存在: {downloaded_file}'
                }
            
            # 生成规范文件名
            standard_filename = self.get_standard_filename(url, source_path.name, version_type)
            
            # 获取保存目录
            save_dir = self.get_save_directory(version_type)
            target_path = save_dir / standard_filename
            
            # 移动文件
            import shutil
            shutil.move(str(source_path), str(target_path))
            
            print(f"✅ 文件已整理到规范目录: {target_path}")
            
            return {
                'success': True,
                'original_file': downloaded_file,
                'standard_file': str(target_path),
                'filename': standard_filename,
                'directory': str(save_dir)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'文件整理失败: {str(e)}'
            }
    
    def create_week_directories(self, weeks_ahead: int = 4) -> List[str]:
        """
        创建未来几周的目录结构
        
        Args:
            weeks_ahead: 提前创建的周数
            
        Returns:
            创建的目录列表
        """
        created_dirs = []
        now = datetime.now()
        
        for i in range(weeks_ahead + 1):  # 包含当前周
            week_info = now.isocalendar()
            target_week = week_info[1] + i
            target_year = week_info[0]
            
            # 处理跨年情况
            if target_week > 52:
                target_week = target_week - 52
                target_year += 1
            
            week_dir = f"{target_year}_W{target_week}"
            
            for version_type in self.version_types.keys():
                dir_path = self.base_dir / week_dir / version_type
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(dir_path))
        
        return created_dirs
    
    def validate_file_naming(self, filename: str) -> Dict[str, any]:
        """
        验证文件命名是否符合规范 - 支持新旧两种格式
        
        Args:
            filename: 文件名
            
        Returns:
            验证结果
        """
        # 新格式：tencent_{文件名}_{YYYYMMDD_HHMM}_{版本类型}_W{周数}.{扩展名}
        new_pattern = r'^tencent_(.+?)_(\d{8})_(\d{4})_(baseline|midweek|weekend)_W(\d+)\.(csv|xlsx|xls|xlsm)$'
        # 旧格式：tencent_{文件名}_csv_{YYYYMMDD_HHMM}_{版本类型}_W{周数}.csv
        old_pattern = r'^tencent_(.+?)_csv_(\d{8})_(\d{4})_(baseline|midweek|weekend)_W(\d+)\.csv$'
        
        # 先尝试新格式
        match = re.match(new_pattern, filename)
        is_new_format = True
        if not match:
            # 尝试旧格式
            match = re.match(old_pattern, filename)
            is_new_format = False
        
        if not match:
            return {
                'valid': False,
                'error': '文件名格式不符合规范',
                'expected_format': 'tencent_{文件名}_{YYYYMMDD_HHMM}_{版本类型}_W{周数}.{扩展名}'
            }
        
        if is_new_format:
            doc_name, date_str, time_str, version_type, week_str, file_ext = match.groups()
        else:
            doc_name, date_str, time_str, version_type, week_str = match.groups()
            file_ext = 'csv'
        
        # 验证日期格式
        try:
            datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M")
        except ValueError:
            return {
                'valid': False,
                'error': '日期时间格式无效',
                'date_str': date_str,
                'time_str': time_str
            }
        
        return {
            'valid': True,
            'doc_name': doc_name,
            'date': date_str,
            'time': time_str,
            'version_type': version_type,
            'week': week_str,
            'url_hash': 'N/A'  # 不再使用URL哈希
        }
    
    def get_current_week_info(self) -> Dict[str, any]:
        """
        获取当前周信息
        
        Returns:
            当前周信息字典
        """
        now = datetime.now()
        week_info = now.isocalendar()
        strategy, description, target_week = self.get_time_strategy()
        
        return {
            'current_year': week_info[0],
            'current_week': week_info[1],
            'current_weekday': week_info[2],
            'strategy': strategy,
            'description': description,
            'target_week': target_week,
            'week_directory': f"{week_info[0]}_W{week_info[1]}"
        }


def main():
    """命令行工具入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='文件版本管理工具')
    parser.add_argument('action', choices=['info', 'create-dirs', 'find', 'validate'], 
                       help='操作类型')
    parser.add_argument('--url', '-u', help='腾讯文档URL')
    parser.add_argument('--filename', '-f', help='文件名')
    parser.add_argument('--base-dir', '-d', help='基础目录路径')
    
    args = parser.parse_args()
    
    manager = FileVersionManager(args.base_dir)
    
    if args.action == 'info':
        info = manager.get_current_week_info()
        print("📅 当前时间策略信息:")
        print(f"  策略: {info['strategy']}")
        print(f"  描述: {info['description']}")
        print(f"  目标周: {info['target_week']}")
        print(f"  周目录: {info['week_directory']}")
    
    elif args.action == 'create-dirs':
        created_dirs = manager.create_week_directories()
        print(f"✅ 创建了 {len(created_dirs)} 个目录:")
        for dir_path in created_dirs:
            print(f"  📁 {dir_path}")
    
    elif args.action == 'find':
        if not args.url:
            print("错误: find操作需要提供URL (--url)")
            return
        
        baseline_file = manager.find_file_by_strategy(args.url)
        if baseline_file:
            print(f"✅ 找到基准版文件: {baseline_file}")
        else:
            print("❌ 未找到基准版文件")
    
    elif args.action == 'validate':
        if not args.filename:
            print("错误: validate操作需要提供文件名 (--filename)")
            return
        
        result = manager.validate_file_naming(args.filename)
        if result['valid']:
            print("✅ 文件命名符合规范")
            print(f"  文档名: {result['doc_name']}")
            print(f"  日期: {result['date']}")
            print(f"  时间: {result['time']}")
            print(f"  版本类型: {result['version_type']}")
            print(f"  周数: {result['week']}")
            # URL哈希已移除，不再显示
        else:
            print(f"❌ {result['error']}")
            if 'expected_format' in result:
                print(f"  期望格式: {result['expected_format']}")


if __name__ == "__main__":
    main()