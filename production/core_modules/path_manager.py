#!/usr/bin/env python3
"""
路径管理器 - 统一管理系统所有路径
解决路径不一致和硬编码问题

Created: 2025-09-10
Author: System Architecture Team
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class PathManager:
    """统一路径管理器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """单例模式确保全局唯一路径管理器"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化路径管理器"""
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: Optional[str] = None):
        """
        加载路径配置文件
        
        Args:
            config_path: 配置文件路径，默认使用unified_paths.json
        """
        if config_path is None:
            # 使用默认配置文件
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "unified_paths.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
                logger.info(f"路径配置加载成功: {config_path}")
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            self._init_default_config()
        except Exception as e:
            logger.error(f"加载配置失败: {e}，使用默认配置")
            self._init_default_config()
    
    def _init_default_config(self):
        """初始化默认配置（向后兼容）"""
        self._config = {
            "base_paths": {
                "project_root": "/root/projects/tencent-doc-manager",
                "parent_root": "/root/projects"
            },
            "storage_paths": {
                "config": {"path": "{project_root}/config"},
                "downloads": {"path": "{project_root}/downloads"},
                "csv_versions": {"path": "{project_root}/csv_versions"},
                "comparison_results": {"path": "{project_root}/comparison_results"},
                "comparison_baseline": {"path": "{project_root}/comparison_baseline"},
                "comparison_target": {"path": "{project_root}/comparison_target"},
                "scoring_results": {
                    # 修正：统一使用project_root下的路径
                    "detailed": {"path": "{project_root}/scoring_results/detailed"},
                    "comprehensive": {"path": "{project_root}/scoring_results/comprehensive"}
                },
                "semantic_results": {"path": "{project_root}/semantic_results"},
                "semantic_logs": {"path": "{project_root}/semantic_logs"},
                "excel_output": {"path": "{project_root}/excel_output"},
                "excel_uploads": {"path": "{project_root}/excel_uploads"},
                "ui_data": {"path": "{project_root}/ui_data"},
                "logs": {"path": "{project_root}/logs"}
            }
        }
    
    def _resolve_path(self, path_template: str) -> str:
        """
        解析路径模板中的变量
        
        Args:
            path_template: 包含{变量}的路径模板
            
        Returns:
            解析后的实际路径
        """
        if not isinstance(path_template, str):
            return path_template
            
        # 替换基础路径变量
        for key, value in self._config.get("base_paths", {}).items():
            path_template = path_template.replace(f"{{{key}}}", value)
        
        return path_template
    
    def get_path(self, path_key: str, create_if_missing: bool = False) -> Path:
        """
        获取指定键的路径
        
        Args:
            path_key: 路径键，支持点号分隔的嵌套键（如 "scoring_results.detailed"）
            create_if_missing: 如果路径不存在是否创建
            
        Returns:
            Path对象
        """
        # 解析嵌套键
        keys = path_key.split('.')
        current = self._config.get("storage_paths", {})
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, {})
            else:
                raise KeyError(f"路径键不存在: {path_key}")
        
        # 获取路径字符串
        if isinstance(current, dict):
            path_str = current.get("path", "")
        else:
            path_str = str(current)
        
        # 解析路径模板
        resolved_path = self._resolve_path(path_str)
        path_obj = Path(resolved_path)
        
        # 如果需要，创建目录
        if create_if_missing and not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目录: {path_obj}")
        
        return path_obj
    
    def get_all_paths(self) -> Dict[str, Path]:
        """
        获取所有配置的路径
        
        Returns:
            路径字典
        """
        paths = {}
        
        def _extract_paths(data, prefix=""):
            """递归提取所有路径"""
            if isinstance(data, dict):
                for key, value in data.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, dict):
                        if "path" in value:
                            # 这是一个路径定义
                            paths[new_prefix] = Path(self._resolve_path(value["path"]))
                        else:
                            # 继续递归
                            _extract_paths(value, new_prefix)
        
        _extract_paths(self._config.get("storage_paths", {}))
        return paths
    
    def verify_paths(self, fix_missing: bool = False) -> Dict[str, bool]:
        """
        验证所有路径是否存在
        
        Args:
            fix_missing: 是否创建缺失的路径
            
        Returns:
            路径存在性字典
        """
        results = {}
        all_paths = self.get_all_paths()
        
        for key, path in all_paths.items():
            exists = path.exists()
            results[key] = exists
            
            if not exists:
                logger.warning(f"路径不存在: {key} -> {path}")
                if fix_missing:
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        logger.info(f"创建路径: {path}")
                        results[key] = True
                    except Exception as e:
                        logger.error(f"创建路径失败 {path}: {e}")
        
        return results
    
    def get_scoring_results_path(self, detailed: bool = True) -> Path:
        """
        获取打分结果路径（特殊处理，解决历史问题）
        
        Args:
            detailed: True获取详细打分路径，False获取综合打分路径
            
        Returns:
            打分结果路径
        """
        # 检查环境变量是否强制使用旧路径（向后兼容）
        use_legacy_path = os.environ.get("USE_LEGACY_SCORING_PATH", "false").lower() == "true"
        
        if use_legacy_path:
            # 使用旧的错误路径（在parent_root下）
            parent_root = self._config["base_paths"]["parent_root"]
            if detailed:
                return Path(parent_root) / "scoring_results" / "detailed"
            else:
                return Path(parent_root) / "scoring_results" / "comprehensive"
        else:
            # 使用正确的路径（在project_root下）
            if detailed:
                return self.get_path("scoring_results.detailed", create_if_missing=True)
            else:
                return self.get_path("scoring_results.comprehensive", create_if_missing=True)
    
    def migrate_scoring_results(self):
        """
        迁移scoring_results从错误位置到正确位置
        """
        # 旧路径（错误位置）
        old_path = Path(self._config["base_paths"]["parent_root"]) / "scoring_results"
        # 新路径（正确位置）
        new_path = Path(self._config["base_paths"]["project_root"]) / "scoring_results"
        
        if old_path.exists() and not new_path.exists():
            logger.info(f"迁移scoring_results: {old_path} -> {new_path}")
            import shutil
            shutil.move(str(old_path), str(new_path))
            logger.info("迁移完成")
        elif old_path.exists() and new_path.exists():
            logger.warning("新旧路径都存在，需要手动处理合并")
        else:
            logger.info("无需迁移scoring_results")
    
    def cleanup_downloads(self, days: int = 7):
        """
        清理downloads目录中的旧文件
        
        Args:
            days: 保留最近N天的文件
        """
        import time
        
        downloads_path = self.get_path("downloads")
        if not downloads_path.exists():
            logger.warning(f"downloads目录不存在: {downloads_path}")
            return
        
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        cleaned_count = 0
        for file_path in downloads_path.iterdir():
            if file_path.is_file():
                file_mtime = file_path.stat().st_mtime
                if file_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"删除旧文件: {file_path.name}")
                    except Exception as e:
                        logger.error(f"删除文件失败 {file_path}: {e}")
        
        logger.info(f"清理完成，删除了 {cleaned_count} 个旧文件")
        return cleaned_count


# 全局路径管理器实例
path_manager = PathManager()


# 便捷函数
def get_path(path_key: str, create_if_missing: bool = False) -> Path:
    """获取路径的便捷函数"""
    return path_manager.get_path(path_key, create_if_missing)


def get_scoring_path(detailed: bool = True) -> Path:
    """获取打分路径的便捷函数"""
    return path_manager.get_scoring_results_path(detailed)


def verify_all_paths(fix: bool = False) -> Dict[str, bool]:
    """验证所有路径的便捷函数"""
    return path_manager.verify_paths(fix)


if __name__ == "__main__":
    # 测试路径管理器
    print("=== 路径管理器测试 ===")
    
    # 1. 获取所有路径
    print("\n1. 所有配置路径:")
    for key, path in path_manager.get_all_paths().items():
        print(f"  {key}: {path}")
    
    # 2. 验证路径
    print("\n2. 路径验证结果:")
    results = path_manager.verify_paths()
    for key, exists in results.items():
        status = "✓" if exists else "✗"
        print(f"  {status} {key}")
    
    # 3. 获取特定路径
    print("\n3. 获取特定路径:")
    print(f"  downloads: {get_path('downloads')}")
    print(f"  scoring_results.detailed: {get_scoring_path(detailed=True)}")
    
    # 4. 清理downloads
    print("\n4. 清理downloads目录:")
    # cleaned = path_manager.cleanup_downloads(days=7)
    # print(f"  清理了 {cleaned} 个文件")