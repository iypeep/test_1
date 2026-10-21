$ErrorActionPreference = 'Continue'
$app = 'D:\HQ Package System V2'
$today = Get-Date -Format 'yyyyMMdd'
$main = Join-Path $app ('Logs\' + $today + '\Main_' + $today + '.log')
$epc  = Join-Path $app ('EpcLog\' + $today + '\' + $today + '.log')

"=== 1. MODELS seen today (Main log) ==="
$lines = [System.IO.File]::ReadAllLines($main, [System.Text.Encoding]::UTF8)
$models = @{}
$sscc = @{}
$settings = @{}
$qtyFields = @{}
foreach ($l in $lines) {
  $m = [regex]::Match($l, '"MODEL"\s*:\s*"([^"]+)"')
  if ($m.Success) { $k = $m.Groups[1].Value; if (-not $models.ContainsKey($k)) { $models[$k] = 0 }; $models[$k]++ }
  $m2 = [regex]::Match($l, '"SSCC"\s*:\s*"([^"]+)"')
  if ($m2.Success) { $sscc[$m2.Groups[1].Value] = 1 }
  $m3 = [regex]::Match($l, '"SETTINGNAME"\s*:\s*"([^"]+)"')
  if ($m3.Success) { $k = $m3.Groups[1].Value; if (-not $settings.ContainsKey($k)) { $settings[$k] = 0 }; $settings[$k]++ }
  foreach ($f in @('BoxQty','QTY','Qty','Amount','PCS','Pcs','Num','Count')) {
    $m4 = [regex]::Match($l, '"' + $f + '"\s*:\s*"?([0-9]+)"?')
    if ($m4.Success) { $k = $f + '=' + $m4.Groups[1].Value; if (-not $qtyFields.ContainsKey($k)) { $qtyFields[$k] = 0 }; $qtyFields[$k]++ }
  }
}
foreach ($k in ($models.GetEnumerator() | Sort-Object Value -Descending)) { "  MODEL " + $k.Key + " : " + $k.Value + " record(s)" }
foreach ($k in ($settings.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 8)) { "  SETTINGNAME " + $k.Key + " : " + $k.Value }
"  distinct SSCC today: " + $sscc.Count
"--- quantity-ish fields seen ---"
foreach ($k in ($qtyFields.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10)) { "  " + $k.Key + "  x" + $k.Value }

"=== 2. one full record (40 lines around the last MODEL line) ==="
$idx = -1
for ($i = $lines.Count - 1; $i -ge 0; $i--) { if ($lines[$i] -match '"MODEL"') { $idx = $i; break } }
if ($idx -ge 0) {
  $from = [Math]::Max(0, $idx - 32); $to = [Math]::Min($lines.Count - 1, $idx + 8)
  for ($i = $from; $i -le $to; $i++) { $t = $lines[$i]; if ($t.Length -gt 170) { $t = $t.Substring(0,170) }; "    " + $i + ": " + $t }
}

"=== 3. EpcLog value classes ==="
$epcVals = @{}
$cls = @{ EPC = 0; DSN = 0; DEVICE = 0; OTHER = 0 }
$epcDistinct = @{}
$fs = [System.IO.File]::Open($epc, 'Open', 'Read', 'ReadWrite')
$sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8, $true)
while (-not $sr.EndOfStream) {
  $l = $sr.ReadLine(); if (-not $l) { continue }
  $m = [regex]::Match($l, '^(\S+ \S+)\s+InPut:(\S*)$')
  if (-not $m.Success) { continue }
  $v = $m.Groups[2].Value
  if ($v -match '^[0-9A-Fa-f]{20,}$') {
    $cls.EPC++
    if (-not $epcDistinct.ContainsKey($v)) { $epcDistinct[$v] = 0 }
    $epcDistinct[$v]++
  } elseif ($v -match '^GN[0-9A-Z]{10,}$') { $cls.DSN++ }
  elseif ($v -match '^[0-9A-Fa-f]+$' -and $v.Length -le 20) { $cls.DEVICE++ }
  else { $cls.OTHER++ }
}
$sr.Close(); $fs.Close()
"  lines by class: " + ($cls.GetEnumerator() | ForEach-Object { $_.Key + '=' + $_.Value }) -join '  '
"  distinct raw EPC values: " + $epcDistinct.Count
"--- reads per EPC (top 10) ---"
$epcDistinct.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10 | ForEach-Object { "  {0,6} x {1}" -f $_.Value, $_.Key }

"=== 4. cartons vs EPC reads (same day) ==="
$cartons = $sscc.Count
"  cartons (distinct SSCC): " + $cartons
if ($cartons -gt 0) {
  $allIn = ($cls.EPC + $cls.DSN + $cls.DEVICE + $cls.OTHER)
  "  EPC-class lines per carton : " + [math]::Round($cls.EPC / $cartons, 2)
  "  all InPut lines per carton : " + [math]::Round($allIn / $cartons, 2)
  "  device/serial lines per carton : " + [math]::Round(($cls.DEVICE + $cls.DSN) / $cartons, 2)
}
"DONE"