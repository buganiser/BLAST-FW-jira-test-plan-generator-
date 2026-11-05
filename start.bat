@echo off
REM Jira Test Plan Generator - Startup Script for Windows
REM This script starts both the backend API server and the React frontend

echo ============================================
echo Jira Test Plan Generator - Starting Services
echo ============================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

echo.
echo [1/4] Installing Python dependencies...
pip install -r requirements.txt

echo.
echo [2/4] Installing Frontend dependencies...
cd frontend
npm install
cd ..

echo.
echo [3/4] Starting Backend API Server (port 8000)...
start "Jira Test Plan Generator - Backend" cmd /k python server.py

echo.
echo [4/4] Starting Frontend Dev Server (port 3000)...
cd frontend
start "Jira Test Plan Generator - Frontend" cmd /k npm run dev
cd ..

echo.
echo ============================================
echo Services Started!
echo ============================================
echo Backend API:  http://localhost:8000
echo Frontend UI:  http://localhost:3000
echo API Docs:     http://localhost:8000/docs
echo ============================================
echo.
echo Press any key to close this window (services will continue running)
pause