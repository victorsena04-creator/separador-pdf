@echo off
title Separador de PDF
python app.py
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao iniciar o aplicativo.
    echo Certifique-se de executar install.bat primeiro.
    pause
)
