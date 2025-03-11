@echo off
REM 静默安装DyDown并记录日志
Dydown_Installer.exe /VERYSILENT /LOG=install.log

REM 检查安装日志
if exist "install.log" (
    echo 安装日志已生成：install.log
) else (
    echo 安装日志生成失败
    exit /b 1
)

echo 安装测试完成