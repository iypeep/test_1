# extract-rfid-boxes2.ps1 - read-only: app Rfid_*.log -> one TSV row per box (tab separated; timestamps contain commas)
# usage: extract-rfid-boxes2.ps1 [-From 20260923] [-To 20261022] [-Out <path>]
param(
  [string]$From = '',
  [string]$To = '',
  [string]$Out = ''
)
$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'
$logRoot = Join-Path $app 'Logs'
if (-not $To) { $To = Get-Date -Format 'yyyyMMdd' }
if (-not $From) { $From = (Get-Date).AddDays(-30).ToString('yyyyMMdd') }
if (-not $Out) { $Out = Join-Path $env:LOCALAPPDATA ('OMPRemote\rfid\rfidboxes2_' + $From + '_' + $To + '.tsv') }

$dirs = @(Get-ChildItem $logRoot -Directory | Where-Object { $_.Name -ge $From -and $_.Name -le $To } | Sort-Object Name)
"days=" + $dirs.Count

$hdr = @('day', 'seq', 't_first', 't_status', 'delay_ms', 'dsn_n', 'dsn_ids', 'sscc', 'tag_lines', 'tag_distinct', 'tag_ids', 'status', 'rstart', 'rstop', 'heads')
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add(($hdr -join "`t"))

foreach ($d in $dirs) {
  $f = Join-Path $d.FullName ('Rfid_' + $d.Name + '.log')
  if (-not (Test-Path $f)) { continue }
  $seq = 0
  $rec = $null
  $heads = 0

  function New-Rec { return [ordered]@{ t_first = ''; tags = (New-Object System.Collections.Generic.List[string]); dsn = (New-Object System.Collections.Generic.List[string]); sscc = ''; tag_lines = 0; status = ''; rstart = ''; rstop = ''; t_status = '' } }
  function Flush-Rec($day, $rec, $seq, $heads) {
    if ($null -eq $rec) { return }
    if (-not $rec.status -and -not $rec.t_first) { return }
    $delay = ''
    if ($rec.t_first -and $rec.t_status) {
      try {
        $a = [datetime]::ParseExact($rec.t_first, 'yyyy-MM-dd HH:mm:ss,fff', $null)
        $b = [datetime]::ParseExact($rec.t_status, 'yyyy-MM-dd HH:mm:ss,fff', $null)
        $delay = [int]([math]::Round(($b - $a).TotalMilliseconds))
      } catch { }
    }
    $tagU = @($rec.tags | Select-Object -Unique)
    $row = @(
      $day, $seq, $rec.t_first, $rec.t_status, $delay,
      $rec.dsn.Count, (($rec.dsn | Select-Object -Unique) -join '|'),
      $rec.sscc, $rec.tag_lines, $tagU.Count, ($tagU -join '|'),
      $rec.status, $rec.rstart, $rec.rstop, $heads
    )
    $lines.Add(($row -join "`t"))
  }

  $sr = New-Object System.IO.StreamReader([System.IO.File]::Open($f, 'Open', 'Read', 'ReadWrite'), [System.Text.Encoding]::UTF8, $true)
  while (-not $sr.EndOfStream) {
    $l = $sr.ReadLine()
    if (-not $l) { continue }
    if ($l.Trim() -eq '[Head]') { $heads++; continue }
    $m = [regex]::Match($l, '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[\d+\] INFO\s+-\s*(.*)$')
    if (-not $m.Success) { continue }
    $t = $m.Groups[1].Value
    $body = $m.Groups[2].Value.Trim()

    if ($body -match '^readStatus=(True|False)') {
      if ($null -eq $rec) { $rec = New-Rec }
      $rec.status = $Matches[1]
      $rec.t_status = $t
      if (-not $rec.t_first) { $rec.t_first = $t }
      continue
    }
    if ($body -match '^ReaderStop=(OK|NG)') {
      if ($null -eq $rec) { $rec = New-Rec }
      $rec.rstop = $Matches[1]
      $seq++
      Flush-Rec $d.Name $rec $seq $heads
      $rec = $null
      continue
    }
    if ($body -match '^ReaderStart') {
      if ($null -eq $rec) { $rec = New-Rec }
      $rec.rstart = $body
      continue
    }
    if ($body -match '^读取到标签[:：]\s*(\S+)') {
      if ($null -eq $rec) { $rec = New-Rec }
      $rec.tags.Add($Matches[1]); $rec.tag_lines++
      if (-not $rec.t_first) { $rec.t_first = $t }
      continue
    }
    if ($body -match '^\d{20}$') {
      if ($null -eq $rec) { $rec = New-Rec }
      if (-not $rec.sscc) { $rec.sscc = $body }
      if (-not $rec.t_first) { $rec.t_first = $t }
      continue
    }
    if ($body -match '^GN[0-9A-Z]{6,}$') {
      if ($null -eq $rec) { $rec = New-Rec }
      $rec.dsn.Add($body)
      if (-not $rec.t_first) { $rec.t_first = $t }
      continue
    }
  }
  if ($null -ne $rec) { $seq++; Flush-Rec $d.Name $rec $seq $heads }
  $sr.Close()
  "  " + $d.Name + "  seq=" + $seq
}
$txt = ($lines -join "`r`n") + "`r`n"
[System.IO.File]::WriteAllText($Out, $txt, (New-Object System.Text.UTF8Encoding($false)))
"wrote=" + $Out + "  bytes=" + (Get-Item $Out).Length + "  rows=" + ($lines.Count - 1)
"DONE"
