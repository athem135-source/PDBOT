@echo off
REM ============================================
REM Create Desktop Shortcut for PDBot
REM ============================================

set SCRIPT_DIR=%~dp0
set SHORTCUT_NAME=PDBot Chatbot.lnk
set TARGET=%SCRIPT_DIR%start.bat
set DESKTOP=%USERPROFILE%\Desktop

echo Creating desktop shortcut...

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\%SHORTCUT_NAME%'); $Shortcut.TargetPath = '%TARGET%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.IconLocation = 'shell32.dll,13'; $Shortcut.Description = 'Launch PDBot Chatbot'; $Shortcut.Save()"

if exist "%DESKTOP%\%SHORTCUT_NAME%" (
    echo.
    echo [OK] Shortcut created on desktop: %SHORTCUT_NAME%
    echo.
    echo You can now double-click the desktop icon to launch PDBot!
    echo.
) else (
    echo.
    echo [ERROR] Failed to create shortcut.
    echo.
)

pause
