# MarketStream — obtain MFA-authenticated temporary AWS credentials
$mfaArn = "arn:aws:iam::302542863862:mfa/marketstream-dev"
$code = Read-Host "Enter your MFA code"

$creds = aws sts get-session-token --serial-number $mfaArn --token-code $code | ConvertFrom-Json

if ($null -eq $creds) {
    Write-Host "Failed to get session token. Check your MFA code and try again." -ForegroundColor Red
    return
}

$env:AWS_ACCESS_KEY_ID     = $creds.Credentials.AccessKeyId
$env:AWS_SECRET_ACCESS_KEY = $creds.Credentials.SecretAccessKey
$env:AWS_SESSION_TOKEN     = $creds.Credentials.SessionToken

Write-Host "AWS MFA session active until $($creds.Credentials.Expiration)" -ForegroundColor Green