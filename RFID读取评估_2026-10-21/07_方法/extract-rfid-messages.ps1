$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'
$today = Get-Date -Format 'yyyyMMdd'
$main = Join-Path $app ('Logs\' + $today + '\Main_' + $today + '.log')
$gbk = [System.Text.Encoding]::GetEncoding(936)

"=== distinct RFID-related message templates today (numbers normalised) ==="
$tpl = @{}
$fs = [System.IO.File]::Open($main, 'Open', 'Read', 'ReadWrite')
$sr = New-Object System.IO.StreamReader($fs, $gbk, $true)
while (-not $sr.EndOfStream) {
  $l = $sr.ReadLine(); if (-not $l) { continue }
  if ($l -notmatch 'Rfid|RFID|Epc|EPC|标签|读取') { continue }
  $m = [regex]::Match($l, '^\S+ \S+ \[\d+\] \w+\s+-\s+(.*)$')
  $body = if ($m.Success) { $m.Groups[1].Value } else { $l }
  $norm = $body -replace '\d+', '#' -replace '\s+', ' '
  if ($norm.Length -gt 120) { $norm = $norm.Substring(0, 120) }
  if (-not $tpl.ContainsKey($norm)) { $tpl[$norm] = 0 }
  $tpl[$norm]++
}
$sr.Close(); $fs.Close()
$tpl.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 25 | ForEach-Object { "  {0,7}  {1}" -f $_.Value, $_.Key }

"=== raw RFID lines around a good cycle (15:00:40 - 15:01:20) ==="
$fs = [System.IO.File]::Open($main, 'Open', 'Read', 'ReadWrite')
$sr = New-Object System.IO.StreamReader($fs, $gbk, $true)
$n = 0
while (-not $sr.EndOfStream -and $n -lt 60) {
  $l = $sr.ReadLine(); if (-not $l) { continue }
  if ($l -match '^2026-10-21 15:00:(4\d|5\d)|^2026-10-21 15:01:[0-1]\d') {
    if ($l -match 'Rfid|RFID|Epc|EPC|标签|SSCC|读取|校验') {
      $n++
      "  " + $l.Substring(0, [Math]::Min(180, $l.Length))
    }
  }
}
$sr.Close(); $fs.Close()

"=== how many tags does the app expect vs read? (look for count words) ==="
$patterns = @('读取到','读取数量','标签数','Epc数量','EPC数量','校验','比对','匹配')
foreach ($p in $patterns) {
  $c = @(Select-String -Path $main -Pattern $p -ErrorAction SilentlyContinue).Count
  "  " + $p + " : " + $c + " line(s)"
}
"DONE"