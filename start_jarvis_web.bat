@echo off
title Jarvis 2.0 Spatial OS Web Center
cd /d "%~dp0"
echo Starting Jarvis 2.0 Spatial Web OS on http://localhost:8502...
python -m streamlit run app.py --server.port 8502
pause
