@echo off

SET INTERFACES_BASE_DIR=%~1
IF "%INTERFACES_BASE_DIR%"=="" (
  echo "Interfaces source dir not set!"
  exit "1"
) ELSE (
  SET SRC_ROS_MSG_DIR=%INTERFACES_BASE_DIR%
)
SET %INTERFACES_BASE_DIR%CUSTOM_PKG_NAME=%undefined%
SET %INTERFACES_BASE_DIR%%undefined%GEN_MSG_ROOT=%BASE_DIR%\genmsg
mkdir "-p" "%GEN_MSG_ROOT%"
SET %GEN_MSG_ROOT%ROS_MSG_DIR=%GEN_MSG_ROOT%/%CUSTOM_PKG_NAME%
DEL /S "%ROS_MSG_DIR%" || true
COPY  "%SRC_ROS_MSG_DIR%" "%ROS_MSG_DIR%"
IF exist "%GEN_MSG_ROOT%\std_msgs" (
  git "clone" "https://github.com/ros/std_msgs.git" "%GEN_MSG_ROOT%\std_msgs"
)
IF exist "%GEN_MSG_ROOT%\common_msgs" (
  git "clone" "https://github.com/ros/common_msgs.git" "%GEN_MSG_ROOT%\common_msgs"
)
call "%BASE_DIR%\venv\bin\activate.bat"
rospy-build "genmsg" "%ROS_MSG_DIR%" "-s" "%GEN_MSG_ROOT%"
python "-m" "pip" "install" "-e" "%ROS_MSG_DIR%"
