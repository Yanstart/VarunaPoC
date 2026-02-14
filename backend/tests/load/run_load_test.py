#!/usr/bin/env python3
"""
Load Test Runner — CLI wrapper for Locust headless mode.

Runs the pathologist simulation, parses CSV results,
and prints a formatted summary with pass/fail exit codes.

Usage:
    python tests/load/run_load_test.py
    python tests/load/run_load_test.py --users 10 --duration 120 --host http://localhost:8000
    python tests/load/run_load_test.py --error-threshold 5.0  # fail if > 5% errors
"""

import argparse
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def parse_args():
    parser = argparse.ArgumentParser(description="VarunaPoC Load Test Runner")
    parser.add_argument(
        "--users",
        "-u",
        type=int,
        default=10,
        help="Number of concurrent users (default: 10)",
    )
    parser.add_argument(
        "--spawn-rate",
        "-r",
        type=float,
        default=2,
        help="Users spawned per second (default: 2)",
    )
    parser.add_argument(
        "--duration",
        "-t",
        type=int,
        default=120,
        help="Test duration in seconds (default: 120)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="http://localhost:8000",
        help="Target host URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--error-threshold",
        type=float,
        default=10.0,
        help="Max error rate %% before failing (default: 10.0)",
    )
    return parser.parse_args()


def print_header(args):
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}  VarunaPoC Load Test — Pathologist Simulation{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"  {BOLD}Host:{RESET}           {args.host}")
    print(f"  {BOLD}Users:{RESET}          {args.users}")
    print(f"  {BOLD}Spawn rate:{RESET}     {args.spawn_rate}/s")
    print(f"  {BOLD}Duration:{RESET}       {args.duration}s")
    print(f"  {BOLD}Error threshold:{RESET} {args.error_threshold}%")
    print(f"{BLUE}{'─' * 60}{RESET}\n")


def run_locust(args, csv_prefix):
    """Run Locust in headless mode with CSV output."""
    locustfile = Path(__file__).parent / "locustfile.py"

    cmd = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(locustfile),
        "--headless",
        "-u",
        str(args.users),
        "-r",
        str(args.spawn_rate),
        "-t",
        f"{args.duration}s",
        "--host",
        args.host,
        "--csv",
        csv_prefix,
        "--csv-full-history",
    ]

    print(f"{YELLOW}Running: {' '.join(cmd)}{RESET}\n")

    result = subprocess.run(
        cmd,
        capture_output=False,
        check=False,
        timeout=args.duration + 60,  # grace period
    )
    return result.returncode


def parse_results(csv_prefix):
    """Parse Locust CSV output and return summary dict."""
    stats_file = f"{csv_prefix}_stats.csv"

    stats_path = Path(stats_file)
    if not stats_path.exists():
        print(f"{RED}Error: Stats file not found: {stats_file}{RESET}")
        return None

    results = {
        "endpoints": [],
        "total_requests": 0,
        "total_failures": 0,
        "error_rate": 0.0,
    }

    with stats_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "")
            req_count = int(row.get("Request Count", 0))
            fail_count = int(row.get("Failure Count", 0))

            if name == "Aggregated":
                results["total_requests"] = req_count
                results["total_failures"] = fail_count
                results["error_rate"] = (fail_count / req_count * 100) if req_count > 0 else 0.0
                results["avg_response"] = float(row.get("Average Response Time", 0))
                results["p50"] = float(row.get("50%", 0))
                results["p95"] = float(row.get("95%", 0))
                results["p99"] = float(row.get("99%", 0))
                results["rps"] = float(row.get("Requests/s", 0))
            else:
                results["endpoints"].append(
                    {
                        "name": name,
                        "method": row.get("Type", ""),
                        "requests": req_count,
                        "failures": fail_count,
                        "avg_ms": float(row.get("Average Response Time", 0)),
                        "p95_ms": float(row.get("95%", 0)),
                        "p99_ms": float(row.get("99%", 0)),
                    }
                )

    return results


def print_results(results, threshold):
    """Print formatted results summary."""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}  Load Test Results{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")

    # Per-endpoint table
    print(
        f"  {BOLD}{'Endpoint':<45} {'Reqs':>6} {'Fail':>6} {'Avg':>7} {'P95':>7} {'P99':>7}{RESET}"
    )
    print(f"  {'─' * 78}")
    for ep in results["endpoints"]:
        fail_color = RED if ep["failures"] > 0 else GREEN
        print(
            f"  {ep['method'] + ' ' + ep['name']:<45} "
            f"{ep['requests']:>6} "
            f"{fail_color}{ep['failures']:>6}{RESET} "
            f"{ep['avg_ms']:>6.0f}ms "
            f"{ep['p95_ms']:>6.0f}ms "
            f"{ep['p99_ms']:>6.0f}ms"
        )
    print(f"  {'─' * 78}")

    # Summary
    print(f"\n  {BOLD}Total requests:{RESET}  {results['total_requests']}")
    print(f"  {BOLD}Total failures:{RESET}  {results['total_failures']}")
    print(f"  {BOLD}Throughput:{RESET}       {results.get('rps', 0):.1f} req/s")
    print(f"  {BOLD}Avg response:{RESET}     {results.get('avg_response', 0):.0f}ms")

    # Percentiles
    print(f"\n  {BOLD}Latency percentiles:{RESET}")
    print(f"    P50: {results.get('p50', 0):.0f}ms")
    print(f"    P95: {results.get('p95', 0):.0f}ms")
    print(f"    P99: {results.get('p99', 0):.0f}ms")

    # Pass/Fail
    error_rate = results["error_rate"]
    if error_rate <= threshold:
        print(
            f"\n  {GREEN}{BOLD}PASS{RESET} — Error rate: {error_rate:.1f}% (threshold: {threshold}%)"
        )
        return True
    else:
        print(
            f"\n  {RED}{BOLD}FAIL{RESET} — Error rate: {error_rate:.1f}% (threshold: {threshold}%)"
        )
        return False


def main():
    args = parse_args()
    print_header(args)

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_prefix = str(Path(tmpdir) / "varuna_load")

        exit_code = run_locust(args, csv_prefix)

        if exit_code != 0:
            print(f"\n{RED}Locust exited with code {exit_code}{RESET}")

        results = parse_results(csv_prefix)

        if results is None:
            print(f"{RED}Could not parse results.{RESET}")
            sys.exit(1)

        passed = print_results(results, args.error_threshold)
        print()

        sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
