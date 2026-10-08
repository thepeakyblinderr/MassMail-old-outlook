@echo off
rem pushd also works when this folder is on a network (UNC) path
pushd "%~dp0"
echo Starting MassMail...
python main.py
popd
pause
