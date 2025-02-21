@echo off
color 0A
title GRIV Project Manager

:menu
cls
echo ===================================
echo        GRIV Project Manager
echo ===================================
echo 1. First-time Setup
echo 2. Run Application
echo 3. Upload to GitHub
echo 4. Exit
echo ===================================
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto run
if "%choice%"=="3" goto github
if "%choice%"=="4" exit
goto menu

:setup
cls
echo Installing required packages...
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed! Please install Git first.
    pause
    goto menu
)

:: Create virtual environment
python -m venv venv
call venv\Scripts\activate

:: Create requirements if doesn't exist
if not exist requirements.txt (
    echo flask > requirements.txt
    echo gunicorn >> requirements.txt
)

:: Install requirements
pip install -r requirements.txt

:: Create .gitignore
echo Creating .gitignore...
echo __pycache__/ > .gitignore
echo *.pyc >> .gitignore
echo venv/ >> .gitignore
echo .env >> .gitignore
echo *.db >> .gitignore
echo .DS_Store >> .gitignore

echo Setup completed successfully!
pause
goto menu

:run
cls
echo Starting Flask application...
call venv\Scripts\activate
python wsgi.py
pause
goto menu

:github
cls
echo Uploading to GitHub...
call venv\Scripts\activate

:: Initialize git if needed
if not exist .git (
    echo Initializing git repository...
    git init
)

:: Add all files
echo Adding files to git...
git add .

:: Commit changes
set /p commit_msg="Enter commit message (default: Update): "
if "%commit_msg%"=="" set commit_msg=Update
git commit -m "%commit_msg%"

:: Check if remote exists
git remote -v | find "origin" >nul
if %errorlevel% neq 0 (
    echo Adding remote origin...
    git remote add origin https://github.com/blueking99/griv.git
)

:: Push to GitHub
echo Pushing to GitHub...
git push -u origin main

echo GitHub upload completed!
pause
goto menu 