#!/usr/bin/env python3
"""
配置中心 - 统一配置管理系统
实现单一真相源（Single Source of Truth）架构
创建日期：2025-09-17
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigCenter:
    """
    统一配置中心 - 单例模式实现
    负责管理系统所有配置项，提供统一的访问接口
    """

    _instance = None
    _config_cache = {}
    _initialized = False

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ConfigCenter, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置中心"""
        if not self._initialized:
            self.config_dir = Path(__file__).parent
            self._load_all_configs()
            self._initialized = True

    def _load_all_configs(self):
        """加载所有配置文件"""
        try:
            # 加载列定义配置
            from .column_definitions import (
                STANDARD_COLUMNS,
                COLUMN_IDS,
                COLUMN_TYPES,
                COLUMN_WIDTHS,
                COLUMN_ALIASES
            )

            # 加载风险分级配置
            from .risk_classification import (
                L1_COLUMNS,
                L2_COLUMNS,
                L3_COLUMNS,
                RISK_LEVELS
            )

            # 加载打分参数配置
            from .scoring_parameters import (
                COLUMN_WEIGHTS,
                BASE_SCORES,
                FORCE_THRESHOLDS,
                DIFFUSION_PARAMS
            )

            # 存储到缓存
            self._config_cache = {
                # 列定义
                'standard_columns': STANDARD_COLUMNS,
                'column_ids': COLUMN_IDS,
                'column_types': COLUMN_TYPES,
                'column_widths': COLUMN_WIDTHS,
                'column_aliases': COLUMN_ALIASES,

                # 风险分级
                'l1_columns': L1_COLUMNS,
                'l2_columns': L2_COLUMNS,
                'l3_columns': L3_COLUMNS,
                'risk_levels': RISK_LEVELS,

                # 打分参数
                'column_weights': COLUMN_WEIGHTS,
                'base_scores': BASE_SCORES,
                'force_thresholds': FORCE_THRESHOLDS,
                'diffusion_params': DIFFUSION_PARAMS
            }

            logger.info("✅ 配置中心初始化成功")

        except ImportError as e:
            logger.error(f"❌ 配置加载失败: {e}")
            # 使用默认配置作为后备
            self._load_default_configs()

    def _load_default_configs(self):
        """加载默认配置（后备方案）"""
        logger.warning("⚠️ 使用默认配置")

        # 默认标准19列
        self._config_cache['standard_columns'] = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
            "完成链接", "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
        ]

        # 默认L1/L2/L3分类
        self._config_cache['l1_columns'] = [
            "来源", "任务发起时间", "目标对齐", "关键KR对齐",
            "重要程度", "预计完成时间", "完成进度"
        ]

        self._config_cache['l2_columns'] = [
            "项目类型", "具体计划内容", "邓总指导登记",
            "负责人", "协助人", "监督人"
        ]

        self._config_cache['l3_columns'] = [
            "序号", "完成链接", "经理分析复盘",
            "最新复盘时间", "对上汇报", "应用情况"
        ]

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        支持点号分隔的嵌套键访问，如 'columns.standard_columns'
        """
        keys = key.split('.')
        value = self._config_cache

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        # 返回副本避免外部修改
        if isinstance(value, (list, dict)):
            import copy
            return copy.deepcopy(value)

        return value

    def get_standard_columns(self) -> List[str]:
        """获取标准列定义"""
        return self.get('standard_columns', [])

    def get_column_level(self, column_name: str) -> str:
        """
        获取列的风险级别
        返回: 'L1', 'L2', 'L3'
        """
        # 处理列名别名
        column_aliases = self.get('column_aliases', {})
        column_name = column_aliases.get(column_name, column_name)

        if column_name in self.get('l1_columns', []):
            return 'L1'
        elif column_name in self.get('l2_columns', []):
            return 'L2'
        elif column_name in self.get('l3_columns', []):
            return 'L3'
        else:
            logger.warning(f"⚠️ 未知列名: {column_name}")
            return 'L3'  # 默认为L3

    def get_column_weight(self, column_name: str) -> float:
        """获取列的权重"""
        weights = self.get('column_weights', {})
        return weights.get(column_name, 1.0)  # 默认权重1.0

    def validate_columns(self, columns: List[str]) -> tuple[bool, List[str]]:
        """
        验证列名是否符合标准
        返回: (是否有效, 错误信息列表)
        """
        standard = self.get_standard_columns()
        errors = []

        if len(columns) != 19:
            errors.append(f"列数不正确：期望19列，实际{len(columns)}列")
            return False, errors

        # 处理别名
        column_aliases = self.get('column_aliases', {})

        for i, (std, actual) in enumerate(zip(standard, columns)):
            # 检查别名
            actual_normalized = column_aliases.get(actual, actual)
            if std != actual_normalized:
                errors.append(f"列{i}: 期望'{std}'，实际'{actual}'")

        return len(errors) == 0, errors

    def validate_config_consistency(self) -> bool:
        """验证配置一致性"""
        checks = []

        # 1. 列数量检查
        standard_columns = self.get_standard_columns()
        checks.append(len(standard_columns) == 19)

        # 2. L1/L2/L3完整性检查
        l1 = set(self.get('l1_columns', []))
        l2 = set(self.get('l2_columns', []))
        l3 = set(self.get('l3_columns', []))
        all_classified = l1.union(l2).union(l3)

        checks.append(len(all_classified) == 19)
        checks.append(len(l1.intersection(l2)) == 0)  # 无重复
        checks.append(len(l2.intersection(l3)) == 0)
        checks.append(len(l1.intersection(l3)) == 0)

        # 3. 所有分类列都在标准列中
        standard_set = set(standard_columns)
        checks.append(all_classified.issubset(standard_set))

        if not all(checks):
            logger.error("❌ 配置一致性验证失败")
            return False

        logger.info("✅ 配置一致性验证通过")
        return True

    def reload(self, config_type: Optional[str] = None):
        """重新加载配置"""
        logger.info(f"🔄 重新加载配置: {config_type or '全部'}")
        self._load_all_configs()
        self.validate_config_consistency()

    def get_config_stats(self) -> Dict[str, Any]:
        """获取配置统计信息"""
        return {
            "total_columns": len(self.get_standard_columns()),
            "l1_columns": len(self.get('l1_columns', [])),
            "l2_columns": len(self.get('l2_columns', [])),
            "l3_columns": len(self.get('l3_columns', [])),
            "weighted_columns": len(self.get('column_weights', {})),
            "config_items": len(self._config_cache)
        }


# 全局配置中心实例
_config_center = None


def get_config_center() -> ConfigCenter:
    """获取配置中心单例实例"""
    global _config_center
    if _config_center is None:
        _config_center = ConfigCenter()
    return _config_center


# 便捷访问函数
def get_config(key: str, default: Any = None) -> Any:
    """便捷的配置访问函数"""
    return get_config_center().get(key, default)


def get_standard_columns() -> List[str]:
    """获取标准列定义"""
    return get_config_center().get_standard_columns()


def get_column_level(column: str) -> str:
    """获取列的风险级别"""
    return get_config_center().get_column_level(column)


if __name__ == "__main__":
    # 测试配置中心
    config = get_config_center()

    print("📋 配置中心测试")
    print("=" * 60)

    # 显示配置统计
    stats = config.get_config_stats()
    print("\n📊 配置统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 验证配置一致性
    print("\n🔍 配置一致性验证:")
    config.validate_config_consistency()

    print("\n✅ 配置中心就绪")