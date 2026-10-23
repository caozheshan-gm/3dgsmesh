@echo off
call D:\3dgs\scripts\activate-gs.cmd
if errorlevel 1 exit /b 1
cd /d D:\3dgs\apps\gaussian-src
python -m pip install --no-index --no-build-isolation --no-deps ./submodules/diff-gaussian-rasterization ./submodules/simple-knn ./submodules/fused-ssim
exit /b %ERRORLEVEL%
