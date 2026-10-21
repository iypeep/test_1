$ErrorActionPreference = 'Continue'

"=== 1. HQ Package System V2 layout (depth 2) ==="
$app = 'D:\HQ Package System V2'
Get-ChildItem -Path $app -Directory -ErrorAction SilentlyContinue |
  Select-Object Name, LastWriteTime | Format-Table -AutoSize | Out-String -Width 160
"--- top-level files ---"
Get-ChildItem -Path $app -File -ErrorAction SilentlyContinue |
  Select-Object Name, Length, LastWriteTime | Sort-Object LastWriteTime -Descending |
  Format-Table -AutoSize | Out-String -Width 160

"=== 2. config files mentioning rfid/epc/reader/llrp/antenna/impinj ==="
$cfgHits = @(Get-ChildItem -Path $app -Recurse -Depth 2 -Include *.config, *.xml, *.json, *.ini, *.txt, *.yaml -ErrorAction SilentlyContinue |
             Where-Object { $_.Length -lt 2MB })
foreach ($f in $cfgHits) {
  $m = @(Select-String -Path $f.FullName -Pattern 'rfid|epc|reader|llrp|antenna|impinj|5084' -AllMatches -ErrorAction SilentlyContinue)
  if ($m.Count -gt 0) {
    "--- " + $f.FullName + "  (" + $m.Count + " hits)"
    $m | Select-Object -First 6 | ForEach-Object { "    L" + $_.LineNumber + ": " + $_.Line.Trim() }
  }
}

"=== 3. RFID keywords in today's logs ==="
$today = Get-Date -Format 'yyyyMMdd'
foreach ($log in @(Get-ChildItem -Path (Join-Path $app 'Logs') -Recurse -Include *.log -ErrorAction SilentlyContinue |
                   Where-Object { $_.LastWriteTime -ge (Get-Date).AddDays(-1) })) {
  $epc = @(Select-String -Path $log.FullName -Pattern 'Rfid|EPC|Epc|RSSI|Antenna|SSCC' -ErrorAction SilentlyContinue)
  "--- " + $log.FullName + " : " + $epc.Count + " rfid-ish hits (of " + (Get-Content $log.FullName -ErrorAction SilentlyContinue | Measure-Object).Count + " lines)"
  $epc | Select-Object -Last 5 | ForEach-Object { "    L" + $_.LineNumber + ": " + $_.Line.Trim() }
}

"=== 4. is anything talking LLRP (5084) right now? ==="
Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $_.RemotePort -eq 5084 -or $_.LocalPort -eq 5084 } |
  Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess |
  Format-Table -AutoSize | Out-String -Width 160
"--- readers visible in ARP (192.168.1.x) ---"
Get-NetNeighbor -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object { $_.IPAddress -like '192.168.*' -or $_.IPAddress -like '10.22.196.*' } |
  Select-Object IPAddress, LinkLayerAddress, State | Sort-Object IPAddress | Format-Table -AutoSize | Out-String -Width 120

"=== 5. Impinj settings in the registry (MultiReader remembers its reader there) ==="
foreach ($k in @('HKCU:\Software\Impinj', 'HKLM:\SOFTWARE\WOW6432Node\Impinj', 'HKLM:\SOFTWARE\Impinj')) {
  if (Test-Path $k) {
    "--- " + $k
    Get-ChildItem $k -Recurse -ErrorAction SilentlyContinue | Select-Object -First 12 | ForEach-Object { "    " + $_.Name }
  }
}
try {
  $mr = Get-ItemProperty 'HKCU:\Software\Impinj\MultiReader' -ErrorAction Stop
  $mr | Format-List | Out-String -Width 200
} catch { "no HKCU MultiReader key" }

"=== 6. Ben Read RFID folder (the reader app that talks LLRP) ==="
Get-ChildItem -Path 'D:\Ben Read RFID' -Recurse -ErrorAction SilentlyContinue |
  Select-Object @{n='Type';e={if($_.PSIsContainer){'DIR'}else{'FILE'}}}, LastWriteTime, Length, FullName |
  Format-Table -AutoSize | Out-String -Width 200
"--- its .exe/.config files ---"
Get-ChildItem -Path 'D:\Ben Read RFID' -Recurse -Include *.config, *.exe, *.ini, *.xml -ErrorAction SilentlyContinue |
  Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize | Out-String -Width 200

"=== 7. running processes: reader-related ==="
Get-Process | Where-Object { $_.ProcessName -match 'MultiReader|Ben|Reader|Hsl|Package' } |
  Select-Object ProcessName, Id, Path | Format-Table -AutoSize | Out-String -Width 200
"DONE"