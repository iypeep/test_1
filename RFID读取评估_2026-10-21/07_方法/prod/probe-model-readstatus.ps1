# probe-model-readstatus.ps1 - read-only: per-model (MODEL + CongfigSize) RFID result over a date range
# Main log blocks carry MODEL / SETTINGNAME / CongfigSize, then "RFID开启状态：True|False"
param(
  [string]$From = '20260922',
  [string]$To = '20261022'
)
$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'
$agg = @{}
$dirs = @(Get-ChildItem (Join-Path $app 'Logs') -Directory | Where-Object { $_.Name -ge $From -and $_.Name -le $To } | Sort-Object Name)
"days=" + $dirs.Count

foreach ($d in $dirs) {
  $main = Join-Path $d.FullName ('Main_' + $d.Name + '.log')
  if (-not (Test-Path $main)) { continue }
  $model = '?'; $cfg = ''; $setting = '?'
  $sr = New-Object System.IO.StreamReader([System.IO.File]::Open($main, 'Open', 'Read', 'ReadWrite'), [System.Text.Encoding]::UTF8, $true)
  while (-not $sr.EndOfStream) {
    $l = $sr.ReadLine()
    if (-not $l) { continue }
    if ($l.Contains('"MODEL"')) { $model = ($l -replace '.*:\s*"([^"]*)".*', '$1'); continue }
    if ($l.Contains('"CongfigSize"')) { $cfg = ($l -replace '.*:\s*"([^"]*)".*', '$1'); continue }
    if ($l.Contains('"SETTINGNAME"')) { $setting = ($l -replace '.*:\s*"([^"]*)".*', '$1'); continue }
    if ($l -match 'RFID开启状态[:：]\s*(True|False)') {
      $v = $Matches[1]
      $metal = if ($cfg -match 'Metal|金属') { 'Metal' } elseif ($cfg -match 'Plastic|塑料|PCV|PC\b') { 'Plastic' } else { 'NA' }
      $key = $model + "`t" + $setting + "`t" + $metal + "`t" + $cfg
      if (-not $agg.ContainsKey($key)) { $agg[$key] = @(0, 0) }
      if ($v -eq 'True') { $agg[$key][0]++ } else { $agg[$key][1]++ }
      continue
    }
  }
  $sr.Close()
  "  done " + $d.Name + "  keys=" + $agg.Count
}
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("model`tsetting`tshell`tconfig_size`tenable_on`tenable_off`toff_pct")
foreach ($k in ($agg.Keys | Sort-Object { -($agg[$_][0] + $agg[$_][1]) })) {
  $p = $k -split "`t"
  $on = $agg[$k][0]; $off = $agg[$k][1]; $n = $on + $off
  $lines.Add(($p[0], $p[1], $p[2], ($p[3] -replace "`t", ' '), $on, $off, [math]::Round(100.0 * $off / $n, 1)) -join "`t")
}
$out = Join-Path $env:LOCALAPPDATA 'OMPRemote\rfid\model_readstatus.tsv'
[System.IO.File]::WriteAllText($out, (($lines -join "`r`n") + "`r`n"), (New-Object System.Text.UTF8Encoding($false)))
"wrote=" + $out + " rows=" + ($lines.Count - 1)
"DONE"
