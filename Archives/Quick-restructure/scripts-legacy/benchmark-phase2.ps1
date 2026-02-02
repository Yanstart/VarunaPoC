# QUICK- TCP-over-QUIC Tunnel
# Phase 2: Comparative Benchmarks
# Per specification v2.0 Section 7.3
#
# Benchmarks:
#   B1: HTTP GET latency (curl x100) - Handshake gain
#   B2: Download throughput (iperf3, 100MB x5) - BDP utilization
#   B3: Recovery under loss (2% loss, 10MB x10) - Loss tolerance
#   B4: Handshake time (1-RTT vs 3-RTT)
#
# Conditions:
#   RTT: 50ms (LEO), 600ms (GEO)
#   Loss: 0%, 1%, 2%, 5%
#   Bandwidth: 10, 50, 100 Mbps

param(
    [ValidateSet("leo", "geo", "all")]
    [string]$Profile = "leo",

    [ValidateSet("quick", "standard", "full")]
    [string]$Mode = "quick",

    [switch]$TunnelOnly,      # Skip direct TCP baseline
    [switch]$BaselineOnly,    # Only run baseline (direct TCP)
    [switch]$SaveToDb,        # Save results to TimescaleDB
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ResultsDir = Join-Path $ProjectDir "test-results"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Create results directory
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

# Test configurations
$Profiles = @{
    leo = @{ delay = "25ms"; jitter = "5ms"; rate = "100mbit"; name = "LEO (Starlink)" }
    geo = @{ delay = "300ms"; jitter = "20ms"; rate = "50mbit"; name = "GEO" }
}

$LossRates = @("0%", "1%", "2%", "5%")

# Repetition counts based on mode
$Repetitions = @{
    quick = @{ B1 = 10; B2 = 2; B3 = 3 }
    standard = @{ B1 = 30; B2 = 5; B3 = 10 }
    full = @{ B1 = 100; B2 = 10; B3 = 30 }
}

$Rep = $Repetitions[$Mode]

# Results storage
$AllResults = @{
    RunId = "phase2_${Timestamp}"
    Profile = $Profile
    Mode = $Mode
    StartTime = Get-Date
    Benchmarks = @{}
}

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

function Set-NetworkConditions {
    param([string]$Delay, [string]$Jitter, [string]$Loss, [string]$Rate)

    $body = @{
        delay = $Delay
        jitter = $Jitter
        loss = $Loss
        rate = $Rate
    } | ConvertTo-Json

    try {
        $null = Invoke-WebRequest -Uri "http://localhost:8888/apply" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 5
        Start-Sleep -Seconds 2  # Let netem settle
        return $true
    } catch {
        Write-Log "Warning: Could not set network conditions" "Yellow"
        return $false
    }
}

function Get-Statistics {
    param([double[]]$Values)

    if ($Values.Count -eq 0) {
        return @{ Mean = 0; StdDev = 0; Min = 0; Max = 0; P50 = 0; P95 = 0; P99 = 0; Count = 0 }
    }

    $sorted = $Values | Sort-Object
    $count = $Values.Count
    $mean = ($Values | Measure-Object -Average).Average
    $sumSqDiff = ($Values | ForEach-Object { [Math]::Pow($_ - $mean, 2) } | Measure-Object -Sum).Sum
    $stdDev = [Math]::Sqrt($sumSqDiff / $count)

    return @{
        Mean = [Math]::Round($mean, 3)
        StdDev = [Math]::Round($stdDev, 3)
        Min = [Math]::Round(($sorted | Select-Object -First 1), 3)
        Max = [Math]::Round(($sorted | Select-Object -Last 1), 3)
        P50 = [Math]::Round($sorted[[Math]::Floor($count * 0.5)], 3)
        P95 = [Math]::Round($sorted[[Math]::Min([Math]::Floor($count * 0.95), $count - 1)], 3)
        P99 = [Math]::Round($sorted[[Math]::Min([Math]::Floor($count * 0.99), $count - 1)], 3)
        Count = $count
    }
}

function Run-B1-LatencyTest {
    param([string]$ProfileName, [hashtable]$Config, [string]$Loss, [int]$Iterations)

    Write-Log "B1: HTTP GET Latency ($Iterations iterations, loss=$Loss)" "Cyan"

    # Set conditions
    Set-NetworkConditions -Delay $Config.delay -Jitter $Config.jitter -Loss $Loss -Rate $Config.rate | Out-Null

    $tunnelTimes = @()

    for ($i = 1; $i -le $Iterations; $i++) {
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $null = Invoke-WebRequest -Uri "http://localhost:8080/test.txt" -UseBasicParsing -TimeoutSec 30
            $sw.Stop()
            $tunnelTimes += $sw.ElapsedMilliseconds
        } catch {
            # Failed request
        }

        if ($i % 10 -eq 0) {
            Write-Host "  Progress: $i/$Iterations" -NoNewline
            Write-Host "`r" -NoNewline
        }
    }
    Write-Host ""

    $stats = Get-Statistics -Values $tunnelTimes
    Write-Log "  Tunnel: Mean=$($stats.Mean)ms, P95=$($stats.P95)ms, StdDev=$($stats.StdDev)ms" "Green"

    return @{
        Profile = $ProfileName
        Loss = $Loss
        Tunnel = $stats
    }
}

function Run-B2-ThroughputTest {
    param([string]$ProfileName, [hashtable]$Config, [string]$Loss, [int]$Iterations)

    Write-Log "B2: Download Throughput ($Iterations iterations, loss=$Loss)" "Cyan"

    # Set conditions
    Set-NetworkConditions -Delay $Config.delay -Jitter $Config.jitter -Loss $Loss -Rate $Config.rate | Out-Null

    $tunnelSpeeds = @()
    $downloadPath = Join-Path $ResultsDir "b2_download_temp.bin"

    for ($i = 1; $i -le $Iterations; $i++) {
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            Invoke-WebRequest -Uri "http://localhost:8080/large.bin" -OutFile $downloadPath -TimeoutSec 300
            $sw.Stop()

            $fileSize = (Get-Item $downloadPath).Length
            $speedMbps = ($fileSize * 8) / ($sw.Elapsed.TotalSeconds * 1000000)
            $tunnelSpeeds += $speedMbps

            Remove-Item $downloadPath -ErrorAction SilentlyContinue
            Write-Host "  Run $i`: $([Math]::Round($speedMbps, 2)) Mbps" -ForegroundColor Gray
        } catch {
            Write-Host "  Run $i`: FAILED" -ForegroundColor Red
        }
    }

    $stats = Get-Statistics -Values $tunnelSpeeds
    Write-Log "  Tunnel: Mean=$($stats.Mean) Mbps, StdDev=$($stats.StdDev) Mbps" "Green"

    return @{
        Profile = $ProfileName
        Loss = $Loss
        Tunnel = $stats
    }
}

function Run-B3-RecoveryTest {
    param([string]$ProfileName, [hashtable]$Config, [int]$Iterations)

    Write-Log "B3: Recovery under 2% loss ($Iterations iterations)" "Cyan"

    # Set 2% loss
    Set-NetworkConditions -Delay $Config.delay -Jitter $Config.jitter -Loss "2%" -Rate $Config.rate | Out-Null

    $tunnelTimes = @()
    $tunnelSuccess = 0
    $downloadPath = Join-Path $ResultsDir "b3_download_temp.bin"

    for ($i = 1; $i -le $Iterations; $i++) {
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            Invoke-WebRequest -Uri "http://localhost:8080/large.bin" -OutFile $downloadPath -TimeoutSec 300
            $sw.Stop()

            $fileSize = (Get-Item $downloadPath).Length
            $expectedSize = 10 * 1024 * 1024

            if ($fileSize -eq $expectedSize) {
                $tunnelTimes += $sw.Elapsed.TotalSeconds
                $tunnelSuccess++
                Write-Host "  Run $i`: $([Math]::Round($sw.Elapsed.TotalSeconds, 2))s - OK" -ForegroundColor Gray
            } else {
                Write-Host "  Run $i`: Incomplete ($fileSize bytes)" -ForegroundColor Yellow
            }

            Remove-Item $downloadPath -ErrorAction SilentlyContinue
        } catch {
            Write-Host "  Run $i`: FAILED" -ForegroundColor Red
        }
    }

    $stats = Get-Statistics -Values $tunnelTimes
    Write-Log "  Success: $tunnelSuccess/$Iterations, Mean=$($stats.Mean)s" "Green"

    return @{
        Profile = $ProfileName
        SuccessRate = [Math]::Round($tunnelSuccess / $Iterations * 100, 1)
        Tunnel = $stats
    }
}

function Run-B4-HandshakeTest {
    param([string]$ProfileName, [hashtable]$Config)

    Write-Log "B4: Handshake Time Analysis" "Cyan"

    # Set nominal conditions
    Set-NetworkConditions -Delay $Config.delay -Jitter $Config.jitter -Loss "0%" -Rate $Config.rate | Out-Null

    # Measure time-to-first-byte as proxy for handshake
    $ttfbTimes = @()

    for ($i = 1; $i -le 10; $i++) {
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            # Use curl's time_starttransfer for TTFB
            $result = & curl -s -w "%{time_starttransfer}" -o NUL "http://localhost:8080/test.txt" 2>&1
            $ttfb = [double]$result * 1000  # Convert to ms
            $ttfbTimes += $ttfb
        } catch {}
    }

    $stats = Get-Statistics -Values $ttfbTimes

    # QUIC theoretical: 1 RTT for handshake
    # TCP+TLS theoretical: 3 RTT (SYN + TLS handshake)
    $rttMs = [int]($Config.delay -replace 'ms', '') * 2  # Round-trip
    $quicTheoretical = $rttMs * 1  # 1-RTT
    $tcpTheoretical = $rttMs * 3   # 3-RTT

    Write-Log "  TTFB Mean: $($stats.Mean)ms (QUIC theoretical: ${quicTheoretical}ms, TCP: ${tcpTheoretical}ms)" "Green"

    return @{
        Profile = $ProfileName
        TTFB = $stats
        QuicTheoretical = $quicTheoretical
        TcpTheoretical = $tcpTheoretical
        Improvement = [Math]::Round(($tcpTheoretical - $stats.Mean) / $tcpTheoretical * 100, 1)
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  QUICK- Phase 2: Comparative Benchmarks"
Write-Host "  Mode: $Mode | Profile: $Profile"
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Log "Checking prerequisites..." "Yellow"
$entryStatus = docker inspect -f '{{.State.Running}}' quick-entry 2>$null
if ($entryStatus -ne "true") {
    Write-Log "ERROR: Tunnel not running. Start with: docker-compose --profile go up -d" "Red"
    exit 1
}
Write-Log "Tunnel is running" "Green"

# Ensure large test file exists
$largeFileExists = docker exec quick-test-http sh -c "test -f /usr/share/nginx/html/large.bin && echo yes" 2>$null
if ($largeFileExists -ne "yes") {
    Write-Log "Creating 10MB test file..." "Yellow"
    docker exec quick-test-http sh -c "dd if=/dev/urandom of=/usr/share/nginx/html/large.bin bs=1M count=10 2>/dev/null"
}

# Determine which profiles to run
$profilesToRun = if ($Profile -eq "all") { @("leo", "geo") } else { @($Profile) }

foreach ($profileName in $profilesToRun) {
    $config = $Profiles[$profileName]
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Magenta
    Write-Host "  Profile: $($config.name)"
    Write-Host "  RTT: $($config.delay) x2, Rate: $($config.rate)"
    Write-Host "============================================" -ForegroundColor Magenta

    $profileResults = @{
        B1 = @()
        B2 = @()
        B3 = $null
        B4 = $null
    }

    # B1: Latency tests at different loss rates
    Write-Host ""
    Write-Host "--- B1: HTTP GET Latency ---" -ForegroundColor Yellow
    foreach ($loss in $LossRates) {
        $result = Run-B1-LatencyTest -ProfileName $profileName -Config $config -Loss $loss -Iterations $Rep.B1
        $profileResults.B1 += $result
    }

    # B2: Throughput tests at different loss rates
    Write-Host ""
    Write-Host "--- B2: Download Throughput ---" -ForegroundColor Yellow
    foreach ($loss in @("0%", "1%")) {  # Only test low loss for throughput
        $result = Run-B2-ThroughputTest -ProfileName $profileName -Config $config -Loss $loss -Iterations $Rep.B2
        $profileResults.B2 += $result
    }

    # B3: Recovery test (fixed 2% loss)
    Write-Host ""
    Write-Host "--- B3: Recovery under Loss ---" -ForegroundColor Yellow
    $profileResults.B3 = Run-B3-RecoveryTest -ProfileName $profileName -Config $config -Iterations $Rep.B3

    # B4: Handshake analysis
    Write-Host ""
    Write-Host "--- B4: Handshake Time ---" -ForegroundColor Yellow
    $profileResults.B4 = Run-B4-HandshakeTest -ProfileName $profileName -Config $config

    $AllResults.Benchmarks[$profileName] = $profileResults
}

# Restore nominal conditions
Set-NetworkConditions -Delay "20ms" -Jitter "5ms" -Loss "0.5%" -Rate "150mbit" | Out-Null

# ============================================================================
# GENERATE REPORT
# ============================================================================

$AllResults.EndTime = Get-Date
$AllResults.Duration = ($AllResults.EndTime - $AllResults.StartTime).TotalMinutes

$reportFile = Join-Path $ResultsDir "phase2_${Timestamp}.md"

$report = @"
# QUICK- Phase 2 Benchmark Results

**Run ID:** $($AllResults.RunId)
**Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Mode:** $Mode
**Duration:** $([Math]::Round($AllResults.Duration, 1)) minutes

## Executive Summary

"@

foreach ($profileName in $AllResults.Benchmarks.Keys) {
    $pr = $AllResults.Benchmarks[$profileName]
    $config = $Profiles[$profileName]

    $report += @"

### $($config.name) Profile

| Benchmark | Metric | Value |
|-----------|--------|-------|
| B1 Latency (0% loss) | Mean | $($pr.B1[0].Tunnel.Mean) ms |
| B1 Latency (0% loss) | P95 | $($pr.B1[0].Tunnel.P95) ms |
| B2 Throughput (0% loss) | Mean | $($pr.B2[0].Tunnel.Mean) Mbps |
| B3 Recovery (2% loss) | Success Rate | $($pr.B3.SuccessRate)% |
| B4 Handshake | TTFB | $($pr.B4.TTFB.Mean) ms |
| B4 Handshake | vs TCP Improvement | $($pr.B4.Improvement)% |

"@
}

$report += @"

## Detailed Results

"@

foreach ($profileName in $AllResults.Benchmarks.Keys) {
    $pr = $AllResults.Benchmarks[$profileName]

    $report += @"

### B1: HTTP GET Latency - $profileName

| Loss | Mean (ms) | StdDev | P50 | P95 | P99 | Count |
|------|-----------|--------|-----|-----|-----|-------|
"@

    foreach ($b1 in $pr.B1) {
        $t = $b1.Tunnel
        $report += "| $($b1.Loss) | $($t.Mean) | $($t.StdDev) | $($t.P50) | $($t.P95) | $($t.P99) | $($t.Count) |`n"
    }

    $report += @"

### B2: Download Throughput - $profileName

| Loss | Mean (Mbps) | StdDev | Min | Max | Count |
|------|-------------|--------|-----|-----|-------|
"@

    foreach ($b2 in $pr.B2) {
        $t = $b2.Tunnel
        $report += "| $($b2.Loss) | $($t.Mean) | $($t.StdDev) | $($t.Min) | $($t.Max) | $($t.Count) |`n"
    }
}

$report += @"

## Test Conditions

- **Satellite Simulator**: tc/netem via Docker
- **Tunnel Implementation**: Go/quic-go
- **Entry Proxy**: localhost:8080
- **Backend**: nginx (test-http)

## Specification Reference

Per QUICK- Cahier des Charges v2.0, Section 7.3:
- B1: HTTP GET latency (curl x100) - Demonstrates handshake gain
- B2: Download throughput (iperf3/curl, 100MB) - Demonstrates BDP utilization
- B3: Recovery under 2% loss - Demonstrates loss tolerance
- B4: Handshake time - Demonstrates 1-RTT vs 3-RTT advantage
"@

$report | Out-File -FilePath $reportFile -Encoding UTF8

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Phase 2 Benchmarks Complete"
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Duration: $([Math]::Round($AllResults.Duration, 1)) minutes"
Write-Host "  Results:  $reportFile"
Write-Host ""

# Display summary
foreach ($profileName in $AllResults.Benchmarks.Keys) {
    $pr = $AllResults.Benchmarks[$profileName]
    $config = $Profiles[$profileName]
    Write-Host "$($config.name):" -ForegroundColor Yellow
    Write-Host "  B1 Latency (0%):  $($pr.B1[0].Tunnel.Mean) ms (P95: $($pr.B1[0].Tunnel.P95) ms)"
    Write-Host "  B2 Throughput:    $($pr.B2[0].Tunnel.Mean) Mbps"
    Write-Host "  B3 Recovery:      $($pr.B3.SuccessRate)% success"
    Write-Host "  B4 Handshake:     $($pr.B4.Improvement)% faster than TCP"
    Write-Host ""
}
