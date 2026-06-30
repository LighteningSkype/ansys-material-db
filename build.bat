@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   Ansys Material Database - Build Script
echo ============================================
echo.

REM Check if PyInstaller is installed
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller not found. Installing...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        echo        Try: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo [1/3] Cleaning previous builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo [2/3] Building single-file exe (this may take several minutes)...
python -m PyInstaller ansys_material_db.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo [3/3] Build complete!
echo.
echo Output: dist\AnsysMaterialDB.exe
echo.
dir dist\AnsysMaterialDB.exe
echo.
pause