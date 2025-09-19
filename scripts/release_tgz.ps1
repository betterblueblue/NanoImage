<#
release_tgz.ps1 — 在 Windows 上使用内置 tar 打包为 .tgz（排除虚拟环境/缓存等）
用法：
  pwsh -File scripts/release_tgz.ps1 [-ProjectName nanoimage]
生成文件：release/<ProjectName>-<yyyyMMdd-HHmm>.tgz
#>
param([string]$ProjectName = "nanoimage")
$ErrorActionPreference = "Stop"

# 输出文件
$stamp = Get-Date -Format "yyyyMMdd-HHmm"
$releaseDir = "release"
if (-not (Test-Path $releaseDir)) { New-Item -ItemType Directory -Path $releaseDir | Out-Null }
$out = Join-Path $releaseDir ("$ProjectName-$stamp.tgz")

# 排除列表（目录与文件）
$excludes = @(
  "--exclude=.git", "--exclude=.venv", "--exclude=release", "--exclude=files", "--exclude=storage",
  "--exclude=**/__pycache__", "--exclude=**/*.pyc", "--exclude=.pytest_cache", "--exclude=node_modules"
)

# 使用 tar 打包当前目录
& tar -czf $out $excludes .

# 结果提示
$sizeMB = [Math]::Round(((Get-Item $out).Length/1MB), 2)
Write-Host "[ok] 打包完成 -> $out ($sizeMB MB)" -ForegroundColor Yellow
Write-Host "下一步：上传到服务器后，SSH 执行：" -ForegroundColor Cyan
Write-Host "  tar -xzf $([System.IO.Path]::GetFileName($out))" -ForegroundColor Cyan
Write-Host "  python3 -m venv .venv && source .venv/bin/activate && pip install -U pip && pip install -r requirements.txt" -ForegroundColor Cyan
Write-Host "  python -m uvicorn api.app:app --host 0.0.0.0 --port 8000" -ForegroundColor Cyan

