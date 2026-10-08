@echo off
rem ============================================
rem  鸿胪寺后端一键启动脚本 (Windows)
rem  端口: 8767  仅本机访问 127.0.0.1
rem ============================================
title 鸿胪寺后端

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 python，请先安装 Python 3.10+ 并加入 PATH
    pause
    exit /b 1
)

echo [启动] 鸿胪寺后端 http://127.0.0.1:8767
echo [提示] 按 Ctrl+C 停止服务
echo.

rem 优先使用本目录虚拟环境，否则用系统 python
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8767
) else (
    python -m uvicorn app:app --host 127.0.0.1 --port 8767
)

if errorlevel 1 (
    echo.
    echo [错误] 启动失败。请检查依赖: pip install -r requirements.txt
)
pause
