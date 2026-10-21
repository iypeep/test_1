$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'
$epRoot = Join-Path $app 'EpcLog'

function Last-StampOf {
  param([string]$Path)
  $last = ''
  try {
    $fs = [System.IO.File]::Open($Path, 'Open', 'Read', 'ReadWrite')
    $take = [Math]::Min($fs.Length, 256KB)
    $fs.Position = [Math]::Max(0, $fs.Length - $take)
    $buf = New-Object byte[] $take
    [void]$fs.Read($buf, 0, $take)
    $fs.Close()
    $txt = [System.Text.Encoding]::UTF8.GetString($buf)
    foreach ($m in [regex]::Matches($txt, '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')) { $last = $m.Value }
  } catch { }
  return $last
}

"=== outage screen: last 30 days, days that stopped before 21:00 ==="
$today = Get-Date
$suspect = @()
$all = @(Get-ChildItem $epRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending)
"day folders on disk: " + $all.Count
$sum = 0
foreach ($d in $all) { $sum += (@(Get-ChildItem $d.FullName -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum) }
"EpcLog total size: " + [int]($sum / 1MB) + " MB"

foreach ($d in ($all | Select-Object -First 30)) {
  $f = Join-Path $d.FullName ($d.Name + '.log')
  if (-not (Test-Path $f)) {
    $alt = Get-ChildItem $d.FullName -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $alt) { continue }
    $f = $alt.FullName
  }
  $last = Last-StampOf $f
  $isToday = ($d.Name -eq $today.ToString('yyyyMMdd'))
  if (-not $last) { "  " + $d.Name + "  last=<none>"; continue }
  $lt = [datetime]$last
  $flag = ''
  if ($lt.Hour -lt 21 -and -not $isToday) { $flag = '  <-- stopped early'; $suspect += ($d.Name + ' ' + $last) }
  if ($isToday) { $flag = '  (today, still running? last write ' + $last + ')' }
  "  " + $d.Name + "  last=" + $last + $flag
}
"early stops (excluding today): " + $suspect.Count
$suspect | ForEach-Object { "    " + $_ }

"=== disk footprint / free space ==="
foreach ($dl in @(Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 })) {
  "  " + $dl.DeviceID + " free=" + [int]($dl.FreeSpace / 1GB) + " GB / total=" + [int]($dl.Size / 1GB) + " GB"
}
foreach ($p in @('EpcLog', 'Logs', 'Log', 'DataBase')) {
  $full = Join-Path $app $p
  if (Test-Path $full) {
    $s = @(Get-ChildItem $full -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum)
    "  " + $p.PadRight(9) + " " + [int]($s.Sum / 1MB) + " MB in " + $s.Count + " file(s)"
  }
}

"=== biggest single files in the app (top 6) ==="
Get-ChildItem $app -Recurse -File -ErrorAction SilentlyContinue |
  Sort-Object Length -Descending | Select-Object -First 6 @{n='MB';e={[int]($_.Length/1MB)}}, LastWriteTime, FullName |
  Format-Table -AutoSize | Out-String -Width 190
"DONE"