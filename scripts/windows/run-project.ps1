param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]*$')]
    [string]$Project,
    [ValidateRange(1, 30000)]
    [int]$Iterations = 7000,
    [ValidateSet(1, 2, 4, 8)]
    [int]$Resolution = 2,
    [switch]$ConvertOnly,
    [switch]$TrainOnly
)

$ErrorActionPreference = 'Stop'
if ($ConvertOnly -and $TrainOnly) { throw 'Choose either -ConvertOnly or -TrainOnly.' }

$repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$dataset = Join-Path (Join-Path $repo 'data') $Project
$input = Join-Path $dataset 'input'
$output = Join-Path (Join-Path $repo 'outputs') $Project
$official = 'D:\3dgs\apps\gaussian-src'
$colmap = 'D:\3dgs\apps\colmap-4.2.1\COLMAP.bat'
$python = 'D:\3dgs\envs\gs-main\python.exe'
$converter = Join-Path $PSScriptRoot 'convert-colmap42.py'

foreach ($file in @((Join-Path $official 'convert.py'), (Join-Path $official 'train.py'), $converter, $colmap, $python)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Required tool missing: $file" }
}

# The pinned official convert.py builds unquoted COLMAP paths internally.
if ($dataset -match '\s') { throw "Dataset path cannot contain spaces with this convert.py: $dataset" }

if (-not (Test-Path -LiteralPath $input -PathType Container)) {
    New-Item -ItemType Directory -Path $input -Force | Out-Null
    Write-Host "Created $input. Copy JPG/PNG images there and run the command again."
    exit 0
}
$photos = @(Get-ChildItem -LiteralPath $input -File | Where-Object { $_.Extension.ToLowerInvariant() -in @('.jpg', '.jpeg', '.png') })
if ($photos.Count -lt 3) { Write-Host "Found $($photos.Count) JPG/PNG images in $input; need at least 3."; exit 2 }
Write-Host "Project: $Project | input photos: $($photos.Count) | iterations: $Iterations | resolution: $Resolution"
if ($photos.Count -gt 300 -and -not $TrainOnly) {
    Write-Warning 'Official convert.py uses exhaustive matching. More than 300 photos may take a long time; select frames first.'
}

if (-not $TrainOnly) {
    foreach ($subdir in @('distorted', 'sparse', 'images')) {
        if (Test-Path -LiteralPath (Join-Path $dataset $subdir)) {
            throw "Conversion output already exists: $(Join-Path $dataset $subdir). Use -TrainOnly after checking it, or start a new project name."
        }
    }
    Write-Host 'Step 1/2: official convert.py (COLMAP feature extraction, matching, mapping, undistortion)'
    & $python $converter -s $dataset --colmap_executable $colmap
    if ($LASTEXITCODE -ne 0) { throw "convert.py failed with exit code $LASTEXITCODE" }
}

$images = Join-Path $dataset 'images'
$sparse = Join-Path $dataset 'sparse\0'
foreach ($file in @((Join-Path $sparse 'cameras.bin'), (Join-Path $sparse 'images.bin'), (Join-Path $sparse 'points3D.bin'))) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "COLMAP result missing: $file" }
}
if (-not (Test-Path -LiteralPath $images -PathType Container)) { throw "Undistorted images missing: $images" }
Write-Host "COLMAP output: $sparse"

if ($ConvertOnly) {
    Write-Host 'Conversion complete. Inspect camera coverage before training, then run with -TrainOnly.'
    exit 0
}

if (Test-Path -LiteralPath $output) {
    if (@(Get-ChildItem -LiteralPath $output -Force).Count -gt 0) {
        throw "Training output is not empty: $output. Use a new project name or move the old output before retrying."
    }
} else {
    New-Item -ItemType Directory -Path $output -Force | Out-Null
}

Write-Host 'Step 2/2: official train.py (3D Gaussian Splatting)'
Push-Location $official
try {
    & $python train.py -s $dataset -m $output --iterations $Iterations --resolution $Resolution --data_device cpu --disable_viewer --test_iterations $Iterations
    if ($LASTEXITCODE -ne 0) { throw "train.py failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}
$ply = Join-Path $output "point_cloud\iteration_$Iterations\point_cloud.ply"
if (-not (Test-Path -LiteralPath $ply -PathType Leaf)) { throw "Training ended but PLY is missing: $ply" }
Write-Host "3DGS model: $ply"
