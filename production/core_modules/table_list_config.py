#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表格列表配置
定义系统中所有可能参与对比的表格
"""

# 标准30个业务表格列表
STANDARD_BUSINESS_TABLES = [
    "小红书内容审核记录表",
    "小红书达人合作管理表", 
    "小红书品牌投放效果分析表",
    "小红书用户增长数据统计表",
    "小红书社区运营活动表",
    "小红书商业化收入明细表",
    "小红书内容创作者等级评定表",
    "小红书平台违规处理记录表",
    "员工绩效考核评估表",
    "部门预算执行情况表",
    "客户关系管理跟进表",
    "供应商资质审核记录表",
    "产品销售业绩统计表",
    "市场营销活动ROI分析表",
    "人力资源招聘进度表",
    "财务月度报表汇总表",
    "企业风险评估矩阵表",
    "合规检查问题跟踪表",
    "信息安全事件处理表",
    "法律风险识别评估表",
    "内控制度执行监督表",
    "供应链风险管控表",
    "数据泄露应急响应表",
    "审计发现问题整改表",
    "项目进度里程碑跟踪表",
    "项目资源分配计划表",
    "项目风险登记管理表",
    "项目质量检查评估表",
    "项目成本预算控制表",
    "项目团队成员考核表"
]

# 标准19个列名
STANDARD_COLUMN_NAMES = [
    "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
    "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
    "协助人", "监督人", "重要程度", "预计完成时间", "完成进度", 
    "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
]

# 表格分组（用于映射到热力图的不同区域）
TABLE_GROUPS = {
    "小红书业务": list(range(0, 8)),     # 前8个表格：小红书相关
    "企业管理": list(range(8, 16)),      # 中间8个：企业管理相关
    "风险合规": list(range(16, 24)),     # 第三组：风险合规相关
    "项目管理": list(range(24, 30))      # 最后6个：项目管理相关
}

def get_table_index(table_name: str) -> int:
    """
    根据表格名获取其在标准列表中的索引
    支持模糊匹配
    """
    # 精确匹配
    if table_name in STANDARD_BUSINESS_TABLES:
        return STANDARD_BUSINESS_TABLES.index(table_name)
    
    # 模糊匹配（包含关键词）
    for i, standard_name in enumerate(STANDARD_BUSINESS_TABLES):
        if table_name in standard_name or standard_name in table_name:
            return i
    
    # 关键词匹配
    keywords_map = {
        "出国销售": 2,  # 映射到"小红书品牌投放效果分析表"
        "回国销售": 3,  # 映射到"小红书用户增长数据统计表"
        "小红书部门": 0,  # 映射到"小红书内容审核记录表"
    }
    
    for keyword, index in keywords_map.items():
        if keyword in table_name:
            return index
    
    # 未找到匹配，返回-1
    return -1

def get_column_index(column_name: str) -> int:
    """
    根据列名获取其在标准列表中的索引
    """
    if column_name in STANDARD_COLUMN_NAMES:
        return STANDARD_COLUMN_NAMES.index(column_name)
    return -1