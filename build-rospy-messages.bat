@echo off

SET BASE_DIR=%~dp0
SET SOURCES_PATH=%~1

IF "%SOURCES_PATH%"=="" (
  SET SOURCES_PATH=%BASE_DIR%source_list.json
)
SET GEN_MSG_ROOT=%BASE_DIR%genmsg
call "%BASE_DIR%\venv\Scripts\activate"
python "%BASE_DIR%\clone_repos.py" "%SOURCES_PATH%" "%GEN_MSG_ROOT%"
python "%BASE_DIR%\generate_messages.py" "%SOURCES_PATH%" "%GEN_MSG_ROOT%"
