#!/usr/bin/env python3
"""快速可视化测试脚本"""

import asyncio
import os
from visual_debug import VisualDebugger

async def main():
    """直接运行快速测试"""
    print("="*50)
    print("腾讯文档上传 - 快速可视化测试")
    print("="*50)
    
    debugger = VisualDebugger()
    await debugger.quick_test()

if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 运行测试
    asyncio.run(main())