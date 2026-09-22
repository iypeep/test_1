<#
  fetch-tarballs.ps1 — 下载 Hermes 桌面端重建所需的 290 个 npm tarball（原始发布版）

  用法（在能访问 npm registry 的机器上）:
      powershell -ExecutionPolicy Bypass -File .\fetch-tarballs.ps1
      # 只能访问镜像时（例：npmmirror）:
      powershell -ExecutionPolicy Bypass -File .\fetch-tarballs.ps1 -Registry https://registry.npmmirror.com

  产物: .\tarballs\<registry 路径...>，可直接 commit + push 回仓库。
  每个文件都会按清单里的 sha512 校验；重跑会补齐失败的项。
#>
param(
  [string]$List = "$PSScriptRoot\missing-npm-tarballs.txt",
  [string]$Out = "$PSScriptRoot\tarballs",
  [string]$Registry = ""
)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = "SilentlyContinue"

function Get-Sha512B64([string]$Path) {
  $sha = [System.Security.Cryptography.SHA512]::Create()
  try { return [Convert]::ToBase64String($sha.ComputeHash([IO.File]::ReadAllBytes($Path))) }
  finally { $sha.Dispose() }
}

$lines = @(Get-Content $List | Where-Object { $_.Trim() })
Write-Host "清单: $($lines.Count) 个包 | 输出: $Out" -ForegroundColor Cyan

$ok = 0; $fail = @(); $i = 0
foreach ($line in $lines) {
  $i++
  $parts = $line.Split("`t")
  if ($parts.Count -lt 3) { $fail += "清单格式异常: $line"; continue }
  $name, $url, $integrity = $parts[0], $parts[1], $parts[2]

  if ($Registry) {
    $u = [Uri]$url
    $url = $Registry.TrimEnd("/") + $u.AbsolutePath
  }

  $rel  = ([Uri]$url).AbsolutePath.TrimStart("/")
  $dest = Join-Path $Out ($rel -replace "/", "\")
  New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null

  $expected = $integrity.Split("-", 2)[1]
  $done = $false
  foreach ($attempt in 1..3) {
    try {
      Invoke-WebRequest -Uri $url -OutFile $dest -TimeoutSec 180
      if ((Get-Sha512B64 $dest) -eq $expected) { $done = $true; $ok++; break }
      Write-Host "  校验不符(重试 $attempt): $name" -ForegroundColor Yellow
    } catch {
      if ($attempt -eq 3) { Write-Host "  下载失败: $name — $($_.Exception.Message)" -ForegroundColor DarkYellow }
      Start-Sleep -Seconds 2
    }
  }
  if (-not $done) { $fail += $name }
  if ($i % 25 -eq 0) { Write-Host "  进度 $i/$($lines.Count)（已校验 $ok）" }
}

Write-Host ""
Write-Host "verified: $ok / $($lines.Count)" -ForegroundColor Green
if ($fail.Count) {
  Write-Host "FAILED ($($fail.Count)):" -ForegroundColor Red
  $fail | ForEach-Object { Write-Host "  $_" }
  Write-Host "重跑本脚本即可补齐失败项。"
  exit 1
}
Write-Host "全部完成。请把 $Out 整个目录 commit + push 回本仓库。"
