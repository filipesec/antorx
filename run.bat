@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment not found. Run install.bat first.
  exit /b 1
)
".venv\Scripts\python.exe" main.py %*
