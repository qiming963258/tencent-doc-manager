# 腾讯文档自动化Docker环境
FROM ubuntu:22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    gnupg \
    xvfb \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 安装Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip3 install playwright asyncio schedule

# 安装Playwright浏览器
RUN playwright install chromium && \
    playwright install-deps chromium

# 创建工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 创建必要目录
RUN mkdir -p /app/config /app/downloads /app/uploads

# 设置权限
RUN chmod +x /app/cloud_automation_solution.py

# 启动脚本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 暴露端口（如果需要监控）
EXPOSE 8080

# 启动服务
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python3", "/app/cloud_automation_solution.py"]