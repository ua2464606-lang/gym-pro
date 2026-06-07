@echo off
title GYM PRO - EXE Builder (Fixed)
color 0A
echo.
echo  ==========================================
echo   💪  GYM PRO — EXE Builder (Fixed)
echo  ==========================================
echo.

REM ── Check Python ─────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python nahi mila! python.org se install karen.
    pause & exit /b 1
)
echo  [OK] Python mil gaya.
echo.

REM ── Check gym_pro.py ─────────────────────────────────────────
if not exist "gym_pro.py" (
    echo  [ERROR] gym_pro.py is folder mein nahi hai!
    echo  build_exe.bat aur gym_pro.py ek hi folder mein hone chahiye.
    pause & exit /b 1
)

REM ── Clean old build/venv ──────────────────────────────────────
echo  Purani build files hata rahe hain...
if exist "venv_gym"  rmdir /s /q "venv_gym"
if exist "build"     rmdir /s /q "build"
if exist "dist"      rmdir /s /q "dist"
if exist "GymPro.spec" del /q "GymPro.spec"
echo  [OK] Clean ho gaya.
echo.

REM ── Create fresh virtual environment ─────────────────────────
echo  [1/4] Fresh virtual environment bana rahe hain...
python -m venv venv_gym
if %errorlevel% neq 0 (
    echo  [ERROR] venv nahi bana!
    pause & exit /b 1
)
echo  [OK] venv ban gaya.
echo.

REM ── Install packages in venv (clean, no tensorflow/torch) ────
echo  [2/4] Packages install ho rahe hain (sirf zaruri wale)...
echo  (Pehli dafa 10-15 minute lag sakte hain)
echo.

REM numpy 1.x fix - face_recognition aur dlib ko yahi chahiye
venv_gym\Scripts\pip install --upgrade pip --quiet
venv_gym\Scripts\pip install "numpy<2" --quiet
echo  [OK] numpy 1.x install ho gaya.

REM Try pre-built dlib wheel first (Visual C++ ki zaroorat nahi)
echo  dlib install ho raha hai (pre-built wheel)...
venv_gym\Scripts\pip install dlib --quiet
if %errorlevel% neq 0 (
    echo.
    echo  [!] dlib ka pre-built wheel nahi mila.
    echo  Pre-compiled wheel download karte hain...
    venv_gym\Scripts\pip install https://github.com/z-mahmud22/Dlib_Windows_Python3.x/releases/download/v19.24.2/dlib-19.24.2-cp311-cp311-win_amd64.whl --quiet
    if %errorlevel% neq 0 (
        echo.
        echo  ============================================
        echo  [ERROR] dlib install nahi hua!
        echo.
        echo  MANUAL FIX:
        echo  1. Is link se .whl file download karen:
        echo     https://github.com/z-mahmud22/Dlib_Windows_Python3.x/releases
        echo  2. Python 3.11 ke liye:
        echo     dlib-19.24.2-cp311-cp311-win_amd64.whl
        echo  3. Is folder mein rakhein: %CD%
        echo  4. Phir ye command chalayein:
        echo     venv_gym\Scripts\pip install dlib-19.24.2-cp311-cp311-win_amd64.whl
        echo  5. Phir dobara build_exe.bat chalayein
        echo  ============================================
        pause & exit /b 1
    )
)
echo  [OK] dlib install ho gaya.

venv_gym\Scripts\pip install face_recognition --quiet
venv_gym\Scripts\pip install opencv-python --quiet
venv_gym\Scripts\pip install pillow --quiet
venv_gym\Scripts\pip install pyinstaller --quiet
echo.
echo  [OK] Sab packages install ho gaye.
echo.

REM ── Build EXE ────────────────────────────────────────────────
echo  [3/4] EXE ban rahi hai... (5-10 minute lag sakte hain)
echo.

venv_gym\Scripts\pyinstaller ^
  --onefile ^
  --windowed ^
  --name "GymPro" ^
  --hidden-import "face_recognition" ^
  --hidden-import "face_recognition_models" ^
  --hidden-import "dlib" ^
  --hidden-import "cv2" ^
  --hidden-import "PIL" ^
  --hidden-import "PIL._tkinter_finder" ^
  --collect-all "face_recognition_models" ^
  gym_pro.py

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Build fail ho gayi! Upar error message dekhen.
    pause & exit /b 1
)

echo.
echo  [OK] EXE ban gayi!
echo.

REM ── Copy DB ───────────────────────────────────────────────────
echo  [4/4] Database setup ready.
echo  [OK] App pehli run par gymPro.db khud bana legi.
echo.
echo  ==========================================
echo   ✅  BUILD COMPLETE!
echo  ==========================================
echo.
echo  Aapki files yahan hain:
echo  📁 dist\GymPro.exe
echo.
echo  CLIENT KO GymPro.exe BHEJNI HAI.
echo  Client sirf GymPro.exe double-click karega - bas!
echo.
pause
