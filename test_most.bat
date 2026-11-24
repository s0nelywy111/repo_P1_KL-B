@echo off
REM KL-B: test mostu na liniach testowych (bez symulatora i bez LSL)
cd /d "%~dp0"
"D:\Programs\PsychoPy\python.exe" narzedzia\sim_to_lsl.py --plik narzedzia\linie_testowe.jsonl --tylko-wypisz
pause
