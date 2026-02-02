<#
.SYNOPSIS
    QUICK- A/B Benchmark: QUIC Tunnel vs TCP Baseline
.DESCRIPTION
    Compare performance between QUIC tunnel and pure TCP for all protocols
    under various satellite network conditions
.PARAMETER Protocol
    Protocol to test: all, http, ssh, mysql, redis, echo
.PARAMETER Duration
    Test duration in seconds (default: 10)
.PARAMETER Scenario
    Satellite scenario: leo, meo, geo, starlink, oneweb
#>

param(
    [ValidateSet("all", "http", "ssh", "mysql", "redis", "echo", "ftp", "smtp")]
    [string]$Protocol = "all",

    [int]$Duration = 10,

    [ValidateSet("none", "leo", "meo", "geo", "starlink", "oneweb")]
    [string]$Scenario = "none"
)

$ErrorActionPreference = "Continue"

# Port mappings
$QuicPorts = @{
    http     = 8080
    ssh      = 2222
    ftp      = 2121
    smtp     = 2525
    mysql    = 3306
    postgres = 5433
    redis    = 6379
    mqtt     = 1883
    websocket= 8081
    echo     = 9000
    iperf    = 5201
}

$TcpPorts = @{
    http     = 18080
    ssh      = 12222
    ftp      = 10021
    smtp     = 10025
    mysql    = 13306
    postgres = 15433
    redis    = 16379
    mqtt     = 11883
    websocket= 18081
    echo     = 19000
    iperf    = 15201
}

function Write-Header {
    param($msg)
    Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "=" * 70 -ForegroundColor Cyan
}

function Write-Result {
    param($label, $quic, $tcp, $unit)
    $diff = if ($quic -gt 0) { [math]::Round((($tcp - $quic) / $quic) * 100, 1) } else { 0 }
    $diffColor = if ($diff -gt 0) { "Red" } else { "Green" }
    $winner = if ($diff -gt 0) { "QUIC" } else { "TCP" }

    Write-Host ("{0,-20} QUIC: {1,10} {2}  |  TCP: {3,10} {4}  |  " -f $label, $quic, $unit, $tcp, $unit) -NoNewline
    Write-Host ("{0:+0.0;-0.0}% ({1} wins)" -f (-$diff), $winner) -ForegroundColor $diffColor
}

function Measure-Latency {
    param($host_, $port, $samples)

    $latencies = @()
    for ($i = 0; $i -lt $samples; $i++) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect($host_, $port)
            $sw.Stop()
            $latencies += $sw.ElapsedMilliseconds
            $tcp.Close()
        } catch {
            # Connection failed
        }
        Start-Sleep -Milliseconds 100
    }

    if ($latencies.Count -gt 0) {
        return @{
            Min = ($latencies | Measure-Object -Minimum).Minimum
            Max = ($latencies | Measure-Object -Maximum).Maximum
            Avg = [math]::Round(($latencies | Measure-Object -Average).Average, 2)
            Samples = $latencies.Count
        }
    }
    return @{ Min = 0; Max = 0; Avg = 0; Samples = 0 }
}

function Test-HTTP {
    param($port, $label)

    Write-Host "  Testing $label HTTP (port $port)..." -NoNewline

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port/" -TimeoutSec 10 -UseBasicParsing
        $sw.Stop()

        $latency = $sw.ElapsedMilliseconds
        $size = $response.Content.Length

        Write-Host " OK ($latency ms, $size bytes)" -ForegroundColor Green
        return @{ Latency = $latency; Size = $size; Success = $true }
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
        return @{ Latency = 0; Size = 0; Success = $false }
    }
}

function Test-Redis {
    param($port, $label)

    Write-Host "  Testing $label Redis (port $port)..." -NoNewline

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("localhost", $port)
        $stream = $tcp.GetStream()
        $writer = New-Object System.IO.StreamWriter($stream)
        $reader = New-Object System.IO.StreamReader($stream)
        $stream.ReadTimeout = 5000

        # PING command
        $writer.WriteLine("PING")
        $writer.Flush()
        $response = $reader.ReadLine()
        $sw.Stop()

        $tcp.Close()

        if ($response -match "PONG") {
            Write-Host " OK ($($sw.ElapsedMilliseconds) ms)" -ForegroundColor Green
            return @{ Latency = $sw.ElapsedMilliseconds; Success = $true }
        }
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
    }
    return @{ Latency = 0; Success = $false }
}

function Test-Echo {
    param($port, $label)

    Write-Host "  Testing $label Echo (port $port)..." -NoNewline

    $testData = "BENCHMARK-" + (Get-Random -Maximum 99999)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("localhost", $port)
        $stream = $tcp.GetStream()
        $writer = New-Object System.IO.StreamWriter($stream)
        $reader = New-Object System.IO.StreamReader($stream)
        $stream.ReadTimeout = 5000

        $writer.WriteLine($testData)
        $writer.Flush()
        $response = $reader.ReadLine()
        $sw.Stop()

        $tcp.Close()

        if ($response -eq $testData) {
            Write-Host " OK ($($sw.ElapsedMilliseconds) ms)" -ForegroundColor Green
            return @{ Latency = $sw.ElapsedMilliseconds; Success = $true }
        }
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
    }
    return @{ Latency = 0; Success = $false }
}

function Test-MySQL {
    param($port, $label)

    Write-Host "  Testing $label MySQL (port $port)..." -NoNewline

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("localhost", $port)
        $stream = $tcp.GetStream()
        $buffer = New-Object byte[] 256
        $stream.ReadTimeout = 5000
        $read = $stream.Read($buffer, 0, 256)
        $sw.Stop()

        $tcp.Close()

        if ($read -gt 10) {
            Write-Host " OK ($($sw.ElapsedMilliseconds) ms, handshake $read bytes)" -ForegroundColor Green
            return @{ Latency = $sw.ElapsedMilliseconds; Success = $true }
        }
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
    }
    return @{ Latency = 0; Success = $false }
}

function Set-SatelliteScenario {
    param($scenario)

    if ($scenario -eq "none") {
        Write-Host "  No satellite simulation" -ForegroundColor Gray
        return
    }

    Write-Host "  Activating satellite scenario: $scenario" -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8888/scenario/$scenario" -Method POST -TimeoutSec 5
        Write-Host "    RTT: $($response.rtt_ms)ms, Loss: $($response.loss_percent)%" -ForegroundColor Gray
    } catch {
        Write-Host "    Warning: Could not set scenario" -ForegroundColor Red
    }
}

# ============================================================================
# MAIN
# ============================================================================

Write-Header "QUICK- A/B Benchmark: QUIC vs TCP"
Write-Host "  Protocol: $Protocol"
Write-Host "  Duration: $Duration seconds"
Write-Host "  Scenario: $Scenario"
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Set satellite scenario
Set-SatelliteScenario -scenario $Scenario

$results = @{}

# HTTP Test
if ($Protocol -eq "all" -or $Protocol -eq "http") {
    Write-Header "HTTP Benchmark"

    $quicHttp = Test-HTTP -port $QuicPorts.http -label "QUIC"
    $tcpHttp = Test-HTTP -port $TcpPorts.http -label "TCP"

    if ($quicHttp.Success -and $tcpHttp.Success) {
        Write-Result -label "HTTP Latency" -quic $quicHttp.Latency -tcp $tcpHttp.Latency -unit "ms"
    }
    $results["http"] = @{ QUIC = $quicHttp; TCP = $tcpHttp }
}

# Redis Test
if ($Protocol -eq "all" -or $Protocol -eq "redis") {
    Write-Header "Redis Benchmark"

    $quicRedis = Test-Redis -port $QuicPorts.redis -label "QUIC"
    $tcpRedis = Test-Redis -port $TcpPorts.redis -label "TCP"

    if ($quicRedis.Success -and $tcpRedis.Success) {
        Write-Result -label "Redis PING" -quic $quicRedis.Latency -tcp $tcpRedis.Latency -unit "ms"
    }
    $results["redis"] = @{ QUIC = $quicRedis; TCP = $tcpRedis }
}

# Echo Test
if ($Protocol -eq "all" -or $Protocol -eq "echo") {
    Write-Header "Echo Benchmark"

    $quicEcho = Test-Echo -port $QuicPorts.echo -label "QUIC"
    $tcpEcho = Test-Echo -port $TcpPorts.echo -label "TCP"

    if ($quicEcho.Success -and $tcpEcho.Success) {
        Write-Result -label "Echo RTT" -quic $quicEcho.Latency -tcp $tcpEcho.Latency -unit "ms"
    }
    $results["echo"] = @{ QUIC = $quicEcho; TCP = $tcpEcho }
}

# MySQL Test
if ($Protocol -eq "all" -or $Protocol -eq "mysql") {
    Write-Header "MySQL Benchmark"

    $quicMysql = Test-MySQL -port $QuicPorts.mysql -label "QUIC"
    $tcpMysql = Test-MySQL -port $TcpPorts.mysql -label "TCP"

    if ($quicMysql.Success -and $tcpMysql.Success) {
        Write-Result -label "MySQL Handshake" -quic $quicMysql.Latency -tcp $tcpMysql.Latency -unit "ms"
    }
    $results["mysql"] = @{ QUIC = $quicMysql; TCP = $tcpMysql }
}

# Connection Latency Test (multiple samples)
Write-Header "Connection Latency (10 samples)"

$protocols = @("http", "redis", "echo", "mysql")
foreach ($proto in $protocols) {
    if ($Protocol -eq "all" -or $Protocol -eq $proto) {
        $quicLatency = Measure-Latency -host_ "localhost" -port $QuicPorts[$proto] -samples 10
        $tcpLatency = Measure-Latency -host_ "localhost" -port $TcpPorts[$proto] -samples 10

        if ($quicLatency.Samples -gt 0 -and $tcpLatency.Samples -gt 0) {
            Write-Result -label "$proto Conn Avg" -quic $quicLatency.Avg -tcp $tcpLatency.Avg -unit "ms"
        }
    }
}

# Summary
Write-Header "SUMMARY"

$quicWins = 0
$tcpWins = 0

foreach ($proto in $results.Keys) {
    $q = $results[$proto].QUIC.Latency
    $t = $results[$proto].TCP.Latency
    if ($q -gt 0 -and $t -gt 0) {
        if ($q -lt $t) { $quicWins++ } else { $tcpWins++ }
    }
}

Write-Host ""
Write-Host "  QUIC Tunnel Wins: $quicWins" -ForegroundColor $(if ($quicWins -gt $tcpWins) { "Green" } else { "White" })
Write-Host "  TCP Baseline Wins: $tcpWins" -ForegroundColor $(if ($tcpWins -gt $quicWins) { "Green" } else { "White" })
Write-Host ""

if ($Scenario -ne "none") {
    Write-Host "  Note: Results under satellite scenario '$Scenario'" -ForegroundColor Yellow
    Write-Host "  QUIC should show better performance under high latency/loss conditions" -ForegroundColor Gray
}

# Reset satellite scenario
if ($Scenario -ne "none") {
    try {
        Invoke-RestMethod -Uri "http://localhost:8888/scenario/none" -Method POST -TimeoutSec 5 | Out-Null
    } catch {}
}

Write-Host ""
Write-Host "Benchmark completed at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
