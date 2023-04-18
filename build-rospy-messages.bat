@echo off

SET BASE_DIR=%~dp0
SET INTERFACES_BASE_DIR=%~1

IF "%INTERFACES_BASE_DIR%"=="" (
  ECHO "Interfaces source dir not set!"
  exit "1"
) ELSE (
  SET SRC_ROS_MSG_DIR=%INTERFACES_BASE_DIR%
)

for %%i IN ("%INTERFACES_BASE_DIR%") do SET CUSTOM_PKG_NAME=%%~ni

SET GEN_MSG_ROOT=%BASE_DIR%genmsg
MD "%GEN_MSG_ROOT%"
SET ROS_MSG_DIR=%GEN_MSG_ROOT%\%CUSTOM_PKG_NAME%
DEL /F /Q /S "%ROS_MSG_DIR%"
xcopy /e /k /h /i "%SRC_ROS_MSG_DIR%" "%ROS_MSG_DIR%"
IF not exist "%GEN_MSG_ROOT%\std_msgs" (
  git "clone" "https://github.com/ros/std_msgs.git" "%GEN_MSG_ROOT%\std_msgs"
)
IF not exist "%GEN_MSG_ROOT%\common_msgs" (
  git "clone" "https://github.com/ros/common_msgs.git" "%GEN_MSG_ROOT%\common_msgs"
)
call "%BASE_DIR%\venv\Scripts\activate"
%BASE_DIR%\venv\Scripts\rospy-build "genmsg" "%ROS_MSG_DIR%" "-s" "%GEN_MSG_ROOT%"
python "-m" "pip" "install" "-e" "%ROS_MSG_DIR%"
