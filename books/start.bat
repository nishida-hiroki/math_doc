@echo off
cd /d "%~dp0"
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo Starting book database server...
echo Open http://127.0.0.1:5001 in your browser (Chrome or Edge recommended)
python app.py
pause
