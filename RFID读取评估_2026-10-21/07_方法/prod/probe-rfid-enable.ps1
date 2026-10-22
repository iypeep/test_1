# probe-rfid-enable.ps1 - read-only: per-box "RFID开启状态" ratio, split by hour and by model
# usage: probe-rfid-enable.ps1 [-Date 20261022]
param([string[]]$Date = @('20261021', '20261022'))
$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'

foreach ($d in $Date) {
  $main = Join-Path $app ("Logs\" + $d + "\Main_" + $d + ".log")
  "==== $d  exists=" + (Test-Path $main)
  if (-not (Test-Path $main)) { continue }
  $lines = [System.IO.File]::ReadAllLines($main, [System.Text.Encoding]::UTF8)

  $hour = @{}          # hour -> [flows, on, off]
  $model = @{}         # SETTINGNAME -> [on, off]
  $flowStart = 0; $on = 0; $off = 0
  $lastModel = '?'

  for ($i = 0; $i -lt $lines.Length; $i++) {
    $l = $lines[$i]
    if ($l -match '"SETTINGNAME"\s*:\s*"([^"]+)"') { $lastModel = $Matches[1]; continue }
    if ($l -notmatch 'RFID开启状态') { continue }
    $ts = ''
    if ($l -match '^(\d{4}-\d{2}-\d{2} \d{2}):') { $ts = $Matches[1] }
    if (-not $hour.ContainsKey($ts)) { $hour[$ts] = @(0, 0, 0) }
    $hour[$ts][0]++
    if (-not $model.ContainsKey($lastModel)) { $model[$lastModel] = @(0, 0) }
    if ($l -match 'RFID开启状态[:：]\s*True') { $hour[$ts][1]++; $model[$lastModel][0]++; $on++ }
    else { $hour[$ts][2]++; $model[$lastModel][1]++; $off++ }
  }
  "  totals: enable_lines=" + ($on + $off) + "  on=" + $on + "  off=" + $off + "  off_ratio=" + $(if (($on + $off) -gt 0) { [math]::Round(100.0 * $off / ($on + $off), 1) } else { 0 }) + "%"
  "  --- by hour ---"
  $hour.GetEnumerator() | Sort-Object Name | ForEach-Object {
    $r = if (($_.Value[0]) -gt 0) { [math]::Round(100.0 * $_.Value[2] / $_.Value[0], 1) } else { 0 }
    "  " + $_.Key + "  flows=" + $_.Value[0] + "  on=" + $_.Value[1] + "  off=" + $_.Value[2] + "  off%=" + $r
  }
  "  --- by model (top 12 by volume) ---"
  $model.GetEnumerator() | Sort-Object { $_.Value[0] + $_.Value[1] } -Descending | Select-Object -First 12 | ForEach-Object {
    $t = $_.Value[0] + $_.Value[1]
    $r = if ($t -gt 0) { [math]::Round(100.0 * $_.Value[1] / $t, 1) } else { 0 }
    "  " + $_.Key + "  on=" + $_.Value[0] + "  off=" + $_.Value[1] + "  off%=" + $r
  }
}
"DONE"
