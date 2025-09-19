<#
release_zip.ps1 — 在 Windows 上一键打包 NanoImage 项目为干净的发布包（ZIP）
- 优先使用 git archive（仅包含已提交文件，最干净、最快）
- 若未使用 git 或有未提交文件，自动使用 robocopy 构建临时目录并 Compress-Archive
- 自动（可选）生成/更新 requirements.txt（若不存在且本地有 .venv）
- 默认排除：.venv、.git、release、__pycache__、*.pyc、.pytest_cache、node_modules、files、storage
使用：
  1) 在项目根目录，右键“使用 PowerShell 运行”或：
     pwsh -File scripts/release_zip.ps1
  2) 生成的 ZIP 位于 release/ 目录下
#>
param(
  [string]$ProjectName = "nanoimage",
  [switch]$NoFreeze
)

$ErrorActionPreference = "Stop"

function Ensure-Requirements {
  if ($NoFreeze) { return }
  if (Test-Path -Path "requirements.txt") { return }
  $pip = Join-Path ".venv/Scripts" "pip.exe"
  if (Test-Path $pip) {
    Write-Host "[info] generate requirements.txt (pip freeze)" -ForegroundColor Cyan
    & $pip freeze | Out-File -Encoding UTF8 requirements.txt
  } else {
    Write-Warning "No .venv or pip.exe found. Skip auto-generating requirements.txt. Ensure dependency file exists."
  }
}

function Use-GitArchive {
  try {
    git rev-parse --is-inside-work-tree *> $null
  } catch { return $false }
  return $true
}

function New-ReleasePaths {
  $stamp = Get-Date -Format "yyyyMMdd-HHmm"
  $releaseDir = "release"
  if (-not (Test-Path $releaseDir)) { New-Item -ItemType Directory -Path $releaseDir | Out-Null }
  $zipPath = Join-Path $releaseDir ("$ProjectName-$stamp.zip")
  return $zipPath
}

function Build-ByGitArchive {
  param([string]$ZipPath)
  Write-Host "[git] using git archive..." -ForegroundColor Green
  $prefix = "$ProjectName/"
  git archive --format=zip --output "$ZipPath" --prefix "$prefix" HEAD
}

function Build-ByCopyAndCompress {
  param([string]$ZipPath)
  Write-Host "[zip] using robocopy to stage and compress..." -ForegroundColor Green
  $tmp = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ("$ProjectName-pack-" + [System.Guid]::NewGuid()))
  $src = (Get-Location).Path
  $dst = $tmp.FullName

  # 使用 robocopy 复制并排除常见目录/文件
  $excludeDirs = @(".git", ".venv", "release", "__pycache__", ".pytest_cache", "node_modules", "files", "storage")
  $excludeFiles = @("*.pyc", ".DS_Store")
  $xd = @()
  foreach ($d in $excludeDirs) { $xd += @("/XD", (Join-Path $src $d)) }
  $xf = @()
  foreach ($f in $excludeFiles) { $xf += @("/XF", $f) }

  robocopy $src $dst /MIR /NFL /NDL /NJH /NJS /NP @xd @xf | Out-Null

  # 压缩
  Compress-Archive -Path (Join-Path $dst '*') -DestinationPath $ZipPath -Force

  # 清理
  Remove-Item -Recurse -Force $dst
}

# main
Ensure-Requirements
$zip = New-ReleasePaths
if (Use-GitArchive) {
  Build-ByGitArchive -ZipPath $zip
} else {
  Build-ByCopyAndCompress -ZipPath $zip
}

# 输出结果
$sizeMB = [Math]::Round(((Get-Item $zip).Length/1MB), 2)
Write-Host "[ok] package done -> $zip ($sizeMB MB)" -ForegroundColor Yellow
Write-Host "Next: upload via WinSCP, then SSH run:" -ForegroundColor Cyan
Write-Host "  unzip -o $([System.IO.Path]::GetFileName($zip)) && cd $ProjectName" -ForegroundColor Cyan
Write-Host "  python3 -m venv .venv && source .venv/bin/activate && pip install -U pip && pip install -r requirements.txt" -ForegroundColor Cyan
Write-Host "  python -m uvicorn api.app:app --host 0.0.0.0 --port 8000" -ForegroundColor Cyan

