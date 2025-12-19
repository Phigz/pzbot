@echo off
set "PZ_PATH=D:\SteamLibrary\steamapps\common\ProjectZomboid\ProjectZomboid64.exe"
set "PROC_NAME=ProjectZomboid64.exe"

echo Checking for running process...
tasklist /FI "IMAGENAME eq %PROC_NAME%" 2>NUL | %SystemRoot%\System32\find.exe /I /N "%PROC_NAME%">NUL
if "%ERRORLEVEL%"=="0" (
    echo Killing existing Project Zomboid process...
    taskkill /F /IM "%PROC_NAME%"
    timeout /t 2 /nobreak >NUL
)

echo Checking for existing clicker script...
wmic process where "CommandLine like '%%click_start_check.py%%'" call terminate 2>NUL

REM Configure Launch Options via Python
python "%~dp0configure_launch.py" %*
if %ERRORLEVEL% NEQ 0 (
    echo Error configuring launch options.
    pause
    exit /b %ERRORLEVEL%
)

if exist "%PZ_PATH%" (
    if exist "c:\Users\lucas\Zomboid\console.txt" del "c:\Users\lucas\Zomboid\console.txt"

    echo Launching Click Start Check...
    start /B python "%~dp0click_start_check.py"

    echo Launching Project Zomboid in DEBUG mode...
    cd /d "D:\SteamLibrary\steamapps\common\ProjectZomboid"
    start /WAIT "" "ProjectZomboid64.exe" -debug
    echo Game exited.
) else (
    echo ERROR: Project Zomboid executable not found at:
    echo %PZ_PATH%
    pause
)
