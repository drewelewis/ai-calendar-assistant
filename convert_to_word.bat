@echo off
echo Converting AI Calendar Assistant Business Overview to Word document...
echo.

REM Check if pandoc is installed
pandoc --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Pandoc is not installed or not in PATH
    echo.
    echo Please install Pandoc first:
    echo 1. Visit https://pandoc.org/installing.html
    echo 2. Download and install Pandoc for Windows
    echo 3. Restart this command prompt
    echo 4. Run this script again
    pause
    exit /b 1
)

REM Convert markdown to Word document
pandoc AI_Calendar_Assistant_Business_Overview.md -o AI_Calendar_Assistant_Business_Overview.docx

if %errorlevel% equ 0 (
    echo SUCCESS: Word document created successfully!
    echo File: AI_Calendar_Assistant_Business_Overview.docx
    echo.
    echo Opening the document...
    start AI_Calendar_Assistant_Business_Overview.docx
) else (
    echo ERROR: Failed to convert the document
    echo Please check that the markdown file exists and try again
)

echo.
pause
