@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 crm.py
  if errorlevel 1 pause
  exit /b
)
where python >nul 2>nul
if %errorlevel% equ 0 (
  python crm.py
  if errorlevel 1 pause
  exit /b
)
echo Python 3 is required. Install Python for Windows from python.org with Tcl/Tk support.
echo Then double-click Start-CRM.bat again.
pause
phone 512 773-6696