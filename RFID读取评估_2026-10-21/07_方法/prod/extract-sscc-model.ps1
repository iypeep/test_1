# extract-sscc-model.ps1 - read-only: map carton SSCC -> MODEL / SETTINGNAME from Main logs
param(
  [string]$From = '20260922',
  [string]$To = '20261022'
)
$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'
$map = @{}
$dirs = @(Get-ChildItem (Join-Path $app 'Logs') -Directory | Where-Object { $_.Name -ge $From -and $_.Name -le $To } | Sort-Object Name)
"days=" + $dirs.Count
foreach ($d in $dirs) {
  $main = Join-Path $d.FullName ('Main_' + $d.Name + '.log')
  if (-not (Test-Path $main)) { continue }
  $model = ''; $setting = ''; $cfg = ''
  $sr = New-Object System.IO.StreamReader([System.IO.File]::Open($main, 'Open', 'Read', 'ReadWrite'), [System.Text.Encoding]::UTF8, $true)
  while (-not $sr.EndOfStream) {
    $l = $sr.ReadLine()
    if (-not $l) { continue }
    if ($l.Contains('"MODEL"')) { $model = ($l -replace '.*:\s*"([^"]*)".*', '$1'); continue }
    if ($l.Contains('"SETTINGNAME"')) { $setting = ($l -replace '.*:\s*"([^"]*)".*', '$1'); continue }
    if ($l.Contains('"CongfigSize"')) { $cfg = ($l -replace '.*:\s*"([^"]*)".*', '$1'); continue }
    if ($l.Contains('"SSCC"')) {
      $v = ($l -replace '.*:\s*"([^"]*)".*', '$1')
      if ($v -match '^\d{20}$' -and $model) {
        if (-not $map.ContainsKey($v)) { $map[$v] = @($model, $setting, $cfg) }
      }
      continue
    }
  }
  $sr.Close()
  "  done " + $d.Name + "  sscc=" + $map.Count
}
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("sscc`tmodel`tsetting`tconfig_size")
foreach ($k in $map.Keys) {
  $v = $map[$k]
  $lines.Add(($k, $v[0], $v[1], ($v[2] -replace "`t", ' ')) -join "`t")
}
$out = Join-Path $env:LOCALAPPDATA 'OMPRemote\rfid\sscc_model.tsv'
[System.IO.File]::WriteAllText($out, (($lines -join "`r`n") + "`r`n"), (New-Object System.Text.UTF8Encoding($false)))
"wrote=" + $out + " rows=" + ($lines.Count - 1)
"DONE"
