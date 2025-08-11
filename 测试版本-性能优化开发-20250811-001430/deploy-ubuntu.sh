#!/bin/bash
# Ubuntu 4H2G服务器部署脚本 - 性能优化版本

set -e

echo "🚀 开始部署腾讯文档自动化系统 - 性能优化版"

# 检查系统要求
echo "检查系统配置..."
CORES=$(nproc)
MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')

echo "CPU核心数: $CORES"
echo "内存大小: ${MEMORY_GB}GB"

if [ "$CORES" -lt 4 ] || [ "$MEMORY_GB" -lt 2 ]; then
    echo "⚠️  警告: 系统配置可能不满足推荐要求 (4H2G)"
    echo "当前配置: ${CORES}H${MEMORY_GB}G"
    read -p "是否继续部署? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        exit 1
    fi
fi

# 安装Docker和Docker Compose
echo "安装Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 系统优化
echo "应用系统优化配置..."
sudo cp ubuntu-sysctl.conf /etc/sysctl.d/99-tencent-docs.conf
sudo sysctl -p /etc/sysctl.d/99-tencent-docs.conf

# 设置ulimit
echo "优化资源限制..."
cat << 'EOF' | sudo tee -a /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
EOF

# 创建项目目录结构
echo "创建项目目录..."
sudo mkdir -p /opt/tencent-docs/{data,logs,uploads,downloads,ssl,monitoring}
sudo chown -R $USER:$USER /opt/tencent-docs

# 复制项目文件
echo "复制项目文件..."
cp -r ./* /opt/tencent-docs/
cd /opt/tencent-docs

# 设置环境变量
echo "配置环境变量..."
cat << EOF > .env
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
DATABASE_URL=sqlite:///data/tencent_docs.db
MAX_WORKERS=2
MAX_CONCURRENT_DOWNLOADS=3
MAX_CONCURRENT_UPLOADS=2
BROWSER_POOL_SIZE=3
MEMORY_LIMIT_MB=1500
GRAFANA_PASSWORD=$(openssl rand -hex 16)
EOF

# 创建日志轮转配置
echo "配置日志轮转..."
cat << 'EOF' | sudo tee /etc/logrotate.d/tencent-docs
/opt/tencent-docs/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
    postrotate
        docker-compose -f /opt/tencent-docs/docker-compose-optimized.yml restart app > /dev/null 2>&1 || true
    endscript
}
EOF

# 设置防火墙
echo "配置防火墙..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 9090/tcp  # Prometheus
    echo "防火墙规则已添加"
fi

# 构建和启动服务
echo "构建Docker镜像..."
docker build -f Dockerfile-optimized -t tencent-docs-optimized .

echo "启动服务..."
docker-compose -f docker-compose-optimized.yml up -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 健康检查
echo "执行健康检查..."
if curl -f -s http://localhost/api/health > /dev/null; then
    echo "✅ 健康检查通过"
else
    echo "❌ 健康检查失败，检查日志:"
    docker-compose -f docker-compose-optimized.yml logs --tail=20
fi

# 显示服务状态
echo ""
echo "📊 服务状态:"
docker-compose -f docker-compose-optimized.yml ps

echo ""
echo "🔧 系统资源使用:"
echo "内存使用: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "CPU负载: $(uptime | awk -F'load average:' '{print $2}')"

echo ""
echo "🌐 服务访问地址:"
echo "  - Web界面: http://$(hostname -I | awk '{print $1}')"
echo "  - API健康检查: http://$(hostname -I | awk '{print $1}')/api/health"
echo "  - 性能监控: http://$(hostname -I | awk '{print $1}'):9090 (如果启用)"

echo ""
echo "📝 管理命令:"
echo "  - 查看日志: docker-compose -f docker-compose-optimized.yml logs -f"
echo "  - 重启服务: docker-compose -f docker-compose-optimized.yml restart"
echo "  - 停止服务: docker-compose -f docker-compose-optimized.yml down"
echo "  - 更新服务: ./deploy.sh update"

echo ""
echo "🎉 部署完成!"

# 创建管理脚本
cat << 'EOF' > manage.sh
#!/bin/bash
# 服务管理脚本

cd /opt/tencent-docs

case "$1" in
    start)
        docker-compose -f docker-compose-optimized.yml up -d
        ;;
    stop)
        docker-compose -f docker-compose-optimized.yml down
        ;;
    restart)
        docker-compose -f docker-compose-optimized.yml restart
        ;;
    logs)
        docker-compose -f docker-compose-optimized.yml logs -f
        ;;
    status)
        docker-compose -f docker-compose-optimized.yml ps
        docker stats --no-stream
        ;;
    health)
        curl -f http://localhost/api/health && echo "✅ 服务健康" || echo "❌ 服务异常"
        ;;
    update)
        docker-compose -f docker-compose-optimized.yml pull
        docker-compose -f docker-compose-optimized.yml up -d --build
        ;;
    backup)
        DATE=$(date +%Y%m%d_%H%M%S)
        tar -czf "backup_${DATE}.tar.gz" data/
        echo "备份完成: backup_${DATE}.tar.gz"
        ;;
    monitor)
        echo "系统资源监控:"
        echo "内存: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
        echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
        echo "磁盘: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"
        echo "Docker容器:"
        docker stats --no-stream
        ;;
    *)
        echo "用法: $0 {start|stop|restart|logs|status|health|update|backup|monitor}"
        exit 1
        ;;
esac
EOF

chmod +x manage.sh

echo "管理脚本已创建: ./manage.sh"
echo "使用示例: ./manage.sh status"