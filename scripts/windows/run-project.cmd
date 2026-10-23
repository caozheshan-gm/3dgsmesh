@echo off
setlocal
call "%~dp0activate-gs.cmd"
if errorlevel 1 exit /b 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-project.ps1" %*
exit /b %ERRORLEVEL%
