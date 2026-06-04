@echo off
cd /d "%~dp0"

echo.
echo [1/3] Checking token verification...
python -c "import json,sys; d=json.load(open('data/token_count_verification.json')); print(f'  Tokens : {d[\"total_tokens\"]/1e6:.1f}M'); print(f'  Target : {\"MET\" if d[\"target_met\"] else \"NOT MET\"}'); sys.exit(0 if d['target_met'] else 1)"
if errorlevel 1 (
    echo.
    echo STOP: Download not complete or target not met.
    echo Re-run: python data/download_corpus.py
    pause
    exit /b 1
)

echo.
echo [2/3] Starting ingestion...
python ingest_corpus.py
if errorlevel 1 (
    echo.
    echo STOP: Ingestion failed. Check errors above.
    pause
    exit /b 1
)

echo.
echo [3/3] Running benchmark...
python evaluation/run_benchmark.py
if errorlevel 1 (
    echo.
    echo STOP: Benchmark failed. Check errors above.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  ALL DONE. Check results/benchmark_results.json
echo ============================================
pause
