import psutil
import platform
import threading


def _get_cpu_model_fast() -> str:
    """
    Get CPU model name quickly.
    cpuinfo.get_cpu_info() can take 5-10s or hang on some systems.
    We run it in a thread with a 4s timeout — if it times out,
    fall back to Windows Registry or platform.processor().
    """
    result = {"model": None}

    def _try_cpuinfo():
        try:
            import cpuinfo
            info = cpuinfo.get_cpu_info()
            name = info.get("brand_raw", "")
            if name:
                result["model"] = name
        except Exception:
            pass

    t = threading.Thread(target=_try_cpuinfo, daemon=True)
    t.start()
    t.join(timeout=4)   # give cpuinfo 4 seconds max

    if result["model"]:
        return result["model"].strip()

    # Fallback 1: Registry on Windows — Very reliable friendly name
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            )
            name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            if name:
                return name.strip()
        except Exception:
            pass

    # Fallback 2: platform.processor() — last resort
    proc = platform.processor()
    if proc:
        return proc

    return "Unknown CPU"


def get_cpu_performance(model_name: str) -> tuple:
    """
    Heuristic scoring against an Intel i5 6th Gen baseline (Score 100).
    Returns (score, label).
    """
    name = model_name.lower()
    score = 100
    label = "Baseline Performance"

    # Apple Silicon
    if "apple" in name or "m1" in name or "m2" in name or "m3" in name or "m4" in name:
        if "ultra" in name: score = 450
        elif "max" in name: score = 350
        elif "pro" in name: score = 280
        elif "m4" in name: score = 320
        elif "m3" in name: score = 300
        elif "m2" in name: score = 280
        else: score = 250
        label = f"~{score/100:.1f}x Stronger than Baseline"
        return score, label

    # AMD A-Series / Older APUs
    if any(x in name for x in ["a4-", "a6-", "a8-", "a10-", "e2-"]):
        score = 45
        label = "~55% Weaker than Baseline"
        return score, label

    # Intel Low-End
    if any(x in name for x in ["celeron", "pentium", "atom"]):
        score = 40
        label = "~60% Weaker than Baseline"
        return score, label

    # Ryzen
    if "ryzen" in name:
        if "9 " in name: score = 300
        elif "7 " in name: score = 220
        elif "5 " in name: score = 180
        else: score = 130
        
        # Generation boost
        if "5000" in name or "6000" in name or "7000" in name or "8000" in name or "9000" in name:
            score = int(score * 1.3)
        
        label = f"~{score/100:.1f}x Stronger than Baseline"
        return score, label

    # Intel Core Series
    import re

    # First: try to extract generation from explicit "Nth Gen" in the name
    # e.g. "12th Gen Intel(R) Core(TM) i7-1255U" → gen 12
    gen_explicit = re.search(r'(\d{1,2})(?:th|st|nd|rd)\s*gen', name)

    # Also find the family (i3/i5/i7/i9)
    family_match = re.search(r'i([3579])', name)
    if family_match:
        family_num = int(family_match.group(1))
        family = {3: 70, 5: 100, 7: 140, 9: 200}.get(family_num, 100)

        if gen_explicit:
            gen = int(gen_explicit.group(1))
        else:
            # Fallback: parse from model number (e.g. i5-6500 → gen 6)
            model_match = re.search(r'i[3579]-(\d{4,5})', name)
            if model_match:
                model_num = model_match.group(1)
                if len(model_num) == 5:
                    gen = int(model_num[:2])
                else:
                    gen = int(model_num[0])
            else:
                gen = 6  # default to baseline



        
        # Mult for generation (Baseline is Gen 6)
        # Gen 6 = 1.0, Gen 12 = ~1.8
        gen_mult = 1.0 + (gen - 6) * 0.12
        gen_mult = max(gen_mult, 0.5)  # Floor to avoid negative scores
        score = int(family * gen_mult)
        
        if score > 105:
            label = f"~{score/100:.1f}x Stronger than Baseline"
        elif score < 95:
            label = f"~{100-score}% Weaker than Baseline"
        else:
            label = "Similar to Baseline"
        return score, label

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
