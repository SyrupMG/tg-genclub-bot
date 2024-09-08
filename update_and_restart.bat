@echo off
setlocal enabledelayedexpansion

:: Get the directory of the script
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo Script directory: %SCRIPT_DIR%

:: Change to the script's directory
cd /d "%SCRIPT_DIR%"

:: Perform a git pull and capture the output
for /f "tokens=*" %%i in ('git pull') do (
    set "GIT_OUTPUT=%%i"
    echo Git pull output: !GIT_OUTPUT!
    
    :: Check if any updates were pulled
    if not "!GIT_OUTPUT!"=="Already up to date." (
        echo Updates detected. Restarting Docker containers...
        
        :: Stop the containers
        docker-compose down
        
        :: Start the containers
        docker-compose up -d
        
        echo Docker containers restarted.
    ) else (
        echo No updates found. Containers left running.
    )
)

endlocal