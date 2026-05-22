@echo off
setlocal

set "NODE14_HOME=%NODE14_HOME%"
if "%NODE14_HOME%"=="" set "NODE14_HOME=C:\tools\node-v14.21.3-win-x64"

if not exist "%NODE14_HOME%\node.exe" (
  echo [ERROR] Node14 not found: %NODE14_HOME%\node.exe
  echo Please install Node.js 14.21.3 or set NODE14_HOME to your Node14 directory.
  exit /b 1
)

set "PATH=%NODE14_HOME%;%PATH%"
"%NODE14_HOME%\node.exe" %*
