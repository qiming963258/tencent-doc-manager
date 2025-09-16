@echo off
chcp 65001 >nul
echo ========================================
echo 腾讯文档上传系统 - Windows环境设置
echo ========================================
echo.

echo [1] 检查Python版本...
python --version
if errorlevel 1 (
    echo ❌ Python未安装，请先安装Python 3.8+
    pause
    exit
)

echo.
echo [2] 安装Python依赖...
pip install -r requirements.txt

echo.
echo [3] 安装Playwright浏览器...
playwright install chromium

echo.
echo [4] 创建必要的目录...
if not exist logs mkdir logs
if not exist test_uploads mkdir test_uploads

echo.
echo ========================================
echo ✅ 环境设置完成！
echo ========================================
echo.
echo 运行方式：
echo   1. 可视化调试: python visual_debug.py
echo   2. Web界面: python upload_test_server_8109.py
echo   3. 命令行测试: python test_real_upload.py
echo.
pause