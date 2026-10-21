$ErrorActionPreference = 'Continue'
$hub = '\\10.32.134.128\mbd3md3_basin\TBZ\_omp\machines\7H3AA-PALLET\rfid'
Set-Content -Path (Join-Path $hub 'control.json') -Value '{"mode":"pause"}' -Encoding ASCII
Start-Sleep -Seconds 5

Add-Type -Path 'D:\Ben Read RFID\Impinj.OctaneSdk.dll' 2>$null
Add-Type -Path 'D:\Ben Read RFID\LLRP.dll' 2>$null

$ip = '192.168.1.100'
try {
  $r = New-Object Impinj.OctaneSdk.ImpinjReader
  $r.Connect($ip)
  $st = $r.QueryDefaultSettings()
  $st.Report.IncludeAntennaPortNumber = $true
  $st.Report.IncludePeakRssi = $true
  $st.Report.IncludeSeenCount = $true
  $st.Report.IncludeSerializedTid = $true
  $st.Report.IncludeFastId = $true
  $st.Report.IncludePcBits = $true
  $st.Report.IncludeCrc = $true
  $r.ApplySettings($st)
  $rep = $r.QueryTags(3.0)
  "tags: " + $rep.Tags.Count
  $shown = @{}
  foreach ($t in $rep.Tags) {
    $epc = $t.Epc.ToString().Replace(' ', '')
    if ($shown.ContainsKey($epc)) { continue }
    $shown[$epc] = 1
    $ser = ''
    try { $ser = [string]$t.SerializedTid } catch { }
    $tid = ''
    try { if ($t.Tid) { $tid = $t.Tid.ToString().Replace(' ', '') } } catch { }
    $md = $t.ModelDetails
    $modelName = ''
    $epcBits = ''
    $userBits = ''
    try { if ($md) { $modelName = [string]$md.ModelName; $epcBits = [string]$md.EpcSizeBits; $userBits = [string]$md.UserMemorySizeBits } } catch { }
    $pc = ''
    try { if ($t.IsPcBitsPresent) { $pc = $t.PcBits } } catch { }
    ""
    "  EPC            = " + $epc
    "  EPC length     = " + ($epc.Length / 2) + " bytes / " + $epc.Length + " hex"
    "  SerializedTid  = " + $ser
    "  Tid            = " + $tid
    "  chip model     = " + $modelName + "   (epc bits=" + $epcBits + ", user bits=" + $userBits + ")"
    "  PC bits        = " + $pc
    "  antenna/rssi   = " + $t.AntennaPortNumber + " / " + $t.PeakRssiInDbm
  }
  $r.Stop(); $r.Disconnect()
} catch { "READ FAILED: " + $_.Exception.Message }

Set-Content -Path (Join-Path $hub 'control.json') -Value '{"mode":"record"}' -Encoding ASCII
Start-Sleep -Seconds 3
"DONE"