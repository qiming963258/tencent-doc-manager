#!/usr/bin/env python3
"""
虚拟测试文件隔离脚本
将所有虚拟测试文件移动到隔离目录，禁止在生产流程中使用
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class VirtualFileIsolator:
    """虚拟文件隔离器"""

    def __init__(self):
        self.project_root = Path('/root/projects/tencent-doc-manager')
        self.quarantine_dir = self.project_root / '.quarantine_virtual'
        self.quarantine_dir.mkdir(exist_ok=True)

        # 虚拟文件特征
        self.virtual_patterns = [
            '*test*123*',
            '*fake*',
            '*mock*',
            '*demo*',
            '*virtual*',
            '*dummy*',
            'test_*.csv',
            'test_*.json',
            '*_test_data.*',
            'detailed_scores_*' # 包含测试打分数据
        ]

        # 排除目录
        self.exclude_dirs = {
            '.git',
            '__pycache__',
            '.quarantine_virtual',
            'node_modules',
            '.venv'
        }

    def find_virtual_files(self):
        """查找所有虚拟测试文件"""
        virtual_files = []

        for pattern in self.virtual_patterns:
            for file_path in self.project_root.rglob(pattern):
                # 跳过排除目录
                if any(exclude in str(file_path) for exclude in self.exclude_dirs):
                    continue

                # 跳过目录，只处理文件
                if file_path.is_file():
                    # 特别检查：包含测试数据的详细打分文件
                    if 'detailed_scores' in file_path.name:
                        # 检查是否是测试数据（只有5个单元格）
                        try:
                            import json
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                                cell_scores = data.get('cell_scores', {})
                                # 如果只有5个或更少的变更，可能是测试数据
                                if len(cell_scores) <= 5:
                                    virtual_files.append(file_path)
                        except:
                            pass
                    else:
                        virtual_files.append(file_path)

        return list(set(virtual_files))  # 去重

    def isolate_files(self, dry_run=True):
        """隔离虚拟文件"""
        virtual_files = self.find_virtual_files()

        print(f"\n{'='*60}")
        print(f"🚫 虚拟文件隔离报告")
        print(f"{'='*60}")
        print(f"\n📊 发现 {len(virtual_files)} 个虚拟测试文件")

        if dry_run:
            print("\n⚠️  DRY RUN 模式 - 仅显示将要隔离的文件")
            print("    使用 --execute 参数执行实际隔离\n")

        isolated_count = 0
        for file_path in virtual_files:
            rel_path = file_path.relative_to(self.project_root)

            if dry_run:
                print(f"  📄 {rel_path}")
            else:
                # 创建隔离目录结构
                quarantine_path = self.quarantine_dir / rel_path
                quarantine_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    # 移动文件到隔离区
                    shutil.move(str(file_path), str(quarantine_path))
                    print(f"  ✅ 已隔离: {rel_path}")
                    isolated_count += 1
                except Exception as e:
                    print(f"  ❌ 隔离失败: {rel_path} - {e}")

        if not dry_run:
            print(f"\n✅ 成功隔离 {isolated_count} 个文件")
            print(f"📁 隔离目录: {self.quarantine_dir}")

            # 创建隔离记录
            record_file = self.quarantine_dir / f"isolation_record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(record_file, 'w') as f:
                f.write(f"隔离时间: {datetime.now()}\n")
                f.write(f"隔离文件数: {isolated_count}\n")
                f.write("\n文件列表:\n")
                for file_path in virtual_files:
                    f.write(f"  {file_path.relative_to(self.project_root)}\n")

            print(f"📝 隔离记录: {record_file.name}")

    def create_safeguard(self):
        """创建安全保护机制"""
        safeguard_file = self.project_root / 'VIRTUAL_FILES_PROHIBITED.md'

        content = """# ⚠️ 虚拟测试文件禁用声明

## 生效日期：2025-09-21

### 🚫 禁止事项
1. **禁止创建虚拟测试数据文件**
2. **禁止使用fake/mock/demo等命名**
3. **禁止硬编码测试数据**
4. **禁止使用非真实下载的CSV/XLSX文件**

### ✅ 正确做法
1. **只使用真实下载的腾讯文档**
2. **通过完整链路生成的数据**
3. **基于实际CSV对比的打分文件**

### 🔒 安全机制
- 所有虚拟文件已移至 `.quarantine_virtual/` 目录
- 系统将拒绝加载隔离目录中的文件
- 定期检查并清理新的虚拟文件

### 📋 检查命令
```bash
python3 isolate_virtual_files.py --check
```

### ⚡ 紧急恢复
如需恢复某个文件（仅限紧急情况）：
```bash
cp .quarantine_virtual/path/to/file original/path/
```

---
此文件由系统自动生成，请勿删除。
"""

        with open(safeguard_file, 'w') as f:
            f.write(content)

        print(f"\n📄 已创建安全保护文件: {safeguard_file.name}")


def main():
    """主函数"""
    import sys

    isolator = VirtualFileIsolator()

    if '--execute' in sys.argv:
        print("🔴 执行实际隔离操作...")
        isolator.isolate_files(dry_run=False)
        isolator.create_safeguard()
    elif '--check' in sys.argv:
        virtual_files = isolator.find_virtual_files()
        if virtual_files:
            print(f"⚠️  发现 {len(virtual_files)} 个虚拟测试文件需要隔离")
            print("运行 python3 isolate_virtual_files.py --execute 执行隔离")
        else:
            print("✅ 未发现虚拟测试文件")
    else:
        isolator.isolate_files(dry_run=True)
        print("\n提示：使用 --execute 参数执行实际隔离")


if __name__ == "__main__":
    main()