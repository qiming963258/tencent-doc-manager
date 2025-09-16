#!/bin/bash
# 腾讯文档自动下载系统 - 快速部署脚本

echo "======================================"
echo "腾讯文档自动下载系统 - 部署向导"
echo "======================================"

# 检测系统类型
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
else
    echo "不支持的操作系统: $OSTYPE"
    exit 1
fi

echo "检测到系统: $OS"

# 安装依赖
echo ""
echo "1. 安装系统依赖..."

if [ "$OS" == "linux" ]; then
    # Linux依赖
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        wget \
        xvfb \
        chromium-browser \
        chromium-chromedriver
        
    # 安装Chrome（如果需要）
    if ! command -v google-chrome &> /dev/null; then
        echo "安装Google Chrome..."
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google.list
        sudo apt-get update
        sudo apt-get install -y google-chrome-stable
    fi
else
    # macOS依赖
    if ! command -v brew &> /dev/null; then
        echo "请先安装Homebrew"
        exit 1
    fi
    brew install python3
    brew install --cask google-chrome
fi

echo "✅ 系统依赖安装完成"

# 安装Python依赖
echo ""
echo "2. 安装Python依赖..."

pip3 install --upgrade pip
pip3 install \
    selenium \
    undetected-chromedriver \
    pyvirtualdisplay \
    requests \
    schedule

echo "✅ Python依赖安装完成"

# 创建配置文件
echo ""
echo "3. 创建配置文件..."

CONFIG_FILE="server_config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    cat > $CONFIG_FILE << EOF
{
    "cookie_string": "",
    "download_dir": "$(pwd)/downloads",
    "upload_endpoint": "http://your-server.com/api/upload",
    "use_virtual_display": $([ "$OS" == "linux" ] && echo "true" || echo "false"),
    "headless": false,
    "filter_settings": {
        "owner": "my_documents",
        "time_range": "recent_month"
    }
}
EOF
    echo "✅ 配置文件已创建: $CONFIG_FILE"
    echo "⚠️ 请编辑配置文件，添加您的Cookie字符串"
else
    echo "配置文件已存在"
fi

# 创建系统服务（Linux）
if [ "$OS" == "linux" ]; then
    echo ""
    echo "4. 创建系统服务..."
    
    SERVICE_FILE="/etc/systemd/system/tencent-doc-downloader.service"
    
    sudo cat > $SERVICE_FILE << EOF
[Unit]
Description=腾讯文档自动下载服务
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/server_auto_downloader.py
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    echo "✅ 系统服务已创建"
    echo ""
    echo "服务管理命令:"
    echo "  启动: sudo systemctl start tencent-doc-downloader"
    echo "  停止: sudo systemctl stop tencent-doc-downloader"
    echo "  状态: sudo systemctl status tencent-doc-downloader"
    echo "  开机启动: sudo systemctl enable tencent-doc-downloader"
fi

# 创建定时任务
echo ""
echo "5. 设置定时任务..."

CRON_CMD="cd $(pwd) && /usr/bin/python3 server_auto_downloader.py >> /var/log/tencent_doc_cron.log 2>&1"

# 检查是否已存在
if ! crontab -l 2>/dev/null | grep -q "server_auto_downloader.py"; then
    # 添加到crontab（每天凌晨3点执行）
    (crontab -l 2>/dev/null; echo "0 3 * * * $CRON_CMD") | crontab -
    echo "✅ 定时任务已设置（每天凌晨3点执行）"
else
    echo "定时任务已存在"
fi

# 测试脚本
echo ""
echo "6. 测试运行..."

read -p "是否立即测试运行？(y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ "$OS" == "linux" ]; then
        # Linux使用虚拟显示
        echo "启动虚拟显示..."
        Xvfb :99 -screen 0 1920x1080x24 &
        XVFB_PID=$!
        export DISPLAY=:99
        
        echo "运行下载脚本..."
        python3 server_auto_downloader.py
        
        # 清理
        kill $XVFB_PID 2>/dev/null
    else
        # macOS直接运行
        python3 server_auto_downloader.py
    fi
fi

echo ""
echo "======================================"
echo "部署完成！"
echo ""
echo "下一步操作:"
echo "1. 编辑 server_config.json 添加Cookie"
echo "2. 运行测试: python3 server_auto_downloader.py"
echo "3. 启用自动化: sudo systemctl enable tencent-doc-downloader"
echo "======================================"