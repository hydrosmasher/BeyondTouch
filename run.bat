@echo off
set "BEYONDTOUCH_LAUNCH_DIR=%CD%"
cd /d "%~dp0"
py -3.12 src\run.py %*
if errorlevel 1 echo See guide\RUN_LOCALLY.md or open START_HERE.html to view without Python.
