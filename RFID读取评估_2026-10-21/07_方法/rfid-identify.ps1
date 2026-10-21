$ErrorActionPreference = 'Continue'
$hub = '\\10.32.134.128\mbd3md3_basin\TBZ\_omp\machines\7H3AA-PALLET\rfid'

"=== ask our monitor to release the reader ==="
Set-Content -Path (Join-Path $hub 'control.json') -Value '{"mode":"pause"}' -Encoding ASCII
Start-Sleep -Seconds 5

"=== reflect what the report config can include ==="
Add-Type -Path 'D:\Ben Read RFID\Impinj.OctaneSdk.dll' 2>$null
Add-Type -Path 'D:\Ben Read RFID\LLRP.dll' 2>$null
[Impinj.OctaneSdk.ReportConfig].GetProperties() | ForEach-Object { "  ReportConfig." + $_.Name + " : " + $_.PropertyType.Name }
"--- TagModelDetails ---"
[Impinj.OctaneSdk.TagModelDetails].GetProperties() | ForEach-Object { "  " + $_.Name + " : " + $_.PropertyType.Name }

"=== read tags directly (EPC + TID + model) for 3 seconds ==="
$ip = '192.168.1.100'
$cfg = 'D:\HQ Package System V2\Setting\SettingPrm.xml'
if (Test-Path $cfg) {
  $raw = [System.IO.File]::ReadAllText($cfg) -replace "`0", ''
  $m = [regex]::Match($raw, '<rfidSetting>\s*<Ip>([^<]+)</Ip>')
  if ($m.Success) { $ip = $m.Groups[1].Value.Trim() }
}
try {
  $r = New-Object Impinj.OctaneSdk.ImpinjReader
  $r.Connect($ip)
  $st = $r.QueryDefaultSettings()
  try { $st.Report.IncludeAntennaPortNumber = $true } catch { }
  try { $st.Report.IncludePeakRssi = $true } catch { }
  try { $st.Report.IncludeTid = $true } catch { "  (no IncludeTid property)" }
  try { $st.Report.IncludeSerializedTid = $true } catch { }
  $r.ApplySettings($st)
  $rep = $r.QueryTags(3.0)
  "  tags in report: " + $(if ($rep -and $rep.Tags) { $rep.Tags.Count } else { 0 })
  $seen = @{}
  foreach ($t in $rep.Tags) {
    $epc = $t.Epc.ToString().Replace(' ', '')
    $tid = ''
    try { if ($t.Tid) { $tid = $t.Tid.ToString().Replace(' ', '') } } catch { }
    $ser = ''
    try { if ($t.SerializedTid) { $ser = $t.SerializedTid } } catch { }
    $model = ''
    try { if ($t.ModelDetails) { $model = $t.ModelDetails.ToString() } } catch { }
    $key = $epc + '|' + $tid + '|' + $ser
    if ($seen.ContainsKey($key)) { $seen[$key]++; continue }
    $seen[$key] = 1
    $rssi = ''
    try { if ($t.IsPeakRssiInDbmPresent) { $rssi = $t.PeakRssiInDbm } } catch { }
    "  EPC=" + $epc + "  TID=" + $tid + "  SerializedTid=" + $ser + "  model=" + $model + "  ant=" + $t.AntennaPortNumber + "  rssi=" + $rssi
  }
  $r.Stop(); $r.Disconnect()
} catch {
  "  READ FAILED: " + $_.Exception.Message
}

"=== give the reader back to the monitor ==="
Set-Content -Path (Join-Path $hub 'control.json') -Value '{"mode":"record"}' -Encoding ASCII
Start-Sleep -Seconds 3
"DONE"