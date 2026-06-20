[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $null, "User")
Remove-Item Env:\OPENAI_API_KEY -ErrorAction SilentlyContinue
Write-Host "OPENAI_API_KEY removed from this PowerShell window and future PowerShell windows." -ForegroundColor Green
