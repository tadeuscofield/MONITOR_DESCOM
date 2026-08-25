@echo off
set PYTHONUTF8=1
cd /d "%~dp0"
echo ===== %date% %time% ===== >> historico\captura_log.txt
python capturar_anp.py >> historico\captura_log.txt 2>&1
