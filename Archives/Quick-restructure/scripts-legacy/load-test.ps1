# Load Test Script for QUICK- Tunnel
# Generates sustained load to measure throughput and latency
# Usage: .\load-test.ps1 [-Concurrency <n>] [-Requests <n>] [-Implementation <impl>]

param(
    [int]$Concurrency = 10,
    [int]$Requests = 100,

    [ValidateSet("quicgo", "quiche", "tcp")]
    [string]$Implementation = "quicgo",

    [ValidateSet("http", "tcp", "mixed")]
    [string]$Type = "http",

    [switch]$Compare
)

$ErrorActionPreference = "Continue"

# Port mappings
$Ports = @{
    "quicgo" = @{ HTTP = 8080; SSH = 2222 }
    "quiche" = @{ HTTP = 8180; SSH = 2322 }
    "tcp"    = @{ HTTP = 18080; SSH = 12222 }
}

function Measure-HTTPLatency {
    param([string]$Url, [int]$Count)

    $results = @()
    for ($i = 0; $i -lt $Count; $i++) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $null = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing
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
        return @{ Min = 0; Max = 0; Avg = 0; P50 = 0; P95 = 0; P99 = 0; Success = 0; Total = $Data.Count }
    }

    $sorted = $valid | Sort-Object
    $count = $sorted.Count

    return @{
        Min = $sorted[0]
        Max = $sorted[-1]
        Avg = [math]::Round(($sorted | Measure-Object -Average).Average, 2)
        P50 = $sorted[[math]::Floor($count * 0.5)]
        P95 = $sorted[[math]::Floor($count * 0.95)]
        P99 = $sorted[[math]::Floor($count * 0.99)]
        Success = $count
        Total = $Data.Count
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  QUICK- Load Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Concurrency: $Concurrency"
Write-Host "Requests per worker: $Requests"
Write-Host "Total requests: $($Concurrency * $Requests)"
Write-Host ""

$implementations = if ($Compare) { @("quicgo", "tcp") } else { @($Implementation) }

$allResults = @{}

foreach ($impl in $implementations) {
    $port = $Ports[$impl].HTTP
    $url = "http://localhost:$port/"

    Write-Host "Testing $impl (port $port)..." -ForegroundColor Yellow

    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    # Run concurrent workers
    $jobs = @()
    for ($i = 0; $i -lt $Concurrency; $i++) {
        $jobs += Start-Job -ScriptBlock {
            param($Url, $Count)

            $results = @()
            for ($j = 0; $j -lt $Count; $j++) {
                $sw = [System.Diagnostics.Stopwatch]::StartNew()
                try {
                    $null = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing
                    $sw.Stop()
                    $results += $sw.ElapsedMilliseconds
                } catch {
                    $results += -1
                }
            }
            return $results
        } -ArgumentList $url, $Requests
    }

    # Wait for all jobs
    $allLatencies = @()
    foreach ($job in $jobs) {
        $result = Receive-Job -Job $job -Wait
        $allLatencies += $result
        Remove-Job -Job $job
    }

    $sw.Stop()
    $totalTime = $sw.Elapsed.TotalSeconds

    $stats = Get-Stats -Data $allLatencies
    $rps = [math]::Round($stats.Success / $totalTime, 2)

    $allResults[$impl] = @{
        Stats = $stats
        RPS = $rps
        TotalTime = $totalTime
    }

    Write-Host ""
    Write-Host "  Requests:    $($stats.Success)/$($stats.Total) successful" -ForegroundColor $(if ($stats.Success -eq $stats.Total) { "Green" } else { "Yellow" })
    Write-Host "  Duration:    $([math]::Round($totalTime, 2))s"
    Write-Host "  RPS:         $rps req/s"
    Write-Host "  Latency:"
    Write-Host "    Min:       $($stats.Min) ms"
    Write-Host "    Avg:       $($stats.Avg) ms"
    Write-Host "    P50:       $($stats.P50) ms"
    Write-Host "    P95:       $($stats.P95) ms"
    Write-Host "    P99:       $($stats.P99) ms"
    Write-Host "    Max:       $($stats.Max) ms"
    Write-Host ""
}

# Comparison summary
if ($Compare -and $allResults.Count -gt 1) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Comparison Summary" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $header = "{0,-12} {1,10} {2,10} {3,10} {4,10} {5,10}" -f "Impl", "RPS", "Avg(ms)", "P95(ms)", "P99(ms)", "Success%"
    Write-Host $header -ForegroundColor Yellow
    Write-Host ("-" * 65)

    foreach ($impl in $allResults.Keys) {
        $r = $allResults[$impl]
        $successRate = [math]::Round(($r.Stats.Success / $r.Stats.Total) * 100, 1)
        $row = "{0,-12} {1,10} {2,10} {3,10} {4,10} {5,10}%" -f $impl, $r.RPS, $r.Stats.Avg, $r.Stats.P95, $r.Stats.P99, $successRate
        Write-Host $row
    }

    Write-Host ""

    # Performance delta
    if ($allResults.ContainsKey("quicgo") -and $allResults.ContainsKey("tcp")) {
        $quicRPS = $allResults["quicgo"].RPS
        $tcpRPS = $allResults["tcp"].RPS
        $delta = [math]::Round((($quicRPS - $tcpRPS) / $tcpRPS) * 100, 1)

        $color = if ($delta -gt 0) { "Green" } elseif ($delta -lt 0) { "Red" } else { "Yellow" }
        $sign = if ($delta -gt 0) { "+" } else { "" }

        Write-Host "QUIC vs TCP: ${sign}${delta}% throughput" -ForegroundColor $color
    }
}

Write-Host ""
Write-Host "Load test complete" -ForegroundColor Green
