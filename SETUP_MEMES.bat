@echo off
echo ========================================
echo   Meme Shorts Generator - Setup
echo ========================================
echo.

REM Check Python
python --version 2>NUL
if errorlevel 1 (
    echo FEHLER: Python nicht gefunden!
    echo Installiere von https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check ffmpeg
ffmpeg -version 2>NUL
if errorlevel 1 (
    echo FEHLER: ffmpeg nicht gefunden!
    echo Installiere mit: winget install Gyan.FFmpeg
    pause
    exit /b 1
)

REM Install Python deps
echo Installiere Python-Dependencies...
pip install requests pytesseract Pillow edge-tts yt-dlp --quiet

REM Create dirs
if not exist parkour mkdir parkour
if not exist output mkdir output

echo.
echo ========================================
echo   Setup fertig!
echo   Starte mit: python meme_generator_pc.py
echo ========================================
pause
