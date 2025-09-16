#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
提供导出器的配置选项和扩展机制
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class AdvancedConfig:
    """高级配置选项"""
    # 超时配置
    page_load_timeout: int = 60
    element_wait_timeout: int = 10
    extraction_timeout: int = 30
    
    # 重试配置
    max_retries: int = 2
    retry_delay: int = 2
    
    # 浏览器配置
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    viewport_width: int = 1920
    viewport_height: int = 1080
    
    # 数据处理配置
    max_cells: int = 10000
    max_rows: int = 1000
    min_data_threshold: int = 3
    
    # 输出配置
    csv_encoding: str = "utf-8"
    csv_delimiter: str = ","
    
    # 调试配置
    save_screenshots: bool = False
    screenshot_dir: str = "./debug_screenshots"
    log_level: str = "INFO"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "tencent_exporter_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> AdvancedConfig:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                    return AdvancedConfig(**config_dict)
            except Exception as e:
                print(f"警告: 加载配置文件失败 ({e})，使用默认配置")
        
        return AdvancedConfig()
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
            print(f"配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                print(f"警告: 未知的配置项 {key}")
    
    def get_selectors(self) -> Dict[str, list]:
        """获取自定义选择器配置"""
        selectors_file = "custom_selectors.json"
        default_selectors = {
            "table_cells": [
                '.dui-table-cell',
                '[class*="cell"]:not([class*="formula"])',
                '[class*="table-cell"]',
                '[data-sheet-cell]',
                '.edit-area [class*="cell"]',
                '.spreadsheet [class*="cell"]',
                '[class*="grid-cell"]',
                '.table-container td'
            ],
            "table_containers": [
                '.dui-table',
                '[class*="table"]',
                '[class*="grid"]',
                '.edit-area',
                '#app'
            ]
        }
        
        if os.path.exists(selectors_file):
            try:
                with open(selectors_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return default_selectors
    
    def create_sample_config(self):
        """创建示例配置文件"""
        sample_config = AdvancedConfig()
        sample_file = "sample_config.json"
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(sample_config), f, indent=2, ensure_ascii=False)
        
        print(f"示例配置文件已创建: {sample_file}")
        print("您可以复制并修改此文件为 tencent_exporter_config.json")


class ExtensionRegistry:
    """扩展注册器 - 允许用户注册自定义提取器"""
    
    def __init__(self):
        self.custom_extractors = {}
        self.custom_selectors = {}
    
    def register_extractor(self, name: str, extractor_class):
        """注册自定义提取器"""
        self.custom_extractors[name] = extractor_class
        print(f"已注册自定义提取器: {name}")
    
    def register_selectors(self, name: str, selectors: list):
        """注册自定义选择器"""
        self.custom_selectors[name] = selectors
        print(f"已注册自定义选择器组: {name}")
    
    def get_extractor(self, name: str):
        """获取自定义提取器"""
        return self.custom_extractors.get(name)
    
    def get_selectors(self, name: str) -> list:
        """获取自定义选择器"""
        return self.custom_selectors.get(name, [])
    
    def list_extensions(self):
        """列出所有扩展"""
        print("已注册的扩展:")
        print(f"  自定义提取器: {list(self.custom_extractors.keys())}")
        print(f"  自定义选择器: {list(self.custom_selectors.keys())}")


# 全局实例
config_manager = ConfigManager()
extension_registry = ExtensionRegistry()


# 便捷函数
def get_config() -> AdvancedConfig:
    """获取当前配置"""
    return config_manager.config


def update_config(**kwargs):
    """更新配置"""
    config_manager.update_config(**kwargs)


def save_config():
    """保存配置"""
    config_manager.save_config()


# 使用示例
if __name__ == "__main__":
    print("腾讯文档导出器配置管理")
    print("-" * 30)
    
    # 显示当前配置
    current_config = get_config()
    print("当前配置:")
    for key, value in asdict(current_config).items():
        print(f"  {key}: {value}")
    
    # 创建示例配置
    config_manager.create_sample_config()
    
    # 显示扩展信息
    extension_registry.list_extensions()