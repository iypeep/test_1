# probe-rfid-history.ps1 - read-only: per-day readStatus True/False from the app's own Rfid logs
# plus the RFID-related SettingPrm.xml values (file is NUL-padded, so parse textually)
$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'

"=== SettingPrm.xml: RFID-related values (NULs stripped) ==="
$p = Join-Path $app 'Setting\SettingPrm.xml'
$raw = [System.IO.File]::ReadAllText($p).Replace([string][char]0, '')
"--- full (stripped) ---"
$raw.Trim()
"--- end ---"

"=== Rfid logs available ==="
$logs = @(Get-ChildItem (Join-Path $app 'Logs') -Directory |
    Sort-Object Name |
    ForEach-Object {
      $f = Join-Path $_.FullName ('Rfid_' + $_.Name + '.log')
      if (Test-Path $f) { [pscustomobject]@{ Day = $_.Name; File = $f; KB = [math]::Round((Get-Item $f).Length / 1KB, 0) } }
    })
"days_with_rfid_log=" + $logs.Count + "  first=" + $(if ($logs.Count) { $logs[0].Day } else { '-' }) + "  last=" + $(if ($logs.Count) { $logs[-1].Day } else { '-' })

"=== per-day readStatus / 读取到标签 / ReaderStop=NG ==="
"day`tTrue`tFalse`tTrue%`tTagLines`tStopNG"
foreach ($L in $logs) {
  $t = 0; $f = 0; $tag = 0; $ng = 0
  foreach ($l in [System.IO.File]::ReadLines($L.File)) {
    if ($l -match 'readStatus=True') { $t++ }
    elseif ($l -match 'readStatus=False') { $f++ }
    if ($l -match '读取到标签') { $tag++ }
    if ($l -match 'ReaderStop=NG') { $ng++ }
  }
  $pct = if (($t + $f) -gt 0) { [math]::Round(100.0 * $t / ($t + $f), 1) } else { 0 }
  "" + $L.Day + "`t" + $t + "`t" + $f + "`t" + $pct + "`t" + $tag + "`t" + $ng
}
"DONE"
