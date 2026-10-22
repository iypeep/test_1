# extract-epc-tags.ps1 - read-only: EpcLog -> only NON-resident EPC reads (product tags), with timestamps
# resident device/fixture tags are excluded by value; everything else is kept as-is
param(
  [string]$From = '',
  [string]$To = '',
  [string]$Out = ''
)
$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'
$logRoot = Join-Path $app 'EpcLog'
$today = Get-Date -Format 'yyyyMMdd'
if (-not $To) { $To = $today }
if (-not $From) { $From = (Get-Date).AddDays(-30).ToString('yyyyMMdd') }
if (-not $Out) { $Out = Join-Path $env:LOCALAPPDATA ('OMPRemote\rfid\epctags_' + $From + '_' + $To + '.tsv') }

$resident = @{
  '4130333730303130303030373100' = 'A037001000071'
  '4230313930303130303132323900' = 'B019001001229'
  '4130333730303130303031353000' = 'A037001000150'
}

$dirs = @(Get-ChildItem $logRoot -Directory | Where-Object { $_.Name -ge $From -and $_.Name -le $To } | Sort-Object Name)
"days=" + $dirs.Count
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("day`tt`tepc`tascii`tkind`trssi")
$perDay = @{}

foreach ($d in $dirs) {
  $f = Join-Path $d.FullName ($d.Name + '.log')
  if (-not (Test-Path $f)) { continue }
  $n = 0; $kept = 0
  $sr = New-Object System.IO.StreamReader([System.IO.File]::Open($f, 'Open', 'Read', 'ReadWrite'), [System.Text.Encoding]::UTF8, $true)
  while (-not $sr.EndOfStream) {
    $l = $sr.ReadLine()
    if (-not $l) { continue }
    $m = [regex]::Match($l, '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\s+(\w*):(\S*)$')
    if (-not $m.Success) { continue }
    $n++
    $v = $m.Groups[3].Value
    if ($resident.ContainsKey($v)) { continue }
    $ascii = ''
    if ($v -match '^[0-9A-Fa-f]+$' -and ($v.Length % 2) -eq 0 -and $v.Length -le 48) {
      try {
        $bytes = New-Object byte[] ($v.Length / 2)
        for ($i = 0; $i -lt $bytes.Length; $i++) { $bytes[$i] = [Convert]::ToByte($v.Substring($i * 2, 2), 16) }
        $ascii = ([System.Text.Encoding]::ASCII.GetString($bytes)) -replace "[^\x20-\x7E]", ''
      } catch { }
    }
    $lines.Add(($d.Name + "`t" + $m.Groups[1].Value + "`t" + $v + "`t" + $ascii + "`t" + $m.Groups[2].Value + "`t"))
    $kept++
  }
  $sr.Close()
  $perDay[$d.Name] = @($n, $kept)
  "  " + $d.Name + "  lines=" + $n + "  kept=" + $kept
}
[System.IO.File]::WriteAllText($Out, (($lines -join "`r`n") + "`r`n"), (New-Object System.Text.UTF8Encoding($false)))
"wrote=" + $Out + "  rows=" + ($lines.Count - 1) + "  bytes=" + (Get-Item $Out).Length
"DONE"
