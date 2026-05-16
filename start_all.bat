@echo off
echo Starting MediGraph Full Stack...

start "Python API" cmd /k "cd /d C:\Users\chira\OneDrive\Desktop\tigergraph\graphrag-benchmark && .venv\Scripts\activate && uvicorn api_server:app --host 0.0.0.0 --port 8080 --reload"

timeout /t 4 /nobreak

start "Next.js Dashboard" cmd /k "cd /d C:\Users\chira\OneDrive\Desktop\tigergraph\medi-graph-dashboard && pnpm dev"

echo.
echo Started:
echo   Dashboard: http://localhost:3000
echo   API:       http://localhost:8080
echo   API docs:  http://localhost:8080/docs
