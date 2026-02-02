<#
.SYNOPSIS
    QUICK- Multi-Protocol Test Suite
.DESCRIPTION
    Tests all 12+ application protocols through the QUIC tunnel
.PARAMETER Mode
    Test mode: quick (basic), full (comprehensive)
#>

param(
    [ValidateSet("quick", "full")]
    [string]$Mode = "quick"
)

$ErrorActionPreference = "Continue"

# Colors
function Write-Success { param($msg) Write-Host "[PASS] $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Test { param($msg) Write-Host "`n--- $msg ---" -ForegroundColor Yellow }

$passed = 0
$failed = 0
$results = @()

Write-Host "=" * 60
Write-Host "  QUICK- Multi-Protocol Test Suite"
Write-Host "  Mode: $Mode"
Write-Host "=" * 60

# ============================================================================
# HTTP (Port 8080)
# ============================================================================
Write-Test "HTTP (Port 8080)"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/test.txt" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Success "HTTP: GET request successful ($($response.Content.Length) bytes)"
        $passed++
        $results += @{Protocol="HTTP"; Port=8080; Status="PASS"; Details="$($response.Content.Length) bytes"}
    }
} catch {
    Write-Fail "HTTP: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="HTTP"; Port=8080; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# SSH (Port 2222)
# ============================================================================
Write-Test "SSH (Port 2222)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 2222)
    if ($tcpClient.Connected) {
        $stream = $tcpClient.GetStream()
        $buffer = New-Object byte[] 256
        $stream.ReadTimeout = 3000
        $read = $stream.Read($buffer, 0, 256)
        $banner = [System.Text.Encoding]::ASCII.GetString($buffer, 0, $read)
        if ($banner -match "SSH") {
            Write-Success "SSH: Banner received - $($banner.Trim())"
            $passed++
            $results += @{Protocol="SSH"; Port=2222; Status="PASS"; Details=$banner.Trim()}
        }
    }
    $tcpClient.Close()
} catch {
    Write-Fail "SSH: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="SSH"; Port=2222; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# FTP (Port 21)
# ============================================================================
Write-Test "FTP (Port 21)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 21)
    if ($tcpClient.Connected) {
        $stream = $tcpClient.GetStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $stream.ReadTimeout = 5000
        $banner = $reader.ReadLine()
        if ($banner -match "220") {
            Write-Success "FTP: Banner received - $banner"
            $passed++
            $results += @{Protocol="FTP"; Port=21; Status="PASS"; Details=$banner}
        }
    }
    $tcpClient.Close()
} catch {
    Write-Fail "FTP: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="FTP"; Port=21; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# SMTP (Port 25)
# ============================================================================
Write-Test "SMTP (Port 25)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 25)
    if ($tcpClient.Connected) {
        $stream = $tcpClient.GetStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $stream.ReadTimeout = 5000
        $banner = $reader.ReadLine()
        if ($banner -match "220") {
            Write-Success "SMTP: Banner received - $banner"
            $passed++
            $results += @{Protocol="SMTP"; Port=25; Status="PASS"; Details=$banner}
        }
    }
    $tcpClient.Close()
} catch {
    Write-Fail "SMTP: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="SMTP"; Port=25; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# DNS (Port 53) - UDP over TCP tunnel
# ============================================================================
Write-Test "DNS (Port 53)"
try {
    # Test DNS via nslookup pointing to our DNS server
    $result = & nslookup test-http.quick.local localhost 2>&1
    if ($result -match "172.23") {
        Write-Success "DNS: Resolution successful"
        $passed++
        $results += @{Protocol="DNS"; Port=53; Status="PASS"; Details="Resolution OK"}
    } else {
        Write-Fail "DNS: Resolution failed"
        $failed++
        $results += @{Protocol="DNS"; Port=53; Status="FAIL"; Details="No resolution"}
    }
} catch {
    Write-Fail "DNS: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="DNS"; Port=53; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# MySQL (Port 3306)
# ============================================================================
Write-Test "MySQL/MariaDB (Port 3306)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 3306)
    if ($tcpClient.Connected) {
        $stream = $tcpClient.GetStream()
        $buffer = New-Object byte[] 256
        $stream.ReadTimeout = 5000
        $read = $stream.Read($buffer, 0, 256)
        # MySQL handshake starts with packet length + version string
        if ($read -gt 5) {
            Write-Success "MySQL: Handshake received ($read bytes)"
            $passed++
            $results += @{Protocol="MySQL"; Port=3306; Status="PASS"; Details="$read bytes handshake"}
        }
    }
    $tcpClient.Close()
} catch {
    Write-Fail "MySQL: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="MySQL"; Port=3306; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# PostgreSQL (Port 5433)
# ============================================================================
Write-Test "PostgreSQL (Port 5433)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 5433)
    if ($tcpClient.Connected) {
        Write-Success "PostgreSQL: Connection established"
        $passed++
        $results += @{Protocol="PostgreSQL"; Port=5433; Status="PASS"; Details="Connected"}
    }
    $tcpClient.Close()
} catch {
    Write-Fail "PostgreSQL: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="PostgreSQL"; Port=5433; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# Redis (Port 6379)
# ============================================================================
Write-Test "Redis (Port 6379)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    if ($tcpClient.Connected) {
        $stream = $tcpClient.GetStream()
        $writer = New-Object System.IO.StreamWriter($stream)
        $reader = New-Object System.IO.StreamReader($stream)
        $stream.ReadTimeout = 5000

        # Send PING command
        $writer.WriteLine("PING")
        $writer.Flush()
        $response = $reader.ReadLine()

        if ($response -match "PONG") {
            Write-Success "Redis: PING -> PONG"
            $passed++
            $results += @{Protocol="Redis"; Port=6379; Status="PASS"; Details="PONG received"}
        }
    }
    $tcpClient.Close()
} catch {
    Write-Fail "Redis: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="Redis"; Port=6379; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# MQTT (Port 1883)
# ============================================================================
Write-Test "MQTT (Port 1883)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 1883)
    if ($tcpClient.Connected) {
        Write-Success "MQTT: Broker reachable"
        $passed++
        $results += @{Protocol="MQTT"; Port=1883; Status="PASS"; Details="Broker connected"}
    }
    $tcpClient.Close()
} catch {
    Write-Fail "MQTT: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="MQTT"; Port=1883; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# WebSocket (Port 8081)
# ============================================================================
Write-Test "WebSocket (Port 8081)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 8081)
    if ($tcpClient.Connected) {
        Write-Success "WebSocket: Server reachable"
        $passed++
        $results += @{Protocol="WebSocket"; Port=8081; Status="PASS"; Details="Server connected"}
    }
    $tcpClient.Close()
} catch {
    Write-Fail "WebSocket: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="WebSocket"; Port=8081; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# SIP (Port 5060)
# ============================================================================
Write-Test "SIP/VoIP (Port 5060)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 5060)
    if ($tcpClient.Connected) {
        Write-Success "SIP: Asterisk reachable"
        $passed++
        $results += @{Protocol="SIP"; Port=5060; Status="PASS"; Details="Asterisk connected"}
    }
    $tcpClient.Close()
} catch {
    Write-Fail "SIP: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="SIP"; Port=5060; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# Echo (Port 9000)
# ============================================================================
Write-Test "Echo (Port 9000)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 9000)
    if ($tcpClient.Connected) {
        $stream = $tcpClient.GetStream()
        $writer = New-Object System.IO.StreamWriter($stream)
        $reader = New-Object System.IO.StreamReader($stream)
        $stream.ReadTimeout = 5000

        $testMsg = "QUICK-TUNNEL-ECHO-TEST"
        $writer.WriteLine($testMsg)
        $writer.Flush()
        $response = $reader.ReadLine()

        if ($response -eq $testMsg) {
            Write-Success "Echo: Message echoed correctly"
            $passed++
            $results += @{Protocol="Echo"; Port=9000; Status="PASS"; Details="Echo OK"}
        }
    }
    $tcpClient.Close()
} catch {
    Write-Fail "Echo: $($_.Exception.Message)"
    $failed++
    $results += @{Protocol="Echo"; Port=9000; Status="FAIL"; Details=$_.Exception.Message}
}

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n" + "=" * 60
Write-Host "  Protocol Test Summary"
Write-Host "=" * 60
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host "  Total:  $($passed + $failed)"
Write-Host ""

# Results table
Write-Host "Protocol Results:" -ForegroundColor Cyan
Write-Host "-" * 60
foreach ($r in $results) {
    $status = if ($r.Status -eq "PASS") { "PASS" } else { "FAIL" }
    $color = if ($r.Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host ("{0,-15} {1,-6} [{2}] {3}" -f $r.Protocol, ":$($r.Port)", $status, $r.Details) -ForegroundColor $color
}

# Save results
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportPath = "$PSScriptRoot\..\test-results\protocols_$timestamp.md"

$report = @"
# QUICK- Multi-Protocol Test Results

**Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Mode:** $Mode

## Summary

| Metric | Value |
|--------|-------|
| Passed | $passed |
| Failed | $failed |
| Total | $($passed + $failed) |

## Results by Protocol

| Protocol | Port | Status | Details |
|----------|------|--------|---------|
"@

foreach ($r in $results) {
    $report += "`n| $($r.Protocol) | $($r.Port) | $($r.Status) | $($r.Details) |"
}

$report | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "`nResults saved to: $reportPath"
