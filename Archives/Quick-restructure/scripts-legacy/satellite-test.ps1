# Satellite Network Simulation Test
# Tests tunnel performance under various satellite network conditions
# Usage: .\satellite-test.ps1 [-Profile <leo|meo|geo|all>] [-Duration <seconds>]

param(
    [ValidateSet("leo", "meo", "geo", "degraded", "all")]
    [string]$Profile = "all",

    [int]$Duration = 30,
    [int]$Requests = 20,

    [ValidateSet("quicgo", "tcp", "both")]
    [string]$Implementation = "both"
)

$ErrorActionPreference = "Continue"

# Satellite profiles
$Profiles = @{
    "terrestrial" = @{ Name = "Terrestrial (Fiber)"; Delay = "5ms"; Loss = "0.01%"; Rate = "1gbit" }
    "leo_nominal" = @{ Name = "LEO Nominal (Starlink)"; Delay = "20ms"; Loss = "0.5%"; Rate = "150mbit" }
    "leo_degraded" = @{ Name = "LEO Degraded"; Delay = "40ms"; Loss = "2%"; Rate = "100mbit" }
    "leo_handover" = @{ Name = "LEO Handover"; Delay = "100ms"; Loss = "5%"; Rate = "50mbit" }
    "meo_nominal" = @{ Name = "MEO Nominal (O3b)"; Delay = "60ms"; Loss = "0.3%"; Rate = "100mbit" }
    "meo_degraded" = @{ Name = "MEO Degraded"; Delay = "80ms"; Loss = "1%"; Rate = "75mbit" }
    "geo_nominal" = @{ Name = "GEO Nominal"; Delay = "300ms"; Loss = "0.1%"; Rate = "50mbit" }
    "geo_rain_fade" = @{ Name = "GEO Rain Fade"; Delay = "320ms"; Loss = "3%"; Rate = "20mbit" }
}

$SimulatorUrl = "http://localhost:8888"

function Apply-Profile {
    param([string]$ProfileName)
    try {
        $response = Invoke-RestMethod -Uri "$SimulatorUrl/preset/$ProfileName" -Method POST -TimeoutSec 5
        return $true
    } catch {
        Write-Host "Failed to apply profile: $_" -ForegroundColor Red
        return $false
    }
}

function Get-CurrentProfile {
    try {
        $response = Invoke-RestMethod -Uri "$SimulatorUrl/status" -TimeoutSec 5
        return $response
    } catch {
        return $null
    }
}

function Test-Latency {
    param([string]$Url, [int]$Count)

    $results = @()
    for ($i = 0; $i -lt $Count; $i++) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $null = Invoke-WebRequest -Uri $Url -TimeoutSec 30 -UseBasicParsing
            $sw.Stop()
            $results += $sw.ElapsedMilliseconds
        } catch {
            $results += -1
        }
    }
    return $results
}

function Get-Stats {
    param([array]$Data)

    $valid = $Data | Where-Object { $_ -ge 0 }
    if ($valid.Count -eq 0) {
        return @{ Min = "N/A"; Avg = "N/A"; P95 = "N/A"; Max = "N/A"; Success = 0; Total = $Data.Count }
    }

    $sorted = $valid | Sort-Object
    $count = $sorted.Count

    return @{
        Min = $sorted[0]
        Avg = [math]::Round(($sorted | Measure-Object -Average).Average, 0)
        P95 = $sorted[[math]::Floor($count * 0.95)]
        Max = $sorted[-1]
        Success = $count
        Total = $Data.Count
    }
}

# Main
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  QUICK- Satellite Simulation Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check simulator is running
$status = Get-CurrentProfile
if (-not $status) {
    Write-Host "ERROR: Satellite simulator not reachable at $SimulatorUrl" -ForegroundColor Red
    Write-Host "Start it with: docker compose -f docker-compose.monitoring.yaml up -d"
    exit 1
}

Write-Host "Satellite Simulator: OK" -ForegroundColor Green
Write-Host ""

# Determine profiles to test
$profilesToTest = switch ($Profile) {
    "leo" { @("terrestrial", "leo_nominal", "leo_degraded", "leo_handover") }
    "meo" { @("terrestrial", "meo_nominal", "meo_degraded") }
    "geo" { @("terrestrial", "geo_nominal", "geo_rain_fade") }
    "degraded" { @("terrestrial", "leo_handover", "geo_rain_fade") }
    "all" { @("terrestrial", "leo_nominal", "meo_nominal", "geo_nominal") }
}

# Determine implementations
$implementations = switch ($Implementation) {
    "quicgo" { @(@{Name="quic-go"; Port=8080}) }
    "tcp" { @(@{Name="tcp"; Port=18080}) }
    "both" { @(@{Name="quic-go"; Port=8080}, @{Name="tcp"; Port=18080}) }
}

# Results table
$results = @()

foreach ($profileName in $profilesToTest) {
    $profileInfo = $Profiles[$profileName]
    Write-Host "Testing profile: $($profileInfo.Name)" -ForegroundColor Yellow
    Write-Host "  Delay: $($profileInfo.Delay), Loss: $($profileInfo.Loss)"

    # Apply profile
    if (-not (Apply-Profile $profileName)) {
        Write-Host "Skipping profile due to error" -ForegroundColor Red
        continue
    }

    Start-Sleep -Seconds 2  # Let network conditions stabilize

    foreach ($impl in $implementations) {
        $url = "http://localhost:$($impl.Port)/"
        Write-Host "  Testing $($impl.Name)..." -NoNewline

        $latencies = Test-Latency -Url $url -Count $Requests
        $stats = Get-Stats -Data $latencies

        $results += [PSCustomObject]@{
            Profile = $profileInfo.Name
            Implementation = $impl.Name
            Delay = $profileInfo.Delay
            Loss = $profileInfo.Loss
            AvgLatency = $stats.Avg
            P95Latency = $stats.P95
            MaxLatency = $stats.Max
            SuccessRate = [math]::Round(($stats.Success / $stats.Total) * 100, 1)
        }

        Write-Host " Avg: $($stats.Avg)ms, P95: $($stats.P95)ms, Success: $($stats.Success)/$($stats.Total)" -ForegroundColor Green
    }

    Write-Host ""
}

# Reset to terrestrial
Write-Host "Resetting to terrestrial..." -ForegroundColor Yellow
Apply-Profile "terrestrial" | Out-Null

# Summary table
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Results Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$header = "{0,-25} {1,-10} {2,-10} {3,-10} {4,-10} {5,-10}" -f "Profile", "Impl", "Avg(ms)", "P95(ms)", "Max(ms)", "Success%"
Write-Host $header -ForegroundColor Yellow
Write-Host ("-" * 80)

foreach ($r in $results) {
    $row = "{0,-25} {1,-10} {2,-10} {3,-10} {4,-10} {5,-10}%" -f $r.Profile, $r.Implementation, $r.AvgLatency, $r.P95Latency, $r.MaxLatency, $r.SuccessRate
    Write-Host $row
}

# Save results
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultsPath = "test-results/satellite_$timestamp.json"
$results | ConvertTo-Json | Out-File -FilePath $resultsPath -Encoding UTF8
Write-Host ""
Write-Host "Results saved to: $resultsPath" -ForegroundColor Green
