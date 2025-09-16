import os
import re

def adapt_comprehensive_score_path(original_path):
    """
    将旧的comprehensive目录路径转换为新的按周存储的路径

    Args:
        original_path (str): 原始文件路径

    Returns:
        str: 新的文件路径
    """
    # 正则匹配周数
    week_match = re.search(r'comprehensive_score_W(\d+)', original_path)
    if not week_match:
        return original_path

    week_number = week_match.group(1)
    base_dir = "/root/projects/tencent-doc-manager/scoring_results"

    # 新路径格式：/base_dir/2025_W{week_number}/文件名
    old_filename = os.path.basename(original_path)
    new_path = os.path.join(base_dir, f"2025_W{week_number}", old_filename)

    return new_path

def find_latest_comprehensive_score(week_number=None):
    """
    查找指定周数或最新的综合打分文件

    Args:
        week_number (str, optional): 指定的周数，如 'W37'

    Returns:
        str: 最匹配的文件路径
    """
    base_dir = "/root/projects/tencent-doc-manager/scoring_results"

    # 如果没有指定周数，找最新的
    if week_number is None:
        all_dirs = [d for d in os.listdir(base_dir) if d.startswith('2025_W')]
        if not all_dirs:
            return None
        week_number = sorted(all_dirs, key=lambda x: int(x.split('W')[1]))[-1]

    week_dir = os.path.join(base_dir, f"2025_{week_number}")
    if not os.path.exists(week_dir):
        return None

    files = [f for f in os.listdir(week_dir) if f.startswith('comprehensive_score_')]
    if not files:
        return None

    # 返回最新的文件
    latest_file = sorted(files, key=lambda x: os.path.getmtime(os.path.join(week_dir, x)))[-1]
    return os.path.join(week_dir, latest_file)