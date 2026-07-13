@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo       Tutoria - Preparacao local
echo ========================================

where python >nul 2>nul
if errorlevel 1 (
    echo Python nao foi encontrado no computador.
    echo Instale o Python e marque a opcao Add Python to PATH.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 goto erro
)

rem O .env nao vem no GitHub (tem segredo). Criamos um a partir do exemplo.
rem Sem OPENAI_API_KEY o chat roda em modo de demonstracao, sem quebrar.
if not exist ".env" (
    echo Criando arquivo .env a partir do .env.example...
    copy ".env.example" ".env" >nul
)

echo Instalando dependencias...
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro

if not exist "instance\tutoria.db" (
    echo Criando banco SQLite...
    "venv\Scripts\python.exe" db\inicializar_sqlite.py
    if errorlevel 1 goto erro
)

echo.
echo Servidor iniciado em http://localhost:5000
echo Para encerrar, pressione Ctrl+C.
echo.
"venv\Scripts\python.exe" run.py
exit /b 0

:erro
echo.
echo Nao foi possivel preparar o projeto.
echo Confira as mensagens acima.
pause
exit /b 1
