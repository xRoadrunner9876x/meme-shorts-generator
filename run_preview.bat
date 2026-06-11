@echo off
REM === Findet Blender automatisch und rendert Preview ===

REM Standard-Installationspfade prüfen
set BLENDER=

if exist "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" (
    set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
) else if exist "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" (
    set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
) else if exist "C:\Program Files\Blender Foundation\Blender 4.4\blender.exe" (
    set "BLENDER=C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"
) else if exist "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" (
    set "BLENDER=C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
)

if "%BLENDER%"=="" (
    echo [FEHLER] Blender nicht gefunden! Installiere Blender oder trage den Pfad unten ein.
    echo.
    echo Trage den Pfad zu blender.exe hier ein und speichere die Datei:
    echo   set "BLENDER=DEIN_PFAD_HIER\blender.exe"
    pause
    exit /b 1
)

echo Blender gefunden: %BLENDER%
echo Rendert Preview (1 Frame, OptiX GPU)...
echo.

"%BLENDER%" --background --python preview.py

echo.
echo Fertig! Preview liegt auf dem Desktop unter: voxelsim_renders\preview\preview.png
pause
