# 24h run loop for AURUM (signal-only)
# Press Ctrl+C to stop
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class SleepUtil {
  [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);
  public const uint ES_CONTINUOUS = 0x80000000;
  public const uint ES_SYSTEM_REQUIRED = 0x00000001;
}
"@

# prevent sleep (screen can still turn off)
[SleepUtil]::SetThreadExecutionState([SleepUtil]::ES_CONTINUOUS -bor [SleepUtil]::ES_SYSTEM_REQUIRED) | Out-Null

$base = "C:\Users\陈盈桦\Desktop\黄金"
$python = $env:PYTHON_EXE
if ([string]::IsNullOrWhiteSpace($python)) { $python = "C:\Users\陈盈桦\AppData\Local\Programs\Python\Python313\python.exe" }
$main = Join-Path $base "main.py"
$log = Join-Path $base "_tmp\run_24h.log"

if (-not $env:HTTP_PROXY) { $env:HTTP_PROXY = "http://127.0.0.1:10808" }
if (-not $env:HTTPS_PROXY) { $env:HTTPS_PROXY = "http://127.0.0.1:10808" }

Write-Host "AURUM 24h runner started. Logs -> $log" -ForegroundColor Green

try {
  while ($true) {
    "`n[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] START main.py" | Out-File -FilePath $log -Append -Encoding UTF8
    & $python $main 2>&1 | Tee-Object -FilePath $log -Append
    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] EXIT main.py" | Out-File -FilePath $log -Append -Encoding UTF8
    Start-Sleep -Seconds 5
  }
} finally {
  [SleepUtil]::SetThreadExecutionState([SleepUtil]::ES_CONTINUOUS) | Out-Null
}
