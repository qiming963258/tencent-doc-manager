@echo off
chcp 65001 >nul
title 腾讯文档上传 - Web界面
cls
echo ========================================
echo 腾讯文档上传 - Web测试界面
echo ========================================
echo.
echo Web服务器启动中...
echo 访问地址: http://localhost:8109
echo.
echo 按Ctrl+C停止服务器
echo.
python upload_test_server_8109.py
pause