#!/bin/bash
# 启动生产环境集成测试系统脚本 v3.0
# 完全按照项目正式流程运行

echo "========================================"
echo "🚀 启动腾讯文档管理系统 - 生产环境集成测试平台"
echo "📦 版本: v3.0.0 - Production Integrated"
echo "🌐 端口: 8094"
echo "📁 项目目录: /root/projects/tencent-doc-manager"
echo "========================================"

# 设置工作目录
cd /root/projects/tencent-doc-manager

# 检查Python环境
echo "📦 检查Python环境..."
python3 --version
echo ""

# 检查项目目录结构
echo "📁 检查项目目录结构..."
echo "✓ 项目根目录: $(pwd)"
echo "✓ 正式下载目录: $(ls -d downloads 2>/dev/null && echo "存在" || echo "不存在")"
echo "✓ 对比结果目录: $(ls -d comparison_results 2>/dev/null && echo "存在" || echo "不存在")"
echo "✓ 配置文件: $(ls config.json 2>/dev/null && echo "存在" || echo "不存在")"
echo "✓ 备用配置: $(ls auto_download_config.json 2>/dev/null && echo "存在" || echo "不存在")"
echo ""

# 检查必要的依赖
echo "📦 检查依赖包..."
pip3 list | grep -E "flask|pandas|requests" || {
    echo "⚠️ 缺少依赖，正在安装..."
    pip3 install flask pandas requests flask-cors
}
echo ""

# 检查核心模块
echo "🔧 检查项目核心模块..."
echo "✓ 简单对比模块: $(ls simple_comparison_handler.py 2>/dev/null && echo "存在" || echo "不存在")"
echo "✓ 生产环境模块目录: $(ls -d production/core_modules 2>/dev/null && echo "存在" || echo "不存在")"
echo "✓ 自适应对比器: $(ls production/core_modules/adaptive_table_comparator.py 2>/dev/null && echo "存在" || echo "不存在")"
echo "✓ 自动导出模块: $(find . -name "*tencent_export_automation*" | head -1 | xargs test -f && echo "存在" || echo "不存在")"
echo ""

# 停止可能存在的旧进程
echo "🔍 检查是否有旧进程运行..."
OLD_PID=$(lsof -ti:8094 2>/dev/null)
if [ ! -z "$OLD_PID" ]; then
    echo "⏹️ 停止旧进程 (PID: $OLD_PID)..."
    kill -9 $OLD_PID
    sleep 3
fi

# 创建必要的目录（使用项目正式目录结构）
echo "📁 确保项目目录结构完整..."
mkdir -p downloads
mkdir -p comparison_results  
mkdir -p comparison_baseline
mkdir -p comparison_target
mkdir -p logs
mkdir -p temp_workflow

echo "✅ 目录结构检查完成"
echo ""

# 验证配置文件
echo "⚙️ 验证配置文件..."
if [ -f "config.json" ]; then
    echo "✓ 主配置文件存在"
    # 检查配置文件格式
    python3 -c "import json; json.load(open('config.json'))" 2>/dev/null && echo "✓ 主配置格式正确" || echo "⚠️ 主配置格式有误"
else
    echo "⚠️ 主配置文件不存在，将使用默认配置"
fi

if [ -f "auto_download_config.json" ]; then
    echo "✓ 备用配置文件存在"
    python3 -c "import json; json.load(open('auto_download_config.json'))" 2>/dev/null && echo "✓ 备用配置格式正确" || echo "⚠️ 备用配置格式有误"
fi
echo ""

# 启动服务
echo "🚀 启动生产环境集成测试系统..."
echo "========================================"

# 使用nohup在后台运行
nohup python3 production_integrated_test_system_8094.py > logs/production_test_8094.log 2>&1 &
NEW_PID=$!

echo "✅ 生产环境测试系统已启动 (PID: $NEW_PID)"
echo "📝 日志文件: logs/production_test_8094.log"
echo ""
echo "🌐 访问地址:"
echo "   主界面: http://localhost:8094"
echo "   健康检查: http://localhost:8094/health"
echo "   对比结果: http://localhost:8094/results"
echo "   文件管理: http://localhost:8094/files"
echo ""
echo "📖 系统特性:"
echo "   ✓ 使用项目正式下载目录: /downloads"
echo "   ✓ 使用项目正式配置文件: /config.json"
echo "   ✓ 使用项目正式对比算法: AdaptiveTableComparator + SimpleComparison"
echo "   ✓ 使用项目正式结果存储: /comparison_results"
echo "   ✓ Cookie持久化存储: localStorage + 项目配置同步"
echo "   ✓ 完整路径说明面板"
echo "   ✓ 实时状态监控"
echo "   ✓ 文件管理界面"
echo ""
echo "🔧 管理命令:"
echo "   查看实时日志: tail -f logs/production_test_8094.log"
echo "   停止服务: kill $NEW_PID"
echo "   重启服务: ./start_production_test_8094.sh"
echo "========================================"

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo "🔍 检查服务状态..."
curl -s http://localhost:8094/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 生产环境测试系统启动成功!"
    
    # 显示健康检查信息
    echo ""
    echo "🏥 系统健康状态:"
    curl -s http://localhost:8094/health | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"   状态: {data.get('status', 'unknown')}\"
    print(f\"   版本: {data.get('version', 'unknown')}\"
    print(f\"   系统: {data.get('system', 'unknown')}\"
    print(f\"   时间: {data.get('timestamp', 'unknown')}\"
    print(f\"   模块状态:\")
    for module, status in data.get('modules', {}).items():
        icon = '✅' if status else '❌'
        print(f\"     {icon} {module}\")
    print(f\"   目录配置:\")
    for key, path in data.get('directories', {}).items():
        print(f\"     📁 {key}: {path}\")
except:
    print('   解析健康检查响应失败')
" 2>/dev/null || echo "   健康检查响应解析失败，但服务正在运行"

else
    echo "❌ 服务启动失败，请查看日志文件"
    echo "📝 最近的错误日志:"
    tail -20 logs/production_test_8094.log 2>/dev/null || echo "   日志文件不存在或无法读取"
fi

echo ""
echo "========================================"
echo "💡 使用提示:"
echo "   1. 在浏览器打开 http://localhost:8094"
echo "   2. 在Cookie配置区域输入有效的腾讯文档Cookie"
echo "   3. 点击'保存到项目配置'将Cookie同步到项目配置文件"
echo "   4. 在文档对比区域输入两个文档URL进行对比"
echo "   5. 查看路径信息面板了解系统使用的所有文件路径"
echo "   6. 使用文件管理页面浏览下载的文件和对比结果"
echo ""
echo "📚 技术说明:"
echo "   • 系统完全基于项目现有的生产环境组件"
echo "   • 下载使用 TencentDocAutoExporter 类"
echo "   • 对比使用 AdaptiveTableComparator + SimpleComparison"
echo "   • 配置管理与项目主配置文件完全同步"
echo "   • 支持模块动态加载和降级处理"
echo "========================================"