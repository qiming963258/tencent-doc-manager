#!/usr/bin/env python3
"""
强制使用W38基线文件进行对比
这是正确的做法：W38是旧版本，W39是新版本
真实差异只有十几处
"""

import os
import shutil
from pathlib import Path

def setup_correct_baselines():
    """配置正确的W38基线文件"""

    # W38基线（正确的旧版本）
    w38_baselines = {
        'tencent_出国销售计划表_20250915_0145_baseline_W38.csv':
            '/root/projects/tencent-doc-manager/csv_versions/2025_W38/baseline/tencent_出国销售计划表_20250915_0145_baseline_W38.csv',
        'tencent_小红书部门_20250915_0146_baseline_W38.csv':
            '/root/projects/tencent-doc-manager/csv_versions/2025_W38/baseline/tencent_小红书部门_20250915_0146_baseline_W38.csv'
    }

    # W39基线目录（错误地包含了新版本）
    w39_baseline_dir = Path('/root/projects/tencent-doc-manager/csv_versions/2025_W39/baseline')

    # 备份错误的W39基线
    backup_dir = w39_baseline_dir / 'backup_wrong'
    backup_dir.mkdir(exist_ok=True)

    for file in w39_baseline_dir.glob('*.csv'):
        if file.name not in ['tencent_111测试版本-出国销售计划表-工作表1_20250922_0134_baseline_W39.csv']:
            # 这些是我错误下载的新版本
            shutil.move(str(file), str(backup_dir / file.name))
            print(f"❌ 移除错误的基线: {file.name}")

    # 复制W38基线到W39目录（临时解决方案）
    for name, path in w38_baselines.items():
        if os.path.exists(path):
            # 创建W39版本的命名
            new_name = name.replace('_W38.csv', '_W39.csv')
            target = w39_baseline_dir / new_name

            # 如果目标不存在，复制过去
            if not target.exists():
                shutil.copy2(path, str(target))
                print(f"✅ 复制W38基线作为W39基线: {new_name}")
                print(f"   (这是旧版本，用于对比)")

    print("\n📊 基线配置完成:")
    print("- W38基线（旧版本）将用于对比")
    print("- 预期真实差异：约10-20处")
    print("- 如果显示1000+处差异，说明对比错误")

if __name__ == "__main__":
    setup_correct_baselines()

    # 显示当前基线状态
    print("\n📁 当前W39基线目录:")
    w39_dir = Path('/root/projects/tencent-doc-manager/csv_versions/2025_W39/baseline')
    for file in sorted(w39_dir.glob('*.csv')):
        size = file.stat().st_size / 1024
        print(f"  📄 {file.name} ({size:.1f} KB)")