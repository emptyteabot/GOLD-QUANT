# 保持系统唤醒但允许息屏
# 运行后会持续阻止系统睡眠，按 Ctrl+C 退出
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class SleepUtil {
  [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);
  public const uint ES_CONTINUOUS = 0x80000000;
  public const uint ES_SYSTEM_REQUIRED = 0x00000001;
}
"@

# 设置为持续 + 系统需要（不阻止屏幕关闭）
[SleepUtil]::SetThreadExecutionState([SleepUtil]::ES_CONTINUOUS -bor [SleepUtil]::ES_SYSTEM_REQUIRED) | Out-Null
Write-Host "Awake guard started. Press Ctrl+C to stop." -ForegroundColor Green

try {
  while ($true) { Start-Sleep -Seconds 60 }
} finally {
  # 退出时恢复默认
  [SleepUtil]::SetThreadExecutionState([SleepUtil]::ES_CONTINUOUS) | Out-Null
}
