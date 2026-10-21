$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'
$today = Get-Date -Format 'yyyyMMdd'

"=== A. EpcLog today: shape of the data ==="
$f = Join-Path $app ('EpcLog\' + $today + '\' + $today + '.log')
"file=" + $f + "  exists=" + (Test-Path $f)
if (Test-Path $f) {
  $vals = @{}
  $perMin = @{}
  $bursts = @{}
  $raw = @{}
  $n = 0
  $fs = [System.IO.File]::Open($f, 'Open', 'Read', 'ReadWrite')
  $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8, $true)
  while (-not $sr.EndOfStream) {
    $l = $sr.ReadLine()
    if (-not $l) { continue }
    $m = [regex]::Match($l, '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}):\d{2}\.\d+\s+(\w+):(\S*)$')
    if (-not $m.Success) { continue }
    $n++
    $minute = $m.Groups[1].Value
    $key = $m.Groups[3].Value
    if (-not $vals.ContainsKey($key)) { $vals[$key] = 0; $raw[$key] = $key }
    $vals[$key] = $vals[$key] + 1
    if (-not $perMin.ContainsKey($minute)) { $perMin[$minute] = 0 }
    $perMin[$minute] = $perMin[$minute] + 1
    if (-not $bursts.ContainsKey($l.Substring(0, 19))) { $bursts[$l.Substring(0, 19)] = 0 }
    $bursts[$l.Substring(0, 19)] = $bursts[$l.Substring(0, 19)] + 1
  }
  $sr.Close(); $fs.Close()
  "lines=" + $n + "  distinct_values=" + $vals.Count
  "--- top 15 values (count, hex, ascii) ---"
  $vals.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 15 | ForEach-Object {
    $hex = $_.Key
    $ascii = ''
    if ($hex -match '^[0-9A-Fa-f]+$' -and ($hex.Length % 2) -eq 0) {
      try {
        $bytes = New-Object byte[] ($hex.Length / 2)
        for ($i = 0; $i -lt $bytes.Length; $i++) { $bytes[$i] = [Convert]::ToByte($hex.Substring($i * 2, 2), 16) }
        $ascii = ([System.Text.Encoding]::ASCII.GetString($bytes)) -replace "`0", ''
      } catch { }
    }
    "  {0,7}  {1}  =>  {2}" -f $_.Value, $hex, $ascii
  }
  "--- per-minute density (first 10 + last 10 minutes that have data) ---"
  $mins = $perMin.GetEnumerator() | Sort-Object Name
  $mins | Select-Object -First 10 | ForEach-Object { "  " + $_.Key + "  " + $_.Value }
  "  ..."
  $mins | Select-Object -Last 10 | ForEach-Object { "  " + $_.Key + "  " + $_.Value }
  "--- reads per timestamp-second (distribution) ---"
  $b = $bursts.Values | Group-Object | Sort-Object Name | ForEach-Object { "  " + $_.Name + " read(s)/sec : " + $_.Count + " second(s)" }
  $b | Select-Object -First 12
}

"=== B. Main log today: what a carton record looks like ==="
$main = Join-Path $app ('Logs\' + $today + '\Main_' + $today + '.log')
if (Test-Path $main) {
  "--- 2 sample blocks: lines containing SSCC (context around) ---"
  $hits = @(Select-String -Path $main -Pattern 'SSCC' -ErrorAction SilentlyContinue)
  "SSCC mentions: " + $hits.Count
  $hits | Select-Object -First 2 | ForEach-Object {
    $ln = $_.LineNumber
    $from = [Math]::Max(1, $ln - 3); $to = $ln + 3
    Get-Content $main | Select-Object -Skip ($from - 1) -First ($to - $from + 1) | ForEach-Object { "    " + $_.Substring(0, [Math]::Min(200, $_.Length)) }
    "    ---"
  }
}

"=== C. Weight log today: format head ==="
$w = Join-Path $app ('Logs\' + $today + '\Weight_' + $today + '.log')
if (Test-Path $w) {
  $fs2 = [System.IO.File]::Open($w, 'Open', 'Read', 'ReadWrite')
  $sr2 = New-Object System.IO.StreamReader($fs2, [System.Text.Encoding]::UTF8, $true)
  for ($i = 0; $i -lt 12 -and -not $sr2.EndOfStream; $i++) { "    " + $sr2.ReadLine() }
  $sr2.Close(); $fs2.Close()
}

"=== D. ShipPlan (per-model plan files) ==="
$sp = Join-Path $app 'ShipPlan'
$files = @(Get-ChildItem $sp -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5)
"count=" + @(Get-ChildItem $sp -File -ErrorAction SilentlyContinue).Count
foreach ($x in $files) {
  "--- " + $x.Name + " (" + $x.Length + " bytes, " + $x.LastWriteTime + ")"
  Get-Content $x.FullName -ErrorAction SilentlyContinue | Select-Object -First 12 | ForEach-Object { "    " + $_ }
}

"=== E. DataBase folder ==="
Get-ChildItem (Join-Path $app 'DataBase') -Recurse -ErrorAction SilentlyContinue |
  Select-Object LastWriteTime, Length, FullName | Format-Table -AutoSize | Out-String -Width 160
"DONE"