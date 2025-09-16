#!/bin/bash
# 8093服务内存优化启动脚本

echo "🚀 启动8093服务（内存优化版本）"

# 清理Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# 设置环境变量
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export DEEPSEEK_API_KEY=sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb

# 限制Python内存使用
export PYTHONMALLOC=malloc
export MALLOC_TRIM_THRESHOLD_=131072
export MALLOC_MMAP_THRESHOLD_=131072

# 设置Flask优化
export FLASK_ENV=production
export WERKZEUG_DEBUG_PIN=off

# 检查端口是否被占用
PORT=8093
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ 端口 $PORT 已被占用，尝试清理..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 2
fi

# 启动服务
echo "📝 日志文件: /tmp/8093_optimized.log"
cd /root/projects/tencent-doc-manager

# 使用nohup启动，限制内存使用
ulimit -v 1048576  # 限制虚拟内存为1GB
nohup python3 -u production_integrated_test_system_8093.py > /tmp/8093_optimized.log 2>&1 &

PID=$!
echo "✅ 服务已启动，PID: $PID"

# 等待服务启动
sleep 3

# 检查服务状态
if ps -p $PID > /dev/null ; then
    echo "✅ 服务运行正常"
    echo "🌐 访问地址: http://202.140.143.88:8093/"
    echo "📊 查看日志: tail -f /tmp/8093_optimized.log"
else
    echo "❌ 服务启动失败，请查看日志"
    tail -20 /tmp/8093_optimized.log
fi