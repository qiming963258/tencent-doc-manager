#!/bin/bash
# 启动增强版对比测试系统脚本

echo "========================================"
echo "🚀 启动腾讯文档对比测试系统 V2.0"
echo "========================================"

# 设置工作目录
cd /root/projects/tencent-doc-manager

# 检查Python环境
echo "📦 检查Python环境..."
python3 --version

# 检查必要的依赖
echo "📦 检查依赖包..."
pip3 list | grep -E "flask|pandas|requests" || {
    echo "⚠️ 缺少依赖，正在安装..."
    pip3 install flask pandas requests
}

# 停止可能存在的旧进程
echo "🔍 检查是否有旧进程运行..."
OLD_PID=$(lsof -ti:8094)
if [ ! -z "$OLD_PID" ]; then
    echo "⏹️ 停止旧进程 (PID: $OLD_PID)..."
    kill -9 $OLD_PID
    sleep 2
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p comparison_downloads
mkdir -p comparison_temp
mkdir -p comparison_logs
mkdir -p comparison_results

# 启动服务
echo "🚀 启动服务..."
echo "========================================"

# 使用nohup在后台运行
nohup python3 comparison_test_ui_enhanced.py > comparison_8094.log 2>&1 &
NEW_PID=$!

echo "✅ 服务已启动 (PID: $NEW_PID)"
echo "📝 日志文件: comparison_8094.log"
echo ""
echo "🌐 访问地址:"
echo "   主界面: http://localhost:8094"
echo "   健康检查: http://localhost:8094/health"
echo ""
echo "📖 使用说明:"
echo "   1. 在浏览器打开 http://localhost:8094"
echo "   2. 输入基线和目标文档URL"
echo "   3. 点击'开始对比'按钮"
echo "   4. 查看实时日志和对比结果"
echo ""
echo "🔧 管理命令:"
echo "   查看日志: tail -f comparison_8094.log"
echo "   停止服务: kill $NEW_PID"
echo "   测试系统: python3 test_comparison_enhanced.py"
echo "========================================"

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 3

# 检查服务状态
curl -s http://localhost:8094/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 服务启动成功!"
    
    # 运行简单测试
    echo ""
    echo "🧪 执行快速健康检查..."
    curl -s http://localhost:8094/health | python3 -m json.tool | head -10
else
    echo "❌ 服务启动失败，请查看日志文件"
    tail -20 comparison_8094.log
fi

echo ""
echo "========================================"
echo "💡 提示: 使用 tail -f comparison_8094.log 查看实时日志"
echo "========================================"