@echo off

SET BASE_DIR=%~dp0

python "-m" "pip" "install" "virtualenv"
python "-m" "venv" "%BASE_DIR%\venv"
call "%BASE_DIR%\venv\Scripts\activate.bat"
python "-m" "pip" "install" "--upgrade" "pip" "setuptools"
python "-m" "pip" "install" "-r" "%BASE_DIR%\requirements.txt"
