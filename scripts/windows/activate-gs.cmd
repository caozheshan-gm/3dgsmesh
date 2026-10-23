@echo off
call D:\3dgs\BuildTools\VC\Auxiliary\Build\vcvarsall.bat x64 -vcvars_ver=14.38 >nul
if errorlevel 1 exit /b 1
call C:\ProgramData\miniconda3\condabin\conda.bat activate D:\3dgs\envs\gs-main
if errorlevel 1 exit /b 1
set "CUDA_HOME=D:\3dgs\envs\gs-main"
set "CUDA_PATH=%CUDA_HOME%"
set "PATH=%CUDA_HOME%\bin;%PATH%"
set "DISTUTILS_USE_SDK=1"
set "MAX_JOBS=4"
set "TORCH_CUDA_ARCH_LIST=8.9"
echo 3DGS environment: Python 3.10, CUDA 12.4, MSVC 14.38, RTX 4090 Laptop.
