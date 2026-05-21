# MarketStream dev environment activation
.\.venv\Scripts\Activate.ps1
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
Write-Host "MarketStream env ready" -ForegroundColor Green
Write-Host "  Python: $(python --version)"
Write-Host "  Java:   $((java -version 2>&1)[0])"
