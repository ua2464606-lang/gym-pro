@echo off
title GYM PRO - Setup & Launcher
color 0A
echo.
echo  ==========================================
echo   💪  GYM PRO  —  First Time Setup
echo  ==========================================
echo.
echo  Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found!
    echo  Please install Python 3.9+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
echo  [OK] Python found.
echo.
echo  Installing required packages...
echo  (This may take 5-10 minutes on first run)
echo.
pip install face_recognition --quiet
pip install opencv-python --quiet
pip install pillow --quiet
pip install numpy --quiet
echo.
echo  [OK] All packages installed!
echo.
echo  ==========================================
echo   🚀  Launching GYM PRO...
echo  ==========================================
echo.
python gym_pro.py
pause
