<#
  rfid-health.ps1 - is this station actually reading RFID right now?

  Read-only by default. It answers, in order:
    1. which reader the app is configured to use (from SettingPrm.xml)
    2. is that reader reachable (LLRP 5084 / http 80)
    3. who owns the LLRP session (Impinj allows exactly one client)
    4. is the app's own write path alive (EpcLog freshness)
    5. is the app logging RFID errors (Main_<date>.log)
  then prints a single verdict line.

  -Inventory additionally performs a real tag inventory through the Impinj
  Octane SDK (D:\Ben Read RFID\Impinj.OctaneSdk.dll). It REFUSES to run while
  another client holds the session, because stealing LLRP would stop production.

  Exit codes: 0 RFID_OK | 1 NO_TAGS | 2 READER_BUSY | 3 APP_NOT_CONNECTED
              4 READER_UNREACHABLE | 5 CONFIG_MISSING | 6 INVENTORY_BLOCKED
#>
param(
  [string]$AppRoot = 'D:\HQ Package System V2',
  [int]$WindowMinutes = 15,
  [switch]$Inventory,
  [int]$InventorySeconds = 5,
  [string]$SdkDir = 'D:\Ben Read RFID'
)

$ErrorActionPreference = 'Continue'
$now = Get-Date
$today = $now.ToString('yyyyMMdd')

function Say([string]$m) { Write-Output $m }

function Tail-Text {
  param([string]$Path, [int]$Lines = 25)
  try {
    $fs = [System.IO.File]::Open($Path, 'Open', 'Read', 'ReadWrite')
    $len = $fs.Length
    $take = [Math]::Min($len, 128KB)
    $fs.Position = $len - $take
    $buf = New-Object byte[] $take
    [void]$fs.Read($buf, 0, $take)
    $fs.Close()
    $txt = [System.Text.Encoding]::UTF8.GetString($buf)
    if ($txt.IndexOf([char]0xFFFD) -ge 0) { $txt = [System.Text.Encoding]::GetEncoding(936).GetString($buf) }
    $all = $txt -split "`r?`n"
    if ($all.Count -le $Lines) { return $all }
    return $all[($all.Count - $Lines)..($all.Count - 1)]
  } catch { return @() }
}

# ---------------------------------------------------------------- 1. config
$cfgPath = Join-Path $AppRoot 'Setting\SettingPrm.xml'
if (-not (Test-Path $cfgPath)) { Say ('CONFIG_MISSING ' + $cfgPath); exit 5 }
# the app writes this file padded to 2048 bytes with NULs, which breaks [xml];
# pull the three numbers we need textually instead.
$raw = [System.IO.File]::ReadAllText($cfgPath) -replace "`0", ''
$rfidIp = ''
$txPower = ''
$rxPower = ''
$mRfid = [regex]::Match($raw, '<rfidSetting>\s*<Ip>([^<]+)</Ip>\s*<TxPower>([^<]*)</TxPower>\s*<RxPower>([^<]*)</RxPower>', 'Singleline')
if ($mRfid.Success) {
  $rfidIp = $mRfid.Groups[1].Value.Trim()
  $txPower = $mRfid.Groups[2].Value.Trim()
  $rxPower = $mRfid.Groups[3].Value.Trim()
}
Say ('reader_ip=' + $rfidIp + ' tx=' + $txPower + ' rx=' + $rxPower)
if (-not $rfidIp) { Say 'CONFIG_MISSING rfidSetting.Ip'; exit 5 }

# ---------------------------------------------------------------- 2. reachability
function Test-Port([string]$host_, [int]$port, [int]$timeoutMs = 2000) {
  $c = New-Object Net.Sockets.TcpClient
  try {
    $iar = $c.BeginConnect($host_, $port, $null, $null)
    if (-not $iar.AsyncWaitHandle.WaitOne($timeoutMs)) { return 'timeout' }
    $c.EndConnect($iar)
    return 'open'
  } catch { return 'closed' } finally { $c.Close() }
}
$llrp = Test-Port $rfidIp 5084
$http = Test-Port $rfidIp 80
Say ('llrp_5084=' + $llrp + ' http_80=' + $http)
if ($llrp -ne 'open') { Say ('VERDICT READER_UNREACHABLE (' + $rfidIp + ':' + $llrp + ')'); exit 4 }

# ---------------------------------------------------------------- 3. session owner
$ownerPid = 0
$ownerName = '-'
try {
  $conns = @(Get-NetTCPConnection -RemoteAddress $rfidIp -RemotePort 5084 -ErrorAction SilentlyContinue |
             Where-Object { $_.State -eq 'Established' })
  if ($conns.Count -gt 0) {
    $ownerPid = [int]$conns[0].OwningProcess
    $p = Get-Process -Id $ownerPid -ErrorAction SilentlyContinue
    if ($p) { $ownerName = $p.ProcessName }
    Say ('llrp_client=' + $ownerName + ' (pid ' + $ownerPid + ') local=' + $conns[0].LocalAddress + ':' + $conns[0].LocalPort)
  } else {
    Say 'llrp_client=(none)'
  }
} catch { Say ('llrp_client=unknown (' + $_.Exception.Message + ')') }

# ---------------------------------------------------------------- 4. EpcLog freshness
$epcDir = Join-Path $AppRoot ('EpcLog\' + $today)
$epcFile = Join-Path $epcDir ($today + '.log')
$epcAge = -1
$epcRecent = 0
$epcLast = ''
if (Test-Path $epcFile) {
  $epcAge = [int]($now - (Get-Item $epcFile).LastWriteTime).TotalMinutes
  $lines = Tail-Text $epcFile 400
  foreach ($l in $lines) {
    if ($l -match '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})') {
      $ts = [datetime]$matches[1]
      if (($now - $ts).TotalMinutes -le $WindowMinutes) { $epcRecent++ }
      $epcLast = $matches[1]
    }
  }
  Say ('epclog=' + $epcFile + ' age_min=' + $epcAge + ' entries_last_' + $WindowMinutes + 'min=' + $epcRecent + ' last=' + $epcLast)
} else {
  Say ('epclog=MISSING ' + $epcFile)
}

# ---------------------------------------------------------------- 5. app errors
$mainLog = Join-Path $AppRoot ('Logs\' + $today + '\Main_' + $today + '.log')
$errCount = 0
$stopCount = 0
$flowCount = 0
$lastErr = ''
if (Test-Path $mainLog) {
  $tailLines = Tail-Text $mainLog 4000
  foreach ($l in $tailLines) {
    if ($l -match '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})') {
      $ts = [datetime]$matches[1]
      if (($now - $ts).TotalMinutes -gt $WindowMinutes) { continue }
      if ($l -match 'Rfid event error') { $errCount++; $lastErr = $l.Trim() }
      if ($l -match 'RFID 读写器停止') { $stopCount++ }
      if ($l -match 'RfidFlow start') { $flowCount++ }
    }
  }
  Say ('main_log: rfid_flow_start=' + $flowCount + ' rfid_errors=' + $errCount + ' reader_stop=' + $stopCount + ' (last ' + $WindowMinutes + 'min)')
  if ($lastErr) { Say ('last_error=' + $lastErr.Substring(0, [Math]::Min(200, $lastErr.Length))) }
} else {
  Say ('main_log=MISSING ' + $mainLog)
}

# ---------------------------------------------------------------- optional inventory
if ($Inventory) {
  $sdk = Join-Path $SdkDir 'Impinj.OctaneSdk.dll'
  if (-not (Test-Path $sdk)) { Say ('INVENTORY_BLOCKED sdk missing: ' + $sdk); exit 6 }
  $busyByOther = ($ownerPid -gt 0) -and ($ownerName -notmatch 'rfid-health')
  if ($busyByOther) {
    Say ('INVENTORY_BLOCKED reader session held by ' + $ownerName + ' (pid ' + $ownerPid + ') - refusing to steal it')
    exit 6
  }
  try {
    Add-Type -Path $sdk
    $reader = [Impinj.OctaneSdk.Reader]::Create($rfidIp)
    $reader.Connect()
    $settings = $reader.QueryDefaultSettings()
    $settings.Report.IncludeAntennaPortNumber = $true
    $settings.Report.IncludePeakRssi = $true
    $settings.Report.IncludeSeenCount = $true
    $settings.Report.IncludeFirstSeenTime = $true
    $settings.Session = 2
    $settings.SearchMode = [Impinj.OctaneSdk.SearchMode]::DualTarget
    $settings.Report.Mode = [Impinj.OctaneSdk.ReportingMode]::IndividualReads
    $reader.ApplySettings($settings)
    $seen = @{}
    $handler = { param($s, $e) foreach ($t in $e.TagReport.Tags) { $script:seen[$t.Epc.ToString()] = $t.AntennaPortNumber } }
    $sub = Register-ObjectEvent -InputObject $reader -EventName TagsReported -Action $handler
    $reader.Start()
    Start-Sleep -Seconds $InventorySeconds
    $reader.Stop()
    Unregister-Event -SourceIdentifier $sub.Name -ErrorAction SilentlyContinue
    $reader.Disconnect()
    Say ('inventory_seconds=' + $InventorySeconds + ' distinct_epcs=' + $script:seen.Count)
    foreach ($k in $script:seen.Keys) { Say ('  EPC ' + $k + '  antenna ' + $script:seen[$k]) }
  } catch {
    Say ('INVENTORY_FAILED ' + $_.Exception.Message)
  }
}

# ---------------------------------------------------------------- verdict
$verdict = 'RFID_OK'
$why = ''
if ($llrp -ne 'open') { $verdict = 'READER_UNREACHABLE'; $why = 'llrp port not open' }
elseif ($errCount -gt 0 -and $ownerPid -gt 0 -and $ownerName -notmatch 'HQ Package') {
  $verdict = 'READER_BUSY'
  $why = 'app is failing to connect while ' + $ownerName + ' (pid ' + $ownerPid + ') holds the LLRP session'
}
elseif ($errCount -gt 0) { $verdict = 'APP_NOT_CONNECTED'; $why = 'app logs connect errors' }
elseif ($epcRecent -eq 0) { $verdict = 'NO_TAGS'; $why = 'no EpcLog entries in the last ' + $WindowMinutes + ' min' }
Say ('VERDICT ' + $verdict + ' - ' + $why)
switch ($verdict) {
  'RFID_OK' { exit 0 }
  'NO_TAGS' { exit 1 }
  'READER_BUSY' { exit 2 }
  'APP_NOT_CONNECTED' { exit 3 }
  'READER_UNREACHABLE' { exit 4 }
  default { exit 0 }
}