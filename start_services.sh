#!/bin/bash
# 腾讯文档监控系统 - 服务启动脚本
# 架构：8093(后端API) + 8089(前端UI)

echo "🚀 启动腾讯文档监控系统..."
echo "=" * 50

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查并停止旧服务
echo -e "${YELLOW}🔍 检查现有服务...${NC}"

# 停止8093端口的旧服务
if lsof -Pi :8093 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️ 发现8093端口已被占用，停止旧服务...${NC}"
    kill $(lsof -Pi :8093 -sTCP:LISTEN -t) 2>/dev/null
    sleep 2
fi

# 停止8089端口的旧服务
if lsof -Pi :8089 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️ 发现8089端口已被占用，停止旧服务...${NC}"
    kill $(lsof -Pi :8089 -sTCP:LISTEN -t) 2>/dev/null
    sleep 2
fi

# 启动后端API服务 (8093)
echo -e "${GREEN}📦 启动后端API服务 (端口 8093)...${NC}"
cd /root/projects/tencent-doc-manager
nohup python3 production_integrated_test_system_8093.py > logs/backend_8093.log 2>&1 &
BACKEND_PID=$!
echo "   后端服务PID: $BACKEND_PID"

# 等待后端服务启动
echo -e "${YELLOW}⏳ 等待后端服务启动...${NC}"
for i in {1..10}; do
    if curl -s http://localhost:8093/api/status >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务启动成功！${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ 后端服务启动失败！${NC}"
        exit 1
    fi
done

# 启动前端UI服务 (8089)
echo -e "${GREEN}🎨 启动前端UI服务 (端口 8089)...${NC}"
cd /root/projects/tencent-doc-manager
nohup python3 production/servers/final_heatmap_server.py > logs/frontend_8089.log 2>&1 &
FRONTEND_PID=$!
echo "   前端服务PID: $FRONTEND_PID"

# 等待前端服务启动
echo -e "${YELLOW}⏳ 等待前端服务启动...${NC}"
for i in {1..10}; do
    if curl -s http://localhost:8089/api/workflow-status >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 前端服务启动成功！${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ 前端服务启动失败！${NC}"
        exit 1
    fi
done

# 显示服务状态
echo ""
echo "=" * 50
echo -e "${GREEN}🎉 系统启动完成！${NC}"
echo ""
echo "📊 服务架构："
echo "   • 后端API服务: http://202.140.143.88:8093 (PID: $BACKEND_PID)"
echo "   • 前端UI服务:  http://202.140.143.88:8089 (PID: $FRONTEND_PID)"
echo ""
echo "📝 日志文件："
echo "   • 后端日志: logs/backend_8093.log"
echo "   • 前端日志: logs/frontend_8089.log"
echo ""
echo "🔧 管理命令："
echo "   • 查看状态: curl http://localhost:8093/api/status | python3 -m json.tool"
echo "   • 停止服务: kill $BACKEND_PID $FRONTEND_PID"
echo "   • 查看日志: tail -f logs/backend_8093.log"
echo ""
echo "=" * 50

# 保存PID到文件
echo $BACKEND_PID > /root/projects/tencent-doc-manager/backend.pid
echo $FRONTEND_PID > /root/projects/tencent-doc-manager/frontend.pid

echo -e "${GREEN}✨ 访问 http://202.140.143.88:8089 开始使用系统${NC}"