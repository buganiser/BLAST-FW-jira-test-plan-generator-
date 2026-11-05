#!/bin/bash
# Jira Test Plan Generator - Startup Script for Linux/macOS
# This script starts both the backend API server and the React frontend

set -e

echo "============================================"
echo "Jira Test Plan Generator - Starting Services"
echo "============================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo ""
echo "[1/4] Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "[2/4] Installing Frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "[3/4] Starting Backend API Server (port 8000)..."
python3 server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

echo ""
echo "[4/4] Starting Frontend Dev Server (port 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================"
echo "Services Started!"
echo "============================================"
echo "Backend API:  http://localhost:8000"
echo "Frontend UI:  http://localhost:3000"
echo "API Docs:     http://localhost:8000/docs"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C to kill background processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID