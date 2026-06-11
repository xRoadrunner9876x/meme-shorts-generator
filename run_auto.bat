@echo off
REM === Kompletter Auto-Render: alle 4 Szenen + zusammen schneiden ===

set BLENDER=

if exist "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" (
    set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
) else if exist "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" (
    set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
) else if exist "C:\Program Files\Blender Foundation\Blender 4.4\blender.exe" (
    set "BLENDER=C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"
)

if "%BLENDER%"=="" (
    echo [FEHLER] Blender nicht gefunden!
    echo Trage den Pfad hier ein: set "BLENDER=DEIN_PFAD\blender.exe"
    pause
    exit /b 1
)

echo Blender: %BLENDER%
echo Starte kompletten Render (4 Szenen)...
echo.

python auto_render.py

echo.
echo Fertig! Videos liegen auf dem Desktop unter: voxelsim_renders\
pause
