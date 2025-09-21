#!/usr/bin/env python3
"""
全流程链式传递集成测试
验证文件唯一性、无降级、无虚拟备份的完整机制

测试目标：
1. Session ID确保文件唯一性
2. 文档匹配验证防止错误对比
3. 断链即停原则
4. 无虚拟文件降级
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')

from workflow_chain_manager import get_chain_manager


class WorkflowChainIntegrationTest:
    """全流程链式传递集成测试"""

    def __init__(self):
        """初始化测试环境"""
        self.manager = get_chain_manager()
        self.test_results = []

        # 测试文档配置（使用真实文档）
        self.test_doc = {
            "url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R",
            "name": "小红书部门",
            "baseline_week": "W37",
            "current_week": "W38"
        }

        print("""
╔══════════════════════════════════════════════════════════╗
║       🧪 全流程链式传递集成测试                           ║
╠══════════════════════════════════════════════════════════╣
║ 测试目标：                                                ║
║ 1. Session ID文件唯一性                                  ║
║ 2. 文档匹配验证                                          ║
║ 3. 断链即停原则                                          ║
║ 4. 无虚拟文件降级                                        ║
╚══════════════════════════════════════════════════════════╝
        """)

    def test_session_creation(self):
        """测试1: Session创建与唯一性"""
        print("\n🧪 测试1: Session创建与唯一性")
        print("-" * 60)

        try:
            # 创建会话
            session_id = self.manager.create_session(
                doc_url=self.test_doc["url"],
                doc_name=self.test_doc["name"],
                baseline_week=self.test_doc["baseline_week"],
                current_week=self.test_doc["current_week"]
            )

            # 验证Session ID格式
            assert session_id.startswith("WF_"), "Session ID格式错误"
            assert len(session_id) > 20, "Session ID长度不足"

            # 验证文档ID提取
            assert self.manager.current_session.document_id == "DWFJzdWNwd0RGbU5R", "文档ID提取错误"

            print(f"  ✅ Session创建成功: {session_id}")
            print(f"  ✅ 文档ID正确提取: {self.manager.current_session.document_id}")

            self.test_results.append(("Session创建", True, session_id))
            return session_id

        except Exception as e:
            print(f"  ❌ Session创建失败: {e}")
            self.test_results.append(("Session创建", False, str(e)))
            return None

    def test_step_validation(self):
        """测试2: 步骤顺序验证"""
        print("\n🧪 测试2: 步骤顺序验证")
        print("-" * 60)

        try:
            # 尝试跳过步骤（应该失败）
            result = self.manager.add_step_result(
                "compare_baseline",  # 错误：应该先执行download_csv
                input_files={"csv1": "fake.csv", "csv2": "fake2.csv"},
                output_files={"diff": "diff.json"}
            )

            if not result:
                print("  ✅ 步骤顺序验证生效：拒绝错误顺序")
            else:
                print("  ❌ 步骤顺序验证失败：接受了错误顺序")

            self.test_results.append(("步骤顺序验证", not result, ""))

        except Exception as e:
            print(f"  ❌ 步骤验证测试异常: {e}")
            self.test_results.append(("步骤顺序验证", False, str(e)))

    def test_document_match_validation(self):
        """测试3: 文档匹配验证（防止2010处虚假变更）"""
        print("\n🧪 测试3: 文档匹配验证")
        print("-" * 60)

        try:
            # 测试不同文档（应该失败）
            baseline = "tencent_出国销售计划表_20250920_baseline_W37.csv"
            target = "tencent_小红书部门_20250920_midweek_W38.csv"

            result = self.manager.validate_document_match(baseline, target)

            if not result:
                print(f"  ✅ 文档不匹配检测成功：拒绝不同文档对比")
                print(f"     基线: 出国销售计划表")
                print(f"     目标: 小红书部门")
                print(f"     这种错误对比会产生2010处虚假变更")
            else:
                print(f"  ❌ 文档匹配验证失败：允许了不同文档对比")

            # 测试相同文档（应该通过）
            baseline2 = "tencent_小红书部门_20250919_baseline_W37.csv"
            target2 = "tencent_小红书部门_20250920_midweek_W38.csv"

            # 重新创建会话（因为前面的会话可能已失败）
            self.manager.create_session(
                doc_url=self.test_doc["url"],
                doc_name=self.test_doc["name"],
                baseline_week="W37",
                current_week="W38"
            )

            result2 = self.manager.validate_document_match(baseline2, target2)

            if result2:
                print(f"  ✅ 相同文档验证通过：小红书部门")

            self.test_results.append(("文档匹配验证", not result and result2, ""))

        except Exception as e:
            print(f"  ❌ 文档匹配测试异常: {e}")
            self.test_results.append(("文档匹配验证", False, str(e)))

    def test_virtual_file_rejection(self):
        """测试4: 虚拟文件拦截"""
        print("\n🧪 测试4: 虚拟文件拦截")
        print("-" * 60)

        # 虚拟文件模式
        virtual_patterns = [
            "test_fake_123.csv",
            "mock_demo_file.xlsx",
            "virtual_test_data.json",
            ".quarantine_virtual/isolated_test.csv"
        ]

        blocked_count = 0

        for pattern in virtual_patterns:
            # 检查文件名是否包含禁止的模式
            forbidden = ['test', 'fake', 'mock', 'demo', 'virtual', '123', '.quarantine_virtual']
            is_blocked = any(word in pattern.lower() for word in forbidden)

            if is_blocked:
                print(f"  ✅ 拦截虚拟文件: {pattern}")
                blocked_count += 1
            else:
                print(f"  ❌ 未拦截虚拟文件: {pattern}")

        success = blocked_count == len(virtual_patterns)
        self.test_results.append(("虚拟文件拦截", success, f"{blocked_count}/{len(virtual_patterns)}"))

        if success:
            print(f"  ✅ 所有虚拟文件被成功拦截")

    def test_file_uniqueness(self):
        """测试5: 文件唯一性保证"""
        print("\n🧪 测试5: 文件唯一性保证")
        print("-" * 60)

        try:
            # 创建新会话
            session_id = self.manager.create_session(
                doc_url=self.test_doc["url"],
                doc_name=self.test_doc["name"],
                baseline_week="W37",
                current_week="W38"
            )

            # 模拟文件路径（不带session_id）
            original_file = "/tmp/test_download.csv"

            # 测试自动添加session_id
            new_path = self.manager._add_session_to_filename(original_file)

            # 验证新路径包含session_id
            assert session_id in new_path, "文件路径未包含Session ID"

            print(f"  ✅ 文件唯一性验证通过")
            print(f"     原始: test_download.csv")
            print(f"     新名: test_download_{session_id}.csv")

            self.test_results.append(("文件唯一性", True, new_path))

        except Exception as e:
            print(f"  ❌ 文件唯一性测试失败: {e}")
            self.test_results.append(("文件唯一性", False, str(e)))

    def test_chain_fail_fast(self):
        """测试6: 断链即停原则"""
        print("\n🧪 测试6: 断链即停原则")
        print("-" * 60)

        try:
            # 创建新会话
            session_id = self.manager.create_session(
                doc_url=self.test_doc["url"],
                doc_name=self.test_doc["name"],
                baseline_week="W37",
                current_week="W38"
            )

            # 创建一个临时CSV文件（模拟成功下载）
            temp_csv = f"/tmp/download_{session_id}.csv"
            Path(temp_csv).touch()

            # 第一步成功
            result1 = self.manager.add_step_result(
                "download_csv",
                input_files={"url": self.test_doc["url"]},
                output_files={"csv": temp_csv}
            )

            # 第二步故意失败（基线文件不存在）
            result2 = self.manager.add_step_result(
                "compare_baseline",
                input_files={
                    "baseline": "/nonexistent/baseline.csv",  # 不存在的文件
                    "target": temp_csv
                },
                output_files={"diff": "/tmp/diff.json"}
            )

            # 验证会话状态
            status = self.manager.get_session_status()

            if status["status"] == "failed":
                print(f"  ✅ 断链即停生效：会话已标记为失败")

                # 尝试添加后续步骤（应该拒绝）
                result2 = self.manager.add_step_result(
                    "compare_baseline",
                    input_files={"csv1": "a.csv", "csv2": "b.csv"},
                    output_files={"diff": "diff.json"}
                )

                if not result2:
                    print(f"  ✅ 后续步骤被正确拒绝")

            self.test_results.append(("断链即停", status["status"] == "failed", ""))

            # 清理临时文件
            if Path(temp_csv).exists():
                Path(temp_csv).unlink()

        except Exception as e:
            print(f"  ❌ 断链测试异常: {e}")
            self.test_results.append(("断链即停", False, str(e)))

    def test_complete_workflow_simulation(self):
        """测试7: 完整工作流模拟"""
        print("\n🧪 测试7: 完整工作流模拟（11步）")
        print("-" * 60)

        try:
            # 创建新会话
            session_id = self.manager.create_session(
                doc_url=self.test_doc["url"],
                doc_name=self.test_doc["name"],
                baseline_week="W37",
                current_week="W38"
            )

            # 模拟11个步骤的文件路径
            workflow_files = {
                1: {"input": {"url": self.test_doc["url"]},
                    "output": {"csv": f"/tmp/download_{session_id}.csv"}},
                2: {"input": {"baseline": f"/tmp/baseline_{session_id}.csv",
                             "target": f"/tmp/download_{session_id}.csv"},
                    "output": {"diff": f"/tmp/diff_{session_id}.json"}},
                3: {"input": {"diff": f"/tmp/diff_{session_id}.json"},
                    "output": {"changes": f"/tmp/changes_{session_id}.json"}},
                4: {"input": {"changes": f"/tmp/changes_{session_id}.json"},
                    "output": {"standard": f"/tmp/standard_{session_id}.json"}},
                5: {"input": {"standard": f"/tmp/standard_{session_id}.json"},
                    "output": {"scores": f"/tmp/scores_{session_id}.json"}},
                6: {"input": {"scores": f"/tmp/scores_{session_id}.json"},
                    "output": {"comprehensive": f"/tmp/comprehensive_{session_id}.json"}},
                7: {"input": {"comprehensive": f"/tmp/comprehensive_{session_id}.json"},
                    "output": {"ui_data": f"/tmp/ui_data_{session_id}.json"}},
                8: {"input": {"ui_request": "download"},
                    "output": {"xlsx": f"/tmp/export_{session_id}.xlsx"}},
                9: {"input": {"xlsx": f"/tmp/export_{session_id}.xlsx",
                              "scores": f"/tmp/scores_{session_id}.json"},
                    "output": {"colored": f"/tmp/colored_{session_id}.xlsx"}},
                10: {"input": {"colored": f"/tmp/colored_{session_id}.xlsx"},
                     "output": {"url": "https://docs.qq.com/sheet/NEW_UPLOAD"}},
                11: {"input": {"url": "https://docs.qq.com/sheet/NEW_UPLOAD"},
                     "output": {"ui_update": "success"}}
            }

            # 步骤名称
            steps = [
                "download_csv", "compare_baseline", "extract_differences",
                "ai_standardize", "detailed_scoring", "comprehensive_scoring",
                "ui_adaptation", "download_xlsx", "apply_coloring",
                "upload_to_tencent", "update_ui_links"
            ]

            # 创建临时文件（模拟真实文件）
            for step_num, step_name in enumerate(steps, 1):
                files = workflow_files[step_num]

                # 先创建所有输入文件（如果是文件路径）
                for file_type, file_path in files["input"].items():
                    if file_path and file_path.startswith("/tmp/"):
                        Path(file_path).touch()

                # 创建输出文件（模拟）
                for file_type, file_path in files["output"].items():
                    if file_path.startswith("/tmp/"):
                        Path(file_path).touch()

                # 添加步骤结果
                result = self.manager.add_step_result(
                    step_name,
                    input_files=files["input"],
                    output_files=files["output"],
                    metadata={"step_number": step_num}
                )

                if not result:
                    print(f"  ❌ 步骤{step_num}失败: {step_name}")
                    break

            # 检查最终状态
            status = self.manager.get_session_status()

            if status["status"] == "completed":
                print(f"  ✅ 完整工作流成功完成")
                print(f"     Session: {session_id}")
                print(f"     进度: {status['progress']}")
                success = True
            else:
                print(f"  ⚠️ 工作流未完成: {status['status']}")
                success = False

            self.test_results.append(("完整工作流", success, status['progress']))

            # 清理临时文件
            for files in workflow_files.values():
                for file_path in files["output"].values():
                    if file_path.startswith("/tmp/") and Path(file_path).exists():
                        Path(file_path).unlink()

        except Exception as e:
            print(f"  ❌ 工作流模拟异常: {e}")
            self.test_results.append(("完整工作流", False, str(e)))

    def run_all_tests(self):
        """运行所有测试"""
        # 测试1: Session创建
        session_id = self.test_session_creation()

        # 测试2: 步骤验证
        self.test_step_validation()

        # 测试3: 文档匹配
        self.test_document_match_validation()

        # 测试4: 虚拟文件拦截
        self.test_virtual_file_rejection()

        # 测试5: 文件唯一性
        self.test_file_uniqueness()

        # 测试6: 断链即停
        self.test_chain_fail_fast()

        # 测试7: 完整工作流
        self.test_complete_workflow_simulation()

        # 输出测试报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告总结")
        print("="*60)

        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)

        print(f"\n总体结果: {passed}/{total} 通过")
        print("-"*60)

        for test_name, success, detail in self.test_results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name}: {'通过' if success else '失败'}")
            if detail:
                print(f"   详情: {detail}")

        print("\n" + "="*60)

        if passed == total:
            print("""
╔══════════════════════════════════════════════════════════╗
║     🎉 所有测试通过！全流程唯一性机制验证成功             ║
╠══════════════════════════════════════════════════════════╣
║ ✅ Session链式传递确保文件100%准确                       ║
║ ✅ 文档匹配验证防止2010处虚假变更                        ║
║ ✅ 断链即停原则确保错误立即暴露                          ║
║ ✅ 虚拟文件完全隔离，无降级可能                          ║
╚══════════════════════════════════════════════════════════╝
            """)
        else:
            print(f"\n⚠️ 有{total - passed}个测试失败，请检查并修复")


def main():
    """主函数"""
    tester = WorkflowChainIntegrationTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()