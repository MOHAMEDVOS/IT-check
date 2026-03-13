import sys
import statistics
import math

def analyze_dist(dist_string):
    samples = []
    # parse "40ms x11 | 45ms x25..." or "40ms ×11" (handles x and ×)
    parts = dist_string.replace('x', '×').split('|')
    total_count = 0
    for p in parts:
        p = p.strip()
        if not p: continue
        ms_str, count_str = p.split('×')
        ms = int(ms_str.replace('ms', '').strip())
        count = int(count_str.strip())
        samples.extend([ms] * count)
        total_count += count
    
    if not samples:
        return
        
    avg = sum(samples) / len(samples)
    min_ms = min(samples)
    max_ms = max(samples)
    range_ms = max_ms - min_ms
    std_dev = statistics.stdev(samples) if len(samples) > 1 else 0
    
    # Calculate Jitter
    diffs = [abs(samples[i] - samples[i - 1]) for i in range(1, len(samples))]
    jitter = sum(diffs) / len(diffs) if diffs else 0
    
    # Calculate Spikes (> avg * 1.3 or > 45) -- but using dynamic baseline is better
    baseline = min_ms
    # How many buckets have at least 1 ping?
    unique_buckets = len(set(round(ms/5)*5 for ms in samples))
    
    # How many pings are far from the baseline? (e.g. > baseline + 20ms)
    far_pings = sum(1 for m in samples if m > baseline + 20)
    extreme_pings = sum(1 for m in samples if m > baseline + 80)

    print(f"--- Analysis ---")
    print(f"Total: {total_count}, Avg: {avg:.1f}, Min: {min_ms}, Max: {max_ms}, Range: {range_ms}")
    print(f"StdDev: {std_dev:.1f}, Jitter(sim): {jitter:.1f}")
    print(f"Unique Buckets: {unique_buckets}")
    print(f"Pings > baseline+20ms: {far_pings} ({far_pings/total_count*100:.1f}%)")
    print(f"Pings > baseline+80ms: {extreme_pings} ({extreme_pings/total_count*100:.1f}%)")
    print()

dist1 = "40ms ×11 | 45ms ×25 | 50ms ×1 | 55ms ×2 | 60ms ×1" # FAIR
dist2 = "40ms ×39 | 70ms ×1" # GOOD
dist3 = "45ms ×33 | 50ms ×4 | 105ms ×1 | 195ms ×1 | 210ms ×1|300ms x2 | 150ms ×1  | 75ms ×3  | 95ms ×2 | 85ms ×1 | 115ms ×1 | 105ms ×1 | 195ms ×1" # CRITICAL

print("Example 1 (Expected FAIR)")
analyze_dist(dist1)

print("Example 2 (Expected GOOD)")
analyze_dist(dist2)

print("Example 3 (Expected CRITICAL)")
analyze_dist(dist3)
