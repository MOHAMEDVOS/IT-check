import psutil
import platform


def _get_cpu_model_fast() -> str:
    """
    Get CPU model name quickly via Windows Registry.

    Note: we deliberately do NOT use `py-cpuinfo` — it internally spawns a
    `multiprocessing.Process` which, in a PyInstaller-frozen .exe, launches a
    whole new copy of this app. That child process briefly steals window
    focus and causes the main window to appear minimized after the user
    clicks "Check My System". The Windows Registry path below is instant,
    reliable, and has no subprocess side-effects.
    """
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            )
            try:
                name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            finally:
                winreg.CloseKey(key)
            if name:
                return name.strip()
        except Exception:
            pass

    proc = platform.processor()
    if proc:
        return proc

    return "Unknown CPU"


def get_cpu_performance(model_name: str) -> tuple:
    """
    Table-driven scoring against an Intel i5 6th Gen baseline (Score 100).
    Returns (score, label).
    Covers: Intel Core i/Ultra/N/Xeon/Celeron/Pentium/Atom,
            AMD Ryzen/Threadripper/FX/Phenom/Athlon/APU,
            Apple Silicon, Qualcomm Snapdragon.
    """
    import re

    raw = model_name
    # Normalize: strip trademarks, fancy dashes, collapse whitespace
    t = raw.upper()
    t = re.sub(r'\((?:TM|R|©|®)\)', '', t)
    t = re.sub(r'[\u2010-\u2015]', '-', t)
    t = re.sub(r'\s+', ' ', t).strip()

    # ── Scoring tables (baseline = Intel i5 6th Gen = 100) ──────────────

    INTEL_GEN_SCORE = {
        1: 29, 2: 43, 3: 63, 4: 83, 5: 89,
        6: 100, 7: 109, 8: 148, 9: 158, 10: 168,
        11: 196, 12: 262, 13: 312, 14: 328
    }
    INTEL_FAM_MULT  = {3: 0.78, 5: 1.0, 7: 1.22, 9: 1.55}
    INTEL_SUFFIX_MULT = {
        'Y': 0.75, 'U': 1.0, 'P': 1.15, 'M': 1.1, 'MQ': 1.35, 'MX': 1.45,
        'H': 1.55, 'HQ': 1.55, 'HK': 1.62, 'HS': 1.55, 'HF': 1.55,
        'G7': 1.0, 'G4': 0.92, 'G1': 0.88,
        'T': 1.42, 'S': 1.78, 'F': 1.72,
        'K': 1.85, 'KF': 1.82, 'KS': 1.88,
        'X': 2.1, 'XE': 2.25, '': 1.0,
    }
    CORE_ULTRA_TIER = {5: 280, 7: 340, 9: 400}
    CORE_ULTRA_SFXM = {'U': 0.80, 'H': 1.0, 'HX': 1.15, '': 1.0}
    INTEL_N_SCORE   = {'N100': 42, 'N200': 38, 'N95': 40, 'N97': 42, 'N300': 48, 'N305': 52}
    XEON_TIER_SCORE = {
        'E3': 110, 'E5': 140, 'E7': 160, 'D': 120, 'W': 180,
        'BRONZE': 130, 'SILVER': 160, 'GOLD': 200, 'PLATINUM': 260,
    }
    CELERON_PFX     = {'N': 25, 'J': 30, 'G': 45, 'P': 28}
    PENTIUM_TIER    = {'GOLD': 55, 'SILVER': 40, 'STANDARD': 45}

    RYZEN_SER_SCORE = {
        1000: 55, 2000: 70, 3000: 105, 4000: 140, 5000: 230,
        6000: 248, 7000: 320, 8000: 338, 9000: 360,
    }
    RYZEN_TIER_MULT  = {3: 0.76, 5: 1.0, 7: 1.22, 9: 1.55}
    RYZEN_SUFFIX_MULT = {
        'U': 0.90, 'HS': 1.45, 'H': 1.4, 'HX': 1.5,
        'G': 1.3, 'GE': 1.25, 'X': 1.2, 'X3D': 1.25, 'XS': 1.15, '': 1.0,
    }
    TR_SERIES_SCORE = {1000: 200, 2000: 260, 3000: 350, 5000: 450, 7000: 550}
    FX_CORE_SCORE   = {4: 50, 6: 62, 8: 75, 9: 82}

    APPLE_GEN_SCORE = {1: 260, 2: 320, 3: 375, 4: 420, 5: 480}
    APPLE_TIER_MULT = {'BASE': 1.0, 'PRO': 1.25, 'MAX': 1.55, 'ULTRA': 2.0}

    SNAPDRAGON_SCORE = {
        'X_ELITE': 310, 'X_PLUS': 240,
        '8CX_GEN3': 130, '8CX_GEN2': 100, '8CX': 85,
        '7C_PLUS_GEN3': 75, '7C_PLUS': 55, '7C': 45,
    }

    score = None

    # ── Intel Core Ultra ────────────────────────────────────────────────
    m = re.search(r'CORE\s+ULTRA\s+([579])\s+(\d{3})([A-Z]{0,2})?', t)
    if m:
        tier   = int(m.group(1))
        suffix = (m.group(3) or '').strip()
        base   = CORE_ULTRA_TIER.get(tier, 300)
        score  = round(base * CORE_ULTRA_SFXM.get(suffix, 1.0))

    # ── Intel Core i3/i5/i7/i9 ──────────────────────────────────────────
    if score is None:
        fam_m = re.search(r'\bI([3579])\b', t)
        if fam_m:
            family_num = int(fam_m.group(1))
            gen        = None
            suffix     = ''

            # Model number → gen  (e.g. I5-10400 → gen 10, I7-1255U → gen 12)
            mod_m = re.search(r'I[3579][-\s]?(\d{4,5})([A-Z]{0,3})?', t)
            if mod_m:
                num_str = mod_m.group(1)
                suffix  = (mod_m.group(2) or '').strip()
                if len(num_str) == 5:
                    gen = int(num_str[:2])   # e.g. 10400 → gen 10
                else:
                    # 4-digit: first digit is gen for 2xxx-9xxx.
                    # But Intel Alder/Raptor Lake use 1200-1299 (gen 12),
                    # Tiger Lake 1100-1195 (gen 11), Ice Lake 1000-1068 (gen 10).
                    first = int(num_str[0])
                    second = int(num_str[1])
                    if first == 1:
                        # Distinguish by hundreds digit
                        if second >= 2:
                            gen = 10 + second  # 12xx→12, 13xx→13, 14xx→14
                        elif second == 1:
                            gen = 11
                        else:
                            gen = 10  # 10xx Ice Lake
                    else:
                        gen = first  # 6500→6, 7500→7, 8265→8, 9600→9

            # Explicit "Nth Gen" beats model-number detection
            exp_m = re.search(r'(?:(\d{1,2})(?:ST|ND|RD|TH)\s*GEN|GEN\s*(\d{1,2}))', t)
            if exp_m:
                gen = int(exp_m.group(1) or exp_m.group(2))

            if gen is not None:
                g = INTEL_GEN_SCORE.get(gen, 100)
                f = INTEL_FAM_MULT.get(family_num, 1.0)
                s = INTEL_SUFFIX_MULT.get(suffix, 1.0)
                score = round(g * f * s)

    # ── Intel N-series (N100/N200/N305 …) ──────────────────────────────
    if score is None:
        m = re.search(r'(?:INTEL\s+)?(?:PROCESSOR\s+)?(N\d{3})\b', t)
        if m:
            score = INTEL_N_SCORE.get(m.group(1), 40)

    # ── Intel Xeon ──────────────────────────────────────────────────────
    if score is None:
        m = re.search(r'XEON\s+(E3|E5|E7|D|W|GOLD|PLATINUM|SILVER|BRONZE)[-\s]?\d{4,5}', t)
        if m:
            score = XEON_TIER_SCORE.get(m.group(1), 130)
        elif 'XEON' in t:
            score = 130  # bare Xeon fallback

    # ── Intel Celeron ────────────────────────────────────────────────────
    if score is None:
        m = re.search(r'CELERON\s+([NGJP])(\d{3,5})', t)
        if m:
            pfx = m.group(1)
            num = int(m.group(2))
            base = CELERON_PFX.get(pfx, 25)
            if   num >= 6000: base += 15
            elif num >= 5000: base += 8
            elif num >= 4000: base += 2
            score = base

    # ── Intel Pentium ────────────────────────────────────────────────────
    if score is None:
        if 'PENTIUM' in t:
            tier_m = re.search(r'PENTIUM\s+(GOLD|SILVER)', t)
            tier   = tier_m.group(1) if tier_m else 'STANDARD'
            base   = PENTIUM_TIER.get(tier, 45)
            num_m  = re.search(r'[NGJP](\d{4,5})', t)
            if num_m:
                num = int(num_m.group(1))
                if   num >= 7000: base += 10
                elif num >= 6000: base += 5
            score = base

    # ── Intel Atom ───────────────────────────────────────────────────────
    if score is None and 'ATOM' in t:
        score = 18

    # ── AMD Ryzen ────────────────────────────────────────────────────────
    if score is None:
        m = re.search(r'RYZEN\s*([3579])\s+(?:PRO\s+)?(\d{4,5})([A-Z]{0,3})?', t)
        if m:
            tier       = int(m.group(1))
            series_num = int(m.group(2))
            suffix     = (m.group(3) or '').strip()
            series_base = (series_num // 1000) * 1000
            s = RYZEN_SER_SCORE.get(series_base, 100)
            tm = RYZEN_TIER_MULT.get(tier, 1.0)
            sm = RYZEN_SUFFIX_MULT.get(suffix, 1.0)
            score = round(s * tm * sm)

    # ── AMD Threadripper ─────────────────────────────────────────────────
    if score is None:
        m = re.search(r'THREADRIPPER\s+(?:PRO\s+)?(\d{4})', t)
        if m:
            model_num  = int(m.group(1))
            series_base = (model_num // 1000) * 1000
            base   = TR_SERIES_SCORE.get(series_base, 300)
            is_pro = 'THREADRIPPER PRO' in t
            score  = round(base * 1.15) if is_pro else base

    # ── AMD FX ───────────────────────────────────────────────────────────
    if score is None:
        m = re.search(r'\bFX[-\s](\d{4})', t)
        if m:
            core_prefix = int(m.group(1)[0])
            score = FX_CORE_SCORE.get(core_prefix, 60)

    # ── AMD Legacy APU (A4/A6/A8/A10/A12, E/E1/E2) ───────────────────
    if score is None:
        AMD_APU_SCORE = {'E': 8, 'E1': 12, 'E2': 18, 'A4': 18, 'A6': 26, 'A8': 40, 'A10': 55, 'A12': 62}
        m = re.search(r'\b(E2|E1|E|A(?:4|6|8|10|12))[-\s](\d{4,5})', t)
        if m:
            score = AMD_APU_SCORE.get(m.group(1), 25)

    # ── Intel/AMD low-end catch-all ───────────────────────────────────────
    if score is None and any(x in t for x in ['CELERON', 'PENTIUM', 'ATOM']):
        score = 40

    # ── Apple Silicon ────────────────────────────────────────────────────
    if score is None:
        m = re.search(r'\bM([1-9]\d?)(?:\s+(PRO|MAX|ULTRA))?\b', t)
        if m:
            gen  = int(m.group(1))
            tier = (m.group(2) or 'BASE').strip()
            g = APPLE_GEN_SCORE.get(gen, 220)
            tm = APPLE_TIER_MULT.get(tier, 1.0)
            score = round(g * tm)

    # ── Qualcomm Snapdragon ───────────────────────────────────────────────
    if score is None and 'SNAPDRAGON' in t:
        xm = re.search(r'SNAPDRAGON\s+X\s+(ELITE|PLUS)', t)
        if xm:
            score = SNAPDRAGON_SCORE.get('X_' + xm.group(1), 240)
        else:
            cxm = re.search(r'SNAPDRAGON\s+(8CX|7C\+?)\s*(?:GEN\s*(\d))?', t)
            if cxm:
                base  = cxm.group(1).replace('+', '_PLUS')
                gen_s = ('_GEN' + cxm.group(2)) if cxm.group(2) else ''
                score = SNAPDRAGON_SCORE.get(base + gen_s, 60)

    # ── Fallback ─────────────────────────────────────────────────────────
    if score is None:
        score = 100

    # ── Human-readable label ──────────────────────────────────────────────
    if score > 105:
        label = f"~{score/100:.1f}x Stronger than Baseline"
    elif score < 95:
        pct = round(100 - score)
        label = f"~{pct}% Weaker than Baseline"
    else:
        label = "Similar to Baseline"

    return score, label


def _get_gpu_name() -> str:
    """Try to detect GPU name. Uses GPUtil first, then WMI fallback."""
    # Try GPUtil - global monkey-patch in main.py suppresses CMD window
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            return gpus[0].name
    except Exception:
        pass

    # Fallback: WMI via subprocess
    if platform.system() == "Windows":
        try:
            import subprocess
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip() and l.strip() != "Name"]
            if lines:
                return lines[0]
        except Exception:
            pass

    return "Unknown GPU"


def _cpu_tier(score: int) -> str:
    """Map perf_score to Approved / Not Approved for the dashboard."""
    from thresholds import CPU_PERF_SCORE_MIN
    if score >= CPU_PERF_SCORE_MIN:
        return "Approved"
    return "Not Approved"


def get_system_specs() -> dict:
    """Return CPU, RAM, and GPU info."""
    # CPU
    cpu_model     = _get_cpu_model_fast()
    perf_score, perf_label = get_cpu_performance(cpu_model)
    
    physical_cores = psutil.cpu_count(logical=False) or "?"
    logical_cores  = psutil.cpu_count(logical=True)  or "?"

    cpu_freq   = psutil.cpu_freq()
    base_clock = f"{cpu_freq.current / 1000:.2f} GHz" if cpu_freq else "N/A"

    # RAM
    total_physical_bytes = 0
    if platform.system() == "Windows":
        try:
            import subprocess
            result = subprocess.run(
                ["wmic", "memorychip", "get", "capacity"],
                capture_output=True, text=True, timeout=2,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in result.stdout.strip().splitlines():
                if line.strip() and line.strip().isdigit():
                    total_physical_bytes += int(line.strip())
        except Exception:
            pass
            
    mem = psutil.virtual_memory()
    
    if total_physical_bytes > 0:
        # Use exact physical RAM from motherboard instead of OS usable RAM
        total_ram_gb = total_physical_bytes / (1024**3)
        total_ram = f"{round(total_ram_gb)} GB"
    else:
        # Fallback to psutil (reports slightly less due to hardware reserved)
        total_ram_gb = mem.total / (1024**3)
        total_ram = f"{round(total_ram_gb)} GB"
        
    available_ram = f"{mem.available / (1024**3):.2f} GB"
    ram_usage     = f"{mem.percent}%"

    # GPU
    gpu_name = _get_gpu_name()

    return {
        "cpu_model":      cpu_model,
        "perf_score":     perf_score,
        "perf_label":     perf_label,
        "cpu_score":      perf_score,
        "cpu_label":      _cpu_tier(perf_score),
        "physical_cores": physical_cores,
        "logical_cores":  logical_cores,
        "base_clock":     base_clock,
        "total_ram":      total_ram,
        "available_ram":  available_ram,
        "ram_usage":      ram_usage,
        "gpu_name":       gpu_name,
    }
