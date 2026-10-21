$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'

function Read-EpcDay {
  param([string]$Path)
  $first = ''; $last = ''; $n = 0
  try {
    $fs = [System.IO.File]::Open($Path, 'Open', 'Read', 'ReadWrite')
    $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8, $true)
    while (-not $sr.EndOfStream) {
      $l = $sr.ReadLine()
      if ($l -and $l -match '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})') {
        if (-not $first) { $first = $matches[1] }
        $last = $matches[1]
        $n++
      }
    }
    $sr.Close(); $fs.Close()
  } catch { }
  return @{ first = $first; last = $last; count = $n }
}

"=== EpcLog history: per-day first / last / count (last 21 days) ==="
$epRoot = Join-Path $app 'EpcLog'
$rows = @()
if (Test-Path $epRoot) {
  $dirs = @(Get-ChildItem $epRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 21)
  foreach ($d in $dirs) {
    $f = Join-Path $d.FullName ($d.Name + '.log')
    if (-not (Test-Path $f)) {
      $alt = Get-ChildItem $d.FullName -File -ErrorAction SilentlyContinue | Select-Object -First 1
      if (-not $alt) { $rows += ("{0}  MISSING   (no .log inside)" -f $d.Name); continue }
      $f = $alt.FullName
    }
    $r = Read-EpcDay $f
    $rows += ("{0}  first={1}  last={2}  lines={3}  size={4}" -f $d.Name, $r.first, $r.last, $r.count, (Get-Item $f).Length)
  }
}
$rows
"total day folders: " + @(Get-ChildItem $epRoot -Directory -ErrorAction SilentlyContinue).Count

"=== other log-bearing folders in the app ==="
foreach ($d in @('Log', 'Logs', 'MES Log', 'DataBase', 'ShipPlan', 'Setting')) {
  $p = Join-Path $app $d
  if (Test-Path $p) {
    $files = @(Get-ChildItem $p -File -ErrorAction SilentlyContinue)
    $newest = $files | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    "{0,-10} files={1,-4} newest={2}  ({3} bytes)" -f $d, $files.Count, $(if ($newest) { $newest.LastWriteTime } else { '-' }), $(if ($newest) { $newest.Length } else { 0 })
  }
}
"--- Log\ file families ---"
Get-ChildItem (Join-Path $app 'Log') -File -ErrorAction SilentlyContinue |
  Group-Object { ($_.Name -replace '\d{8}', '<date>') } | Sort-Object Count -Descending |
  Select-Object Count, Name | Format-Table -AutoSize | Out-String -Width 120

"=== archived / rotated history anywhere in the app (zip/rar/7z/bak of logs) ==="
Get-ChildItem $app -Recurse -Depth 3 -Include *.zip, *.rar, *.7z, *.gz, *.bak -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match 'log|epc|main|plc|weight' } |
  Select-Object LastWriteTime, Length, FullName | Sort-Object LastWriteTime -Descending |
  Format-Table -AutoSize | Out-String -Width 200

"=== old Main/Plc/Weight logs kept on disk (before today) ==="
Get-ChildItem (Join-Path $app 'Logs') -Directory -ErrorAction SilentlyContinue |
  Sort-Object Name -Descending | Select-Object -First 10 |
  ForEach-Object {
    $s = @(Get-ChildItem $_.FullName -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum)
    "  " + $_.Name + " : " + $s.Count + " file(s), " + [int]($s.Sum / 1MB) + " MB"
  }

"=== MultiReader: does it keep logs? ==="
$mrExe = 'C:\Program Files (x86)\IMPINJ\Impinj MultiReader v6.6.12\Installer\Deliverables'
"dir exists=" + (Test-Path $mrExe)
if (Test-Path $mrExe) {
  Get-ChildItem $mrExe -Recurse -Include *.log, *.txt, *.xml, *.config -ErrorAction SilentlyContinue |
    Select-Object LastWriteTime, Length, FullName | Sort-Object LastWriteTime -Descending |
    Select-Object -First 15 | Format-Table -AutoSize | Out-String -Width 200
}
foreach ($p in @("$env:APPDATA\Impinj", "$env:LOCALAPPDATA\Impinj", 'C:\ProgramData\Impinj', 'C:\Impinj', 'D:\Impinj')) {
  if (Test-Path $p) { "--- " + $p; Get-ChildItem $p -Recurse -ErrorAction SilentlyContinue | Select-Object -First 10 LastWriteTime, Length, FullName | Format-Table -AutoSize | Out-String -Width 180 }
}

"=== Windows event log: reader/network hiccups in the last 3 days (System) ==="
try {
  $ev = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; StartTime = (Get-Date).AddDays(-3) } -ErrorAction Stop |
          Where-Object { $_.ProviderName -match 'Tcpip|Dhcp|NDIS|Netwtw|e1i|Realtek' -and $_.LevelDisplayName -in @('错误','Error','警告','Warning') })
  "matching events: " + $ev.Count
  $ev | Select-Object -First 8 TimeCreated, ProviderName, Id, LevelDisplayName | Format-Table -AutoSize | Out-String -Width 140
} catch { "event log read failed: " + $_.Exception.Message.Split("`n")[0] }
"DONE"