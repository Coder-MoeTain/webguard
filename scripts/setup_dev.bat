@echo off
REM WebGuard RF - Development Setup (Windows)
cd /d "%~dp0\.."

echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Creating data and models directories...
if not exist data mkdir data
if not exist models mkdir models

echo Generating sample dataset (10k samples)...
python scripts\generate_sample_dataset.py

echo Done. Run: python run_backend.py
echo Then: cd frontend ^&^& npm install ^&^& npm run dev
