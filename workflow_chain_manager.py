#!/usr/bin/env python3
"""
全流程链式传递管理器
确保文件唯一性、无降级、无虚拟备份的完整传递机制

设计理念：
1. 每个工作流创建唯一的Session ID
2. 每步输出包含完整的前步信息
3. 文档ID验证确保对比正确性
4. 任何环节失败立即停止，不降级
5. 所有文件使用Session ID命名，避免查找错误
"""

import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
import traceback


@dataclass
class WorkflowSession:
    """工作流会话数据结构"""
    session_id: str                    # 唯一会话ID
    created_at: str                    # 创建时间
    document_id: str                   # 文档ID（从URL提取）
    document_name: str                 # 文档名称
    baseline_week: str                 # 基线周数
    current_week: str                  # 当前周数
    status: str                        # 状态：running/completed/failed
    current_step: int                  # 当前步骤
    chain: List[Dict[str, Any]]        # 完整链路记录


class WorkflowChainManager:
    """
    工作流链式传递管理器
    负责管理11步完整链路的文件传递
    """

    def __init__(self):
        self.project_root = Path('/root/projects/tencent-doc-manager')
        self.session_dir = self.project_root / 'workflow_sessions'
        self.session_dir.mkdir(exist_ok=True)

        # 当前会话
        self.current_session: Optional[WorkflowSession] = None

        # 步骤定义
        self.steps = [
            "download_csv",           # 1. 下载CSV/XLSX
            "compare_baseline",       # 2. 基线对比
            "extract_differences",    # 3. 提取差异
            "ai_standardize",        # 4. AI标准化
            "detailed_scoring",      # 5. 详细打分
            "comprehensive_scoring",  # 6. 综合打分
            "ui_adaptation",         # 7. UI适配
            "download_xlsx",         # 8. 下载XLSX
            "apply_coloring",        # 9. 应用涂色
            "upload_to_tencent",     # 10. 上传腾讯
            "update_ui_links"        # 11. 更新UI链接
        ]

    def extract_document_id(self, url: str) -> str:
        """从URL提取文档ID"""
        # https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R
        import re
        match = re.search(r'/sheet/([A-Za-z0-9]+)', url)
        if match:
            return match.group(1)
        raise ValueError(f"无法从URL提取文档ID: {url}")

    def create_session(self, doc_url: str, doc_name: str, baseline_week: str, current_week: str) -> str:
        """
        创建新的工作流会话

        Args:
            doc_url: 腾讯文档URL
            doc_name: 文档名称
            baseline_week: 基线周数(如W37)
            current_week: 当前周数(如W38)

        Returns:
            session_id: 唯一会话ID
        """
        session_id = f"WF_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        document_id = self.extract_document_id(doc_url)

        self.current_session = WorkflowSession(
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            document_id=document_id,
            document_name=doc_name,
            baseline_week=baseline_week,
            current_week=current_week,
            status="running",
            current_step=0,
            chain=[]
        )

        # 保存会话文件
        self._save_session()

        print(f"""
╔══════════════════════════════════════════════════════════╗
║          🚀 新工作流会话已创建                            ║
╠══════════════════════════════════════════════════════════╣
║ Session ID: {session_id:<45} ║
║ 文档ID:     {document_id:<45} ║
║ 文档名称:   {doc_name:<45} ║
║ 基线周:     {baseline_week:<45} ║
║ 当前周:     {current_week:<45} ║
╚══════════════════════════════════════════════════════════╝
        """)

        return session_id

    def add_step_result(self, step_name: str, input_files: Dict[str, str],
                       output_files: Dict[str, str], metadata: Dict[str, Any] = None) -> bool:
        """
        添加步骤执行结果到链路

        Args:
            step_name: 步骤名称
            input_files: 输入文件路径字典
            output_files: 输出文件路径字典
            metadata: 额外元数据

        Returns:
            成功返回True，失败返回False并停止链路
        """
        if not self.current_session:
            raise RuntimeError("没有活动的工作流会话")

        if self.current_session.status == "failed":
            print(f"❌ 工作流已失败，拒绝添加步骤: {step_name}")
            return False

        # 验证步骤顺序
        expected_step = self.steps[self.current_session.current_step]
        if step_name != expected_step:
            self._fail_session(f"步骤顺序错误: 期望{expected_step}, 实际{step_name}")
            return False

        # 验证输入文件存在（跳过URL）
        for file_type, file_path in input_files.items():
            if file_path and not file_path.startswith(('http://', 'https://')):
                if not Path(file_path).exists():
                    self._fail_session(f"输入文件不存在: {file_type}={file_path}")
                    return False

        # 验证输出文件包含session_id
        for file_type, file_path in output_files.items():
            if file_path and self.current_session.session_id not in str(file_path):
                # 重命名文件以包含session_id
                new_path = self._add_session_to_filename(file_path)
                output_files[file_type] = new_path

        # 记录步骤
        step_record = {
            "step": step_name,
            "step_number": self.current_session.current_step + 1,
            "timestamp": datetime.now().isoformat(),
            "input_files": input_files,
            "output_files": output_files,
            "metadata": metadata or {},
            "checksum": self._calculate_checksums(output_files)
        }

        self.current_session.chain.append(step_record)
        self.current_session.current_step += 1

        # 保存会话
        self._save_session()

        print(f"✅ 步骤 {self.current_session.current_step}/{len(self.steps)}: {step_name} 完成")

        # 检查是否完成所有步骤
        if self.current_session.current_step == len(self.steps):
            self.current_session.status = "completed"
            self._save_session()
            print("🎉 工作流完成！")

        return True

    def get_previous_output(self, step_back: int = 1) -> Dict[str, str]:
        """
        获取前N步的输出文件

        Args:
            step_back: 向前回溯的步数

        Returns:
            输出文件字典
        """
        if not self.current_session:
            raise RuntimeError("没有活动的工作流会话")

        if len(self.current_session.chain) < step_back:
            raise ValueError(f"链路中只有{len(self.current_session.chain)}步，无法回溯{step_back}步")

        return self.current_session.chain[-step_back]["output_files"]

    def validate_document_match(self, baseline_file: str, target_file: str) -> bool:
        """
        验证基线和目标文件是否属于同一文档

        Args:
            baseline_file: 基线文件路径
            target_file: 目标文件路径

        Returns:
            匹配返回True，不匹配返回False并失败会话
        """
        # 从文件名提取文档名
        baseline_name = Path(baseline_file).stem.split('_')[1]  # tencent_文档名_...
        target_name = Path(target_file).stem.split('_')[1]

        if baseline_name != target_name:
            self._fail_session(
                f"文档不匹配！基线:{baseline_name} vs 目标:{target_name}\n"
                f"这会导致虚假的变更检测（如2010处假变更）"
            )
            return False

        print(f"✅ 文档匹配验证通过: {baseline_name}")
        return True

    def _add_session_to_filename(self, file_path: str) -> str:
        """为文件名添加session_id"""
        path = Path(file_path)
        new_name = f"{path.stem}_{self.current_session.session_id}{path.suffix}"
        new_path = path.parent / new_name

        # 重命名文件
        if path.exists():
            path.rename(new_path)
            print(f"  📝 文件重命名: {path.name} → {new_name}")

        return str(new_path)

    def _calculate_checksums(self, files: Dict[str, str]) -> Dict[str, str]:
        """计算文件校验和"""
        checksums = {}
        for file_type, file_path in files.items():
            if file_path and Path(file_path).exists():
                with open(file_path, 'rb') as f:
                    checksums[file_type] = hashlib.md5(f.read()).hexdigest()[:8]
        return checksums

    def _save_session(self):
        """保存会话到文件"""
        if not self.current_session:
            return

        session_file = self.session_dir / f"{self.current_session.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.current_session), f, ensure_ascii=False, indent=2)

    def _fail_session(self, reason: str):
        """标记会话失败"""
        if self.current_session:
            self.current_session.status = "failed"
            self.current_session.chain.append({
                "error": reason,
                "timestamp": datetime.now().isoformat(),
                "step": self.steps[self.current_session.current_step] if self.current_session.current_step < len(self.steps) else "unknown",
                "traceback": traceback.format_exc()
            })
            self._save_session()

            print(f"""
╔══════════════════════════════════════════════════════════╗
║          ❌ 工作流失败                                    ║
╠══════════════════════════════════════════════════════════╣
║ Session: {self.current_session.session_id:<48} ║
║ 步骤:    {self.current_session.current_step}/{len(self.steps):<48} ║
║ 原因:    {reason[:48]:<48} ║
╚══════════════════════════════════════════════════════════╝
            """)

    def load_session(self, session_id: str) -> bool:
        """加载已存在的会话"""
        session_file = self.session_dir / f"{session_id}.json"
        if not session_file.exists():
            print(f"❌ 会话文件不存在: {session_id}")
            return False

        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.current_session = WorkflowSession(**data)

        print(f"✅ 已加载会话: {session_id}")
        return True

    def get_session_status(self) -> Dict[str, Any]:
        """获取当前会话状态"""
        if not self.current_session:
            return {"status": "no_session"}

        return {
            "session_id": self.current_session.session_id,
            "status": self.current_session.status,
            "progress": f"{self.current_session.current_step}/{len(self.steps)}",
            "current_step": self.steps[self.current_session.current_step] if self.current_session.current_step < len(self.steps) else "completed",
            "document": self.current_session.document_name
        }


# 单例模式
_chain_manager = None

def get_chain_manager() -> WorkflowChainManager:
    """获取链式管理器单例"""
    global _chain_manager
    if _chain_manager is None:
        _chain_manager = WorkflowChainManager()
    return _chain_manager


if __name__ == "__main__":
    # 测试示例
    manager = get_chain_manager()

    # 创建会话
    session_id = manager.create_session(
        doc_url="https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R",
        doc_name="小红书部门",
        baseline_week="W37",
        current_week="W38"
    )

    # 模拟步骤执行
    manager.add_step_result(
        "download_csv",
        input_files={"url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R"},
        output_files={"csv": "/path/to/download.csv"},
        metadata={"rows": 100, "columns": 19}
    )

    print("\n会话状态:", manager.get_session_status())