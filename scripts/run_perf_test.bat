@echo off
setlocal

python -m pytest tests/performance_test.py -v --benchmark-json=perf_report.json

if errorlevel 1 (
    echo 性能测试未通过！
    exit /b 1
) else (
    python scripts/generate_perf_report.py
)