@echo off
REM KL-B: uruchamia symulator (TCP) i most do LSL w dwoch oknach
cd /d "%~dp0"
set PY=D:\Programs\PsychoPy\python.exe
start "Symulator" "%PY%" narzedzia\symulator_biosygnalow.py --mode tcp --scenario mix
timeout /t 2 >nul
start "Most LSL" "%PY%" narzedzia\sim_to_lsl.py
