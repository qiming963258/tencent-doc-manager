@echo off
chcp 65001 >nul
title 腾讯文档上传 - 可视化调试
cls
echo ========================================
echo 腾讯文档上传 - Windows可视化调试
echo ========================================
echo.
echo 启动可视化调试器...
echo 浏览器将自动打开，您可以看到操作过程
echo.
python visual_debug.py
pause