@echo off
title 56 File Converter
echo ===================================================
echo             Starting 56 File Converter
echo ===================================================
echo.
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo Installing requirements...
    pip install -r requirements.txt
)
echo Starting server at http://127.0.0.1:5000...
start http://127.0.0.1:5000
python app.py
pause
