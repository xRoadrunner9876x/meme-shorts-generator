@echo off
echo ========================================
echo   Meme Render Server - Setup + Start
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
    echo Installiere mit: winget install ffmpeg
    echo Oder von: https://www.gyan.dev/ffmpeg/builds/
    pause
    exit /b 1
)

REM Install deps
echo Installiere Dependencies...
pip install flask requests --quiet

echo.
echo Starte Render Server auf Port 8765...
echo VPS verbindet sich unter: http://100.83.156.25:8765
echo.
python pc_renderer_windows.py
pause
