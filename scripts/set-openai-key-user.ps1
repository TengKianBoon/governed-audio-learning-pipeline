Write-Host "This stores OPENAI_API_KEY for your Windows user account." -ForegroundColor Yellow
Write-Host "Use a dedicated OpenAI project key with spend limits. Do not use this on a shared computer." -ForegroundColor Yellow

$secureKey = Read-Host "Paste OpenAI API key" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($secureKey)

try {
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringUni($ptr)
    [Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $plainKey, "User")
    $env:OPENAI_API_KEY = $plainKey
    Write-Host "OPENAI_API_KEY is set for this PowerShell window and future PowerShell windows." -ForegroundColor Green
}
finally {
    if ($ptr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeCoTaskMemUnicode($ptr)
    }
    Remove-Variable secureKey, ptr, plainKey -ErrorAction SilentlyContinue
}
