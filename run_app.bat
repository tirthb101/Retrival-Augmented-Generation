@echo off
cd /d "%~dp0"
echo ==================================
echo     Checking Python Installation
echo ==================================

:: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python.
    pause
    exit /b
)

:: Print Python version
python --version

echo.
echo ==================================
echo     Checking NVIDIA GPU
echo ==================================

:: Check if NVIDIA GPU is available
where nvidia-smi >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] NVIDIA GPU not detected or drivers are not installed.
) else (
    nvidia-smi
)

echo.
echo ==================================
echo     Activating Virtual Environment
echo ==================================

:: Activate the virtual environment
call pdfasker\Scripts\activate

if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b
)

echo Virtual environment activated successfully.

echo.
echo ==================================
echo     Running fast-app.py
echo ==================================

@REM :: Run the application
@REM python fast-app.py sbi
python fast-app.py test

:: Keep the command prompt open in case of errors
pause
