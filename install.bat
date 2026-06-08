@echo off
title Instalando Separador de PDF...
echo ============================================
echo  Instalando dependencias do Separador de PDF
echo ============================================
echo.

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Instalacao concluida com sucesso!
echo  Execute run.bat para iniciar o aplicativo.
echo ============================================
pause
