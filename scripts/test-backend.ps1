param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

function Write-Pass([string]$Message) {
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Write-Fail([string]$Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Get-EnvValueFromFile([string]$FilePath, [string]$Key) {
    if (-not (Test-Path $FilePath)) {
        return $null
    }
    $line = Get-Content -Path $FilePath | Where-Object { $_ -match "^$Key=" } | Select-Object -First 1
    if (-not $line) {
        return $null
    }
    return ($line -replace "^$Key=", "").Trim()
}

function New-TelegramInitData([string]$BotToken, [int64]$UserId, [string]$FirstName, [string]$Username) {
    Add-Type -AssemblyName System.Web

    $userObj = @{
        id         = $UserId
        first_name = $FirstName
        username   = $Username
    }
    $userJson = ($userObj | ConvertTo-Json -Compress)
    $authDate = [int64][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()

    $checkDataString = "auth_date=$authDate`nuser=$userJson"

    $hmacSecret = New-Object System.Security.Cryptography.HMACSHA256
    $hmacSecret.Key = [Text.Encoding]::UTF8.GetBytes("WebAppData")
    $secretKey = $hmacSecret.ComputeHash([Text.Encoding]::UTF8.GetBytes($BotToken))

    $hmacHash = New-Object System.Security.Cryptography.HMACSHA256
    $hmacHash.Key = $secretKey
    $hashBytes = $hmacHash.ComputeHash([Text.Encoding]::UTF8.GetBytes($checkDataString))
    $hash = -join ($hashBytes | ForEach-Object { $_.ToString("x2") })

    $encodedUser = [System.Web.HttpUtility]::UrlEncode($userJson)
    return "user=$encodedUser&auth_date=$authDate&hash=$hash"
}

function Invoke-Api {
    param(
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [object]$Body = $null,
        [string]$ContentType = $null
    )

    $params = @{
        Method  = $Method
        Uri     = $Url
        Headers = $Headers
    }
    if ($null -ne $Body) {
        $params.Body = $Body
    }
    if ($ContentType) {
        $params.ContentType = $ContentType
    }

    try {
        $resp = Invoke-WebRequest @params
        $json = $null
        if ($resp.Content) {
            try { $json = $resp.Content | ConvertFrom-Json } catch {}
        }
        return [pscustomobject]@{
            StatusCode = [int]$resp.StatusCode
            Json       = $json
            Raw        = $resp.Content
        }
    }
    catch {
        $statusCode = -1
        $raw = ""

        if ($_.Exception.Response) {
            try { $statusCode = [int]$_.Exception.Response.StatusCode } catch {}
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $raw = $reader.ReadToEnd()
                $reader.Close()
            } catch {}
        }
        $json = $null
        if ($raw) {
            try { $json = $raw | ConvertFrom-Json } catch {}
        }
        return [pscustomobject]@{
            StatusCode = $statusCode
            Json       = $json
            Raw        = $raw
        }
    }
}

$script:Passed = 0
$script:Failed = 0

function Assert-Step {
    param(
        [string]$Name,
        [scriptblock]$Check
    )
    try {
        & $Check
        $script:Passed++
        Write-Pass $Name
    }
    catch {
        $script:Failed++
        Write-Fail "$Name :: $($_.Exception.Message)"
    }
}

Write-Host "Running backend smoke test against $BaseUrl`n"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendEnv = Join-Path $repoRoot "backend\.env"
$botToken = Get-EnvValueFromFile -FilePath $backendEnv -Key "BOT_TOKEN"
if (-not $botToken) {
    throw "BOT_TOKEN not found in backend/.env"
}

$health = Invoke-Api -Method "GET" -Url "$BaseUrl/health/db"
if ($health.StatusCode -ne 200) {
    throw "Backend is not ready. /health/db returned $($health.StatusCode). Start uvicorn and postgres first."
}

$seed = [int64][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$tgA = 910000000 + $seed
$tgB = 920000000 + $seed
$tgC = 930000000 + $seed

$initA = New-TelegramInitData -BotToken $botToken -UserId $tgA -FirstName "MentorA" -Username "mentor_a_$seed"
$initB = New-TelegramInitData -BotToken $botToken -UserId $tgB -FirstName "MenteeB" -Username "mentee_b_$seed"
$initC = New-TelegramInitData -BotToken $botToken -UserId $tgC -FirstName "MenteeC" -Username "mentee_c_$seed"

$headersA = @{ "X-Telegram-Init-Data" = $initA }
$headersB = @{ "X-Telegram-Init-Data" = $initB }
$headersC = @{ "X-Telegram-Init-Data" = $initC }

$authA = Invoke-Api -Method "GET" -Url "$BaseUrl/api/auth/me" -Headers $headersA
$authB = Invoke-Api -Method "GET" -Url "$BaseUrl/api/auth/me" -Headers $headersB
$authC = Invoke-Api -Method "GET" -Url "$BaseUrl/api/auth/me" -Headers $headersC

Assert-Step "Auth A created/loaded" {
    if ($authA.StatusCode -ne 200) { throw "status=$($authA.StatusCode)" }
}
Assert-Step "Auth B created/loaded" {
    if ($authB.StatusCode -ne 200) { throw "status=$($authB.StatusCode)" }
}
Assert-Step "Auth C created/loaded" {
    if ($authC.StatusCode -ne 200) { throw "status=$($authC.StatusCode)" }
}

$createA = Invoke-Api -Method "POST" -Url "$BaseUrl/api/users" -Headers $headersA -Body @{
    first_name  = "MentorA"
    age         = "28"
    description = "Mentor profile for backend test"
    role        = "mentor"
    direction   = "Frontend"
}
$createB = Invoke-Api -Method "POST" -Url "$BaseUrl/api/users" -Headers $headersB -Body @{
    first_name  = "MenteeB"
    age         = "22"
    description = "Mentee profile for backend test"
    role        = "mentee"
    direction   = "Frontend"
}
$createC = Invoke-Api -Method "POST" -Url "$BaseUrl/api/users" -Headers $headersC -Body @{
    first_name  = "MenteeC"
    age         = "23"
    description = "Second mentee profile for backend test"
    role        = "mentee"
    direction   = "Data Science"
}

Assert-Step "Create profile A (mentor)" {
    if ($createA.StatusCode -ne 201) { throw "status=$($createA.StatusCode) raw=$($createA.Raw)" }
}
Assert-Step "Create profile B (mentee Frontend)" {
    if ($createB.StatusCode -ne 201) { throw "status=$($createB.StatusCode) raw=$($createB.Raw)" }
}
Assert-Step "Create profile C (mentee Data Science)" {
    if ($createC.StatusCode -ne 201) { throw "status=$($createC.StatusCode) raw=$($createC.Raw)" }
}

$idA = [int64]$createA.Json.id
$idB = [int64]$createB.Json.id
$idC = [int64]$createC.Json.id

$candA = Invoke-Api -Method "GET" -Url "$BaseUrl/api/candidates?limit=50" -Headers $headersA
$candB = Invoke-Api -Method "GET" -Url "$BaseUrl/api/candidates?limit=50" -Headers $headersB
$candAFrontend = Invoke-Api -Method "GET" -Url "$BaseUrl/api/candidates?direction=Frontend&limit=50" -Headers $headersA
$dsDirection = [uri]::EscapeDataString("Data Science")
$candADataScience = Invoke-Api -Method "GET" -Url "$BaseUrl/api/candidates?direction=$dsDirection&limit=50" -Headers $headersA

Assert-Step "Candidates for mentor A include both mentees" {
    if ($candA.StatusCode -ne 200) { throw "status=$($candA.StatusCode)" }
    $ids = @($candA.Json | ForEach-Object { [int64]$_.id })
    if (-not ($ids -contains $idB)) { throw "idB not found" }
    if (-not ($ids -contains $idC)) { throw "idC not found" }
}
Assert-Step "Candidates for mentee B include mentor A" {
    if ($candB.StatusCode -ne 200) { throw "status=$($candB.StatusCode)" }
    $ids = @($candB.Json | ForEach-Object { [int64]$_.id })
    if (-not ($ids -contains $idA)) { throw "idA not found" }
}
Assert-Step "Direction filter Frontend returns B only for A" {
    if ($candAFrontend.StatusCode -ne 200) { throw "status=$($candAFrontend.StatusCode)" }
    $ids = @($candAFrontend.Json | ForEach-Object { [int64]$_.id })
    if (-not ($ids -contains $idB)) { throw "idB missing" }
    if ($ids -contains $idC) { throw "idC should not appear" }
}
Assert-Step "Direction filter Data Science returns C only for A" {
    if ($candADataScience.StatusCode -ne 200) { throw "status=$($candADataScience.StatusCode)" }
    $ids = @($candADataScience.Json | ForEach-Object { [int64]$_.id })
    if (-not ($ids -contains $idC)) { throw "idC missing" }
    if ($ids -contains $idB) { throw "idB should not appear" }
}

$selfLikeA = Invoke-Api -Method "POST" -Url "$BaseUrl/api/likes" -Headers $headersA -Body (@{ liked_user_id = $idA } | ConvertTo-Json) -ContentType "application/json"
Assert-Step "Self-like blocked (400)" {
    if ($selfLikeA.StatusCode -ne 400) { throw "status=$($selfLikeA.StatusCode)" }
}

$likeAtoB = Invoke-Api -Method "POST" -Url "$BaseUrl/api/likes" -Headers $headersA -Body (@{ liked_user_id = $idB } | ConvertTo-Json) -ContentType "application/json"
Assert-Step "Like A->B saved without match" {
    if ($likeAtoB.StatusCode -ne 200) { throw "status=$($likeAtoB.StatusCode)" }
    if ($likeAtoB.Json.is_match -ne $false) { throw "is_match expected false" }
}

$repeatLikeAtoB = Invoke-Api -Method "POST" -Url "$BaseUrl/api/likes" -Headers $headersA -Body (@{ liked_user_id = $idB } | ConvertTo-Json) -ContentType "application/json"
Assert-Step "Repeat like returns 409" {
    if ($repeatLikeAtoB.StatusCode -ne 409) { throw "status=$($repeatLikeAtoB.StatusCode)" }
}

$candAAfterLike = Invoke-Api -Method "GET" -Url "$BaseUrl/api/candidates?limit=50" -Headers $headersA
Assert-Step "Liked user B no longer in A candidates" {
    if ($candAAfterLike.StatusCode -ne 200) { throw "status=$($candAAfterLike.StatusCode)" }
    $ids = @($candAAfterLike.Json | ForEach-Object { [int64]$_.id })
    if ($ids -contains $idB) { throw "idB should be excluded after like" }
}

$likeBtoA = Invoke-Api -Method "POST" -Url "$BaseUrl/api/likes" -Headers $headersB -Body (@{ liked_user_id = $idA } | ConvertTo-Json) -ContentType "application/json"
Assert-Step "Like B->A creates match" {
    if (@(200, 201) -notcontains $likeBtoA.StatusCode) { throw "status=$($likeBtoA.StatusCode)" }
    if ($likeBtoA.Json.is_match -ne $true) { throw "is_match expected true" }
    if (-not $likeBtoA.Json.match_id) { throw "match_id is empty" }
}

$dislikeBtoA = Invoke-Api -Method "POST" -Url "$BaseUrl/api/dislikes" -Headers $headersB -Body (@{ disliked_user_id = $idA } | ConvertTo-Json) -ContentType "application/json"
Assert-Step "Dislike B->A saved (like replaced)" {
    if ($dislikeBtoA.StatusCode -ne 200) { throw "status=$($dislikeBtoA.StatusCode)" }
    if ($dislikeBtoA.Json.success -ne $true) { throw "success expected true" }
}

$repeatDislikeBtoA = Invoke-Api -Method "POST" -Url "$BaseUrl/api/dislikes" -Headers $headersB -Body (@{ disliked_user_id = $idA } | ConvertTo-Json) -ContentType "application/json"
Assert-Step "Repeat dislike returns 409" {
    if ($repeatDislikeBtoA.StatusCode -ne 409) { throw "status=$($repeatDislikeBtoA.StatusCode)" }
}

Write-Host ""
Write-Host "==============================" -ForegroundColor DarkGray
Write-Host "Backend test summary: PASS=$script:Passed FAIL=$script:Failed"
Write-Host "==============================" -ForegroundColor DarkGray

if ($script:Failed -gt 0) {
    exit 1
}
exit 0
