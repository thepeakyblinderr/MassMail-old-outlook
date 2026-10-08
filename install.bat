@echo off
rem pushd also works when this folder is on a network (UNC) path
pushd "%~dp0"
echo ============================================
echo  MassMail - First Time Setup
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please download Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
pip install -r requirements.txt

echo.
echo ============================================
echo  Setup complete! Run MassMail with run.bat
echo ============================================
popd
pause
