$ErrorActionPreference = 'Continue'
$python = 'D:\3dgs\envs\gs-main\python.exe'
$wheels = 'D:\3dgs\installers\wheels'
$log = 'D:\3dgs\logs\offline-install.log'
if (-not (Test-Path (Join-Path $wheels 'torch-2.5.1+cu124-cp310-cp310-win_amd64.whl'))) { throw 'Missing Windows PyTorch wheel' }
& $python -m pip install --no-index --find-links=$wheels 'pip==24.3.1' 'setuptools==70.2.0' 'wheel==0.45.1' 'numpy==1.26.4' 'ninja==1.11.1.3' 'cmake==3.31.6' *>> $log
if ($LASTEXITCODE -ne 0) { throw "Build dependencies install failed: $LASTEXITCODE" }
& $python -m pip install --no-index --find-links=$wheels 'torch==2.5.1+cu124' 'torchvision==0.20.1+cu124' 'pillow' 'tqdm' 'plyfile==1.0.3' 'opencv-python-headless==4.10.0.84' 'joblib' *>> $log
if ($LASTEXITCODE -ne 0) { throw "Torch and support package install failed: $LASTEXITCODE" }
& $python -m pip check *>> $log
if ($LASTEXITCODE -ne 0) { throw 'pip check failed' }
& $python D:\3dgs\scripts\gpu-smoke.py *>> $log
if ($LASTEXITCODE -ne 0) { throw 'Torch GPU test failed' }
Get-Content $log -Tail 12
