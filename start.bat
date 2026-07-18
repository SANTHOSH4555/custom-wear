@echo off
title CUSTOM WEAR & CRADANCE Server
echo =====================================================
echo   CUSTOM WEAR & CRADANCE - Premium E-Commerce
echo =====================================================
echo   Starting server on http://localhost:5000
echo =====================================================
cd /d "%~dp0"
backend\venv\Scripts\python run.py
pause
