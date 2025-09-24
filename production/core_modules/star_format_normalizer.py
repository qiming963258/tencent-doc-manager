#!/usr/bin/env python3
"""
星级格式标准化模块
处理腾讯文档导出中星级符号与数字的格式差异
"""

import re
from typing import Any, Dict, List

class StarFormatNormalizer:
    """星级格式标准化器"""

    # 星级到数字的映射
    STAR_TO_NUMBER = {
        '★★★★★': '5',
        '★★★★☆': '4',
        '★★★☆☆': '3',
        '★★☆☆☆': '2',
        '★☆☆☆☆': '1',
        '☆☆☆☆☆': '0'
    }

    # 数字到星级的映射
    NUMBER_TO_STAR = {v: k for k, v in STAR_TO_NUMBER.items()}

    @classmethod
    def normalize_to_number(cls, value: Any) -> str:
        """将星级格式转换为数字"""
        if value is None:
            return ''

        value_str = str(value).strip()

        # 如果已经是数字，直接返回
        if value_str.isdigit() and 0 <= int(value_str) <= 5:
            return value_str

        # 如果是星级格式，转换为数字
        if '★' in value_str or '☆' in value_str:
            # 计算实心星和空心星数量
            filled_stars = value_str.count('★')
            empty_stars = value_str.count('☆')

            # 根据实心星数量返回对应数字
            if filled_stars + empty_stars == 5:
                return str(filled_stars)

            # 尝试直接映射
            return cls.STAR_TO_NUMBER.get(value_str, value_str)

        return value_str

    @classmethod
    def normalize_to_star(cls, value: Any) -> str:
        """将数字转换为星级格式"""
        if value is None:
            return ''

        value_str = str(value).strip()

        # 如果已经是星级格式，直接返回
        if '★' in value_str or '☆' in value_str:
            return value_str

        # 如果是数字，转换为星级
        if value_str.isdigit() and 0 <= int(value_str) <= 5:
            num = int(value_str)
            return '★' * num + '☆' * (5 - num)

        return value_str

    @classmethod
    def is_star_format(cls, value: Any) -> bool:
        """检查是否为星级格式"""
        if value is None:
            return False
        value_str = str(value)
        return '★' in value_str or '☆' in value_str

    @classmethod
    def is_number_format(cls, value: Any) -> bool:
        """检查是否为数字格式（0-5）"""
        if value is None:
            return False
        value_str = str(value).strip()
        return value_str.isdigit() and 0 <= int(value_str) <= 5

    @classmethod
    def are_equivalent(cls, value1: Any, value2: Any) -> bool:
        """检查两个值是否在语义上相等（忽略格式差异）"""
        # 都转换为数字进行比较
        norm1 = cls.normalize_to_number(value1)
        norm2 = cls.normalize_to_number(value2)
        return norm1 == norm2

    @classmethod
    def normalize_csv_data(cls, data: List[Dict], columns_to_normalize: List[str] = None) -> List[Dict]:
        """
        标准化CSV数据中的星级列

        Args:
            data: CSV数据（字典列表）
            columns_to_normalize: 需要标准化的列名列表，默认为['重要程度']

        Returns:
            标准化后的数据
        """
        if columns_to_normalize is None:
            columns_to_normalize = ['重要程度']

        normalized_data = []
        for row in data:
            normalized_row = row.copy()
            for col in columns_to_normalize:
                if col in normalized_row:
                    normalized_row[col] = cls.normalize_to_number(normalized_row[col])
            normalized_data.append(normalized_row)

        return normalized_data

    @classmethod
    def filter_format_changes(cls, modifications: List[Dict]) -> tuple:
        """
        过滤出真正的内容变更（排除纯格式变化）

        Args:
            modifications: 变更列表

        Returns:
            (真正的变更列表, 仅格式变更列表)
        """
        real_changes = []
        format_only_changes = []

        for mod in modifications:
            old_value = mod.get('old', '')
            new_value = mod.get('new', '')

            if cls.are_equivalent(old_value, new_value):
                # 仅格式变化
                format_only_changes.append(mod)
            else:
                # 真正的内容变更
                real_changes.append(mod)

        return real_changes, format_only_changes


def test_normalizer():
    """测试标准化器"""
    print("=" * 60)
    print("测试星级格式标准化器")
    print("=" * 60)

    test_cases = [
        ('★★★★★', '5'),
        ('★★★★☆', '4'),
        ('★★★☆☆', '3'),
        ('5', '★★★★★'),
        ('4', '★★★★☆'),
    ]

    print("\n📊 转换测试:")
    for star_val, num_val in test_cases:
        to_num = StarFormatNormalizer.normalize_to_number(star_val)
        to_star = StarFormatNormalizer.normalize_to_star(num_val)
        equiv = StarFormatNormalizer.are_equivalent(star_val, num_val)

        print(f"  {star_val} → 数字: {to_num}")
        print(f"  {num_val} → 星级: {to_star}")
        print(f"  等价性: {equiv}")
        print()

    # 测试变更过滤
    print("\n🔍 变更过滤测试:")
    test_mods = [
        {'cell': 'L4', 'old': '★★★★★', 'new': '5'},  # 仅格式
        {'cell': 'L5', 'old': '★★★★☆', 'new': '3'},  # 真实变更
        {'cell': 'L6', 'old': '★★★☆☆', 'new': '3'},  # 仅格式
    ]

    real, format_only = StarFormatNormalizer.filter_format_changes(test_mods)
    print(f"  真实变更: {len(real)} 处")
    print(f"  格式变更: {len(format_only)} 处")

    for change in real:
        print(f"    - {change['cell']}: {change['old']} → {change['new']} (内容变化)")

    for change in format_only:
        print(f"    - {change['cell']}: {change['old']} → {change['new']} (仅格式)")


if __name__ == "__main__":
    test_normalizer()