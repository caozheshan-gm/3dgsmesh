@echo off
call D:\3dgs\scripts\activate-gs.cmd
if errorlevel 1 exit /b 1
cd /d D:\3dgs\apps\gaussian-src
python train.py -s D:\3dgs\data\smoke-room-undistorted -m D:\3dgs\runs\smoke-room-50 --iterations 50 --resolution 1 --data_device cpu --disable_viewer --test_iterations 25 50 --save_iterations 50
exit /b %ERRORLEVEL%
