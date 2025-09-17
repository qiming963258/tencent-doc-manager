#!/usr/bin/env python3
"""
配置中心包
提供统一的配置访问接口
"""

from .config_center import (
    ConfigCenter,
    get_config_center,
    get_config,
    get_standard_columns,
    get_column_level
)

from .column_definitions import (
    STANDARD_COLUMNS,
    COLUMN_IDS,
    COLUMN_TYPES,
    COLUMN_WIDTHS,
    COLUMN_ALIASES,
    get_column_index,
    get_column_by_index,
    normalize_column_name
)

from .risk_classification import (
    L1_COLUMNS,
    L2_COLUMNS,
    L3_COLUMNS,
    RISK_LEVELS,
    get_column_risk_level,
    get_risk_info,
    get_base_score
)

from .scoring_parameters import (
    COLUMN_WEIGHTS,
    BASE_SCORES,
    FORCE_THRESHOLDS,
    DIFFUSION_PARAMS,
    HEATMAP_COLOR_RANGES,
    get_column_weight,
    calculate_weighted_score,
    get_color_for_score
)

__all__ = [
    # 配置中心
    'ConfigCenter',
    'get_config_center',
    'get_config',
    'get_standard_columns',
    'get_column_level',

    # 列定义
    'STANDARD_COLUMNS',
    'COLUMN_IDS',
    'COLUMN_TYPES',
    'COLUMN_WIDTHS',
    'COLUMN_ALIASES',
    'get_column_index',
    'get_column_by_index',
    'normalize_column_name',

    # 风险分级
    'L1_COLUMNS',
    'L2_COLUMNS',
    'L3_COLUMNS',
    'RISK_LEVELS',
    'get_column_risk_level',
    'get_risk_info',
    'get_base_score',

    # 打分参数
    'COLUMN_WEIGHTS',
    'BASE_SCORES',
    'FORCE_THRESHOLDS',
    'DIFFUSION_PARAMS',
    'HEATMAP_COLOR_RANGES',
    'get_column_weight',
    'calculate_weighted_score',
    'get_color_for_score'
]

# 版本信息
__version__ = '1.0.0'
__author__ = '配置中心团队'
__date__ = '2025-09-17'