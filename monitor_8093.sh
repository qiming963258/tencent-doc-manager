#!/bin/bash
# 8093服务监控脚本

while true; do
    clear
    echo "========================================="
    echo "📊 8093服务监控面板"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================="
    
    # 检查进程
    PID=$(pgrep -f "production_integrated_test_system_8093.py")
    if [ -n "$PID" ]; then
        echo "✅ 服务状态: 运行中 (PID: $PID)"
        
        # 显示资源使用
        ps aux | grep $PID | grep -v grep | awk '{
            printf "📈 CPU使用率: %s%%\n", $3
            printf "💾 内存使用率: %s%%\n", $4
            printf "📦 虚拟内存: %.1fMB\n", $5/1024
            printf "📋 实际内存: %.1fMB\n", $6/1024
        }'
    else
        echo "❌ 服务状态: 未运行"
        echo "💡 提示: 运行 bash start_8093_optimized.sh 启动服务"
    fi
    
    echo ""
    echo "🌐 访问地址: http://202.140.143.88:8093/"
    echo ""
    
    # 显示最近日志
    echo "📝 最近日志:"
    echo "-----------------------------------------"
    if [ -f /tmp/8093_optimized.log ]; then
        tail -5 /tmp/8093_optimized.log | cut -c1-80
    else
        echo "无日志文件"
    fi
    
    echo ""
    echo "按 Ctrl+C 退出监控"
    sleep 5
done