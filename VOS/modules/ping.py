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
    Strict VoIP scoring 0–100. Weighted:
      - Consistency (std_dev + range)  25%  (distribution spread matters!)
      - Jitter                         25%  (critical for voice)
      - Avg RTT                        20%  (latency matters for calls)
      - Packet Loss                    20%
      - Spike Count                    10%
    Returns (score, verdict, color, notes[])
    """
    notes = []
    score = 100

    # ── 1. Consistency / Distribution penalty (NEW — 25 pts) ─────────────────
    #    This catches the exact scenario: 40ms ×21 | 45ms ×15 | 50ms ×3 | 60ms ×1
    #    Even if jitter looks "ok", spread across buckets = inconsistent
    if result.samples:
        ping_range = result.max_rtt - result.min_rtt
        if result.std_dev <= CONSISTENCY_GOOD_MS and ping_range <= 5:
            pass  # Rock solid — all pings land in same bucket
        elif result.std_dev <= CONSISTENCY_OK_MS and ping_range <= 15:
            score -= 10
            notes.append(f"Ping spread {result.min_rtt}-{result.max_rtt}ms (σ={result.std_dev}ms) — minor inconsistency")
        elif result.std_dev <= 15 or ping_range <= 30:
            score -= 15
            notes.append(f"Ping spread {result.min_rtt}-{result.max_rtt}ms (σ={result.std_dev}ms) — inconsistent, may cause audio artifacts")
        else:
            score -= 30
            notes.append(f"Ping spread {result.min_rtt}-{result.max_rtt}ms (σ={result.std_dev}ms) — very unstable for VoIP")

    # ── 2. Jitter penalty (25 pts) ───────────────────────────────────────────
    if result.jitter <= JITTER_GOOD_MS:
        pass  # Excellent (0-5 ms)
    elif result.jitter <= JITTER_OK_MS:
        score -= 5
        notes.append(f"Jitter {result.jitter}ms — good")
    elif result.jitter < JITTER_PROBLEM_MS:
        score -= 8
        notes.append(f"Jitter {result.jitter}ms — acceptable, but some fluctuations")
    elif result.jitter <= 15:
        score -= 20
        notes.append(f"Jitter {result.jitter}ms — can cause problems (choppy audio likely)")
    elif result.jitter <= 30:
        score -= 30
        notes.append(f"High jitter {result.jitter}ms — expect choppy, robotic audio")
    else:
        score -= 40
        notes.append(f"Severe jitter {result.jitter}ms — calls will be heavily distorted")

    # ── 3. Avg RTT penalty (20 pts) ──────────────────────────────────────────
    if result.avg_rtt <= AVG_GOOD_MS:
        pass  # Great
    elif result.avg_rtt <= AVG_OK_MS:
        score -= 12
        notes.append(f"Latency {result.avg_rtt:.0f}ms — noticeable delay, talk-over-talk on calls")
    elif result.avg_rtt <= 80:
        score -= 20
        notes.append(f"Latency {result.avg_rtt:.0f}ms — significant delay, awkward pauses in conversation")
    elif result.avg_rtt <= 120:
        score -= 30
        notes.append(f"High latency {result.avg_rtt:.0f}ms — callers will talk over each other constantly")
    else:
        score -= 40
        notes.append(f"Very high latency {result.avg_rtt:.0f}ms — unusable for professional calls")

    # ── 4. Packet loss penalty (20 pts) ──────────────────────────────────────
    if result.packet_loss_pct == 0:
        pass
    elif result.packet_loss_pct <= LOSS_OK_PCT:
        score -= 10
        notes.append(f"{result.packet_loss_pct}% loss — rare audio dropouts possible")
    elif result.packet_loss_pct <= 1:
        score -= 15
        notes.append(f"{result.packet_loss_pct}% loss — some words will be cut off")
    elif result.packet_loss_pct <= 3:
        score -= 25
        notes.append(f"{result.packet_loss_pct}% loss — frequent missing audio chunks")
    else:
        score -= 35
        notes.append(f"{result.packet_loss_pct}% loss — severe: entire sentences will drop")

    # ── 5. Spike penalty (10 pts) ────────────────────────────────────────────
    spike_rate = (result.spike_count / len(result.samples) * 100) if result.samples else 0
    if result.spike_count == 0:
        pass
    elif result.spike_count <= 2:
        score -= 8
        notes.append(f"{result.spike_count} spike(s) detected — brief delay bursts during calls")
    elif result.spike_count <= 5:
        score -= 15
        notes.append(f"{result.spike_count} spikes ({spike_rate:.0f}%) — repeated lag bursts, callers hear gaps")
    elif spike_rate <= 20:
        score -= 20
        notes.append(f"{result.spike_count} spikes ({spike_rate:.0f}%) — frequent lag, unreliable for calls")
    else:
        score -= 35
        notes.append(f"{result.spike_count} spikes ({spike_rate:.0f}%) — connection too unstable for any voice work")

    score = max(0, score)

    # ── Verdict (balanced cutoffs: POOR only for clearly bad connections) ───
    if score >= 92:
        verdict, color = "EXCELLENT", "#22D3EE"
        notes.insert(0, "Rock-solid for Readymode calls")
    elif score >= 80:
        verdict, color = "GOOD", "#22D3EE"
        notes.insert(0, "Good enough for calls, minor room for improvement")
    elif score >= 65:
        verdict, color = "FAIR", "#F59E0B"
        notes.insert(0, "Usable but expect occasional call quality issues")
    elif score >= 35:
        verdict, color = "MARGINAL", "#F97316"
        # Softer wording for marginal connections — strong warning is reserved for POOR/CRITICAL
        notes.insert(0, "Connection is marginal but usually OK — keep an eye on call quality")
    elif score >= 20:
        verdict, color = "POOR", "#EF4444"
        notes.insert(0, "Calls will have frequent audio problems — action required")
    else:
        verdict, color = "CRITICAL", "#EF4444"
        notes.insert(0, "Connection unusable for calls — DO NOT use for customer calls")

    return score, verdict, color, notes


def _run_single_round(host: str, count: int) -> tuple:
    """Runs one batch of `count` pings. Returns (samples, sent, lost)."""
    samples = []
    lost = 0
    try:
        proc = subprocess.Popen(
            ["ping", host, "-n", str(count)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        stdout, _ = proc.communicate(timeout=120)
        for line in stdout.splitlines():
            ms = _parse_ping_ms(line)
            if ms is not None:
                samples.append(ms)
        loss_match = re.search(r'(\d+)%\s+loss', stdout, re.IGNORECASE)
        if loss_match:
            lost = round(count * float(loss_match.group(1)) / 100)
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
