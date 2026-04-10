"""
ping.py — Smart ping diagnostics tuned for VoIP/call-center stability (Readymode).
Goes beyond Avg/Max — measures jitter, detects spikes, scores call quality.
"""

import subprocess
import re
import statistics
from dataclasses import dataclass, field
from typing import List, Optional


# ── Thresholds (STRICT — tuned for VoIP / Readymode call quality) ───────────
SPIKE_MULTIPLIER    = 1.3    # >1.3× the average is a spike (strict)
SPIKE_ABS_MS        = 45     # Any ping above 45ms is considered a spike
JITTER_GOOD_MS      = 5      # 0-5 ms jitter = Excellent
JITTER_OK_MS        = 6      # 5-6 ms jitter = Good
JITTER_PROBLEM_MS   = 9      # 9+ ms jitter = Can cause problems
AVG_GOOD_MS         = 30     # Avg RTT under 30ms = good for VoIP
AVG_OK_MS           = 50     # Avg RTT under 50ms = marginal
LOSS_GOOD_PCT       = 0      # Zero loss = good
LOSS_OK_PCT         = 0.5    # Up to 0.5% loss = marginal
CONSISTENCY_GOOD_MS = 3      # Std dev under 3ms = rock solid
CONSISTENCY_OK_MS   = 8      # Std dev under 8ms = acceptable
PING_COUNT          = 20     # Pings per round
PING_ROUNDS         = 2      # Number of rounds (final score = all rounds combined)


@dataclass
class PingResult:
    host: str
    samples: List[int]              = field(default_factory=list)

    avg_rtt: float                  = 0.0
    min_rtt: int                    = 0
    max_rtt: int                    = 0
    jitter: float                   = 0.0          # avg diff between consecutive pings
    std_dev: float                  = 0.0          # statistical spread
    packet_loss_pct: float          = 0.0

    spikes: List[int]               = field(default_factory=list)   # spike values
    spike_count: int                = 0
    spike_indices: List[int]        = field(default_factory=list)   # which ping # spiked

    stability_score: int            = 0            # 0–100
    verdict: str                    = ""           # EXCELLENT / GOOD / MARGINAL / POOR / CRITICAL
    verdict_color: str              = ""           # green / yellow / orange / red
    call_quality_notes: List[str]   = field(default_factory=list)
    latency_distribution: str       = ""           # e.g. "40ms ×47 | 78ms ×1"

    error: Optional[str]            = None


def _parse_ping_ms(line: str) -> Optional[int]:
    """Extract RTT value in ms from a Windows ping reply line."""
    match = re.search(r'time[=<](\d+)ms', line, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _calc_jitter(samples: List[int]) -> float:
    """Jitter = mean of absolute differences between consecutive samples (MOS-style)."""
    if len(samples) < 2:
        return 0.0
    diffs = [abs(samples[i] - samples[i - 1]) for i in range(1, len(samples))]
    return round(statistics.mean(diffs), 1)


def _detect_spikes(samples: List[int], avg: float) -> tuple:
    """
    Return (spike_values, spike_indices).
    A spike = ping > (avg * SPIKE_MULTIPLIER) OR ping > SPIKE_ABS_MS
    """
    spikes, indices = [], []
    for i, ms in enumerate(samples):
        if ms > (avg * SPIKE_MULTIPLIER) or ms > SPIKE_ABS_MS:
            spikes.append(ms)
            indices.append(i + 1)   # 1-based ping number
    return spikes, indices


def _build_latency_distribution(samples: List[int]) -> str:
    """
    Groups ping samples into 5ms-wide buckets and returns a compact summary.
    e.g. "40ms ×47 | 45ms ×2 | 78ms ×1"
    Only shows buckets that actually have pings.
    """
    if not samples:
        return ""
    from collections import Counter
    # Round each sample to nearest 5ms bucket
    buckets = Counter(round(ms / 5) * 5 for ms in samples)
    parts = [f"{ms}ms ×{count}" for ms, count in sorted(buckets.items())]
    return " | ".join(parts)


def _score_and_verdict(result: PingResult) -> tuple:
    """
    Distribution-Based Ping Scoring.
    Decides connection quality strictly based on Standard Deviation and 
    the percentage of pings exceeding a dynamic baseline.
    Returns (score, verdict, color, notes[])
    """
    notes = []
    
    if not result.samples:
        return 0, "CRITICAL", "#EF4444", ["Ping failed entirely"]

    baseline = result.min_rtt
    total_samples = len(result.samples)
    
    # Count how many pings spike more than 20ms above the absolute best ping
    far_pings = sum(1 for ms in result.samples if ms > baseline + 20)
    far_pings_pct = (far_pings / total_samples) * 100
    std_dev = result.std_dev

    # Calculate Jitter (just for dashboard reporting)
    result.jitter = _calc_jitter(result.samples)

    # ── Rule 3: Critical / Poor
    if far_pings_pct > 10.0 or std_dev > 15.0 or result.packet_loss_pct > 3.0:
        score = 25
        verdict, color = "POOR", "#EF4444"
        notes.append(f"Severely unstable: {far_pings_pct:.1f}% of pings spiked heavily (σ={std_dev}ms).")
        notes.append("Calls will drop or have massive delays.")

    # ── Rule 2: Fair / Unstable
    elif far_pings_pct > 0.0 or std_dev > 5.0 or result.packet_loss_pct > 0.0:
        score = 60
        verdict, color = "MARGINAL", "#F97316"
        notes.append(f"Fluctuating network. {far_pings_pct:.1f}% of pings spiked above baseline.")
        notes.append("Audio might become robotic or choppy briefly.")

    # ── Rule 1: Good / Excellent
    else:
        score = 95
        verdict, color = "GOOD", "#22D3EE"
        notes.append("Rock-solid connection. 0% of pings spiked above baseline.")
        notes.append(f"Standard deviation perfectly tight at {std_dev}ms.")
        
    return score, verdict, color, notes


def _run_single_round(host: str, count: int) -> tuple:
    """Runs one batch of `count` pings. Returns (samples, sent, lost)."""
    samples = []
    lost = 0
    proc = None
    try:
        proc = subprocess.Popen(
            ["ping", host, "-n", str(count)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        try:
            stdout, _ = proc.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.communicate(timeout=5)
            except Exception:
                pass
            return samples, count, count  # count everything as lost
        for line in stdout.splitlines():
            ms = _parse_ping_ms(line)
            if ms is not None:
                samples.append(ms)
        loss_match = re.search(r'(\d+)%\s+loss', stdout, re.IGNORECASE)
        if loss_match:
            lost = round(count * float(loss_match.group(1)) / 100)
    except Exception:
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass
    return samples, count, lost


def run_ping(host: str, callback=None) -> PingResult:
    """
    Runs PING_ROUNDS rounds of PING_COUNT pings each.
    Merges all samples from all rounds before computing the final stability score.
    This gives a more reliable verdict than a single short burst.
    """
    host = re.sub(r'^https?://', '', host).strip().rstrip('/')
    result = PingResult(host=host)

    all_samples  = []
    total_sent   = 0
    total_lost   = 0

    try:
        for rnd in range(1, PING_ROUNDS + 1):
            if callback:
                callback(f"Round {rnd}/{PING_ROUNDS} — pinging {host}...")

            samples, sent, lost = _run_single_round(host, PING_COUNT)
            all_samples.extend(samples)
            total_sent  += sent
            total_lost  += lost

        if not all_samples:
            result.error = f"No ping replies received from {host}."
            result.verdict = "UNREACHABLE"
            result.verdict_color = "#EF4444"
            return result

        result.samples = all_samples

        # ── Packet loss across all rounds ─────────────────────────────────────
        result.packet_loss_pct = round((total_lost / total_sent) * 100, 1) if total_sent else 0.0

        # ── Core metrics ─────────────────────────────────────────────────────
        result.avg_rtt = round(statistics.mean(all_samples), 1)
        result.min_rtt = min(all_samples)
        result.max_rtt = max(all_samples)
        result.jitter  = _calc_jitter(all_samples)
        result.std_dev = round(statistics.stdev(all_samples), 1) if len(all_samples) > 1 else 0.0

        # ── Spike detection ──────────────────────────────────────────────────
        result.spikes, result.spike_indices = _detect_spikes(all_samples, result.avg_rtt)
        result.spike_count = len(result.spikes)

        # ── Score & verdict ──────────────────────────────────────────────────
        (result.stability_score,
         result.verdict,
         result.verdict_color,
         result.call_quality_notes) = _score_and_verdict(result)

        # ── Latency distribution ─────────────────────────────────────────────
        result.latency_distribution = _build_latency_distribution(all_samples)

    except subprocess.TimeoutExpired:
        result.error = "Ping timed out."
        result.verdict = "TIMEOUT"
        result.verdict_color = "#EF4444"

    except FileNotFoundError:
        result.error = "ping.exe not found. Are you running on Windows?"
        result.verdict = "ERROR"
        result.verdict_color = "#EF4444"

    except Exception as e:
        result.error = str(e)
        result.verdict = "ERROR"
        result.verdict_color = "#EF4444"

    return result
