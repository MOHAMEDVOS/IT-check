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
        1000: 55, 2000: 72, 3000: 105, 4000: 140, 5000: 230,
        6000: 248, 7000: 320, 8000: 338, 9000: 360,
    }
    RYZEN_TIER_MULT  = {3: 0.76, 5: 1.0, 7: 1.22, 9: 1.55}
    RYZEN_SUFFIX_MULT = {
        'U': 1.90, 'HS': 1.45, 'H': 1.4, 'HX': 1.5,
        'G': 1.3, 'GE': 1.25, 'X': 1.2, 'X3D': 1.25, 'XS': 1.15, '': 1.0,
    }
    TR_SERIES_SCORE = {1000: 200, 2000: 260, 3000: 350, 5000: 450, 7000: 550}
    FX_CORE_SCORE   = {4: 50, 6: 62, 8: 75, 9: 82}
    PHENOM_SCORE = {
        'II_X6': 40, 'II_X4': 33, 'II_X3': 25, 'II_X2': 20,
        'I_X4': 18, 'I_X3': 15, 'I_X2': 12
    }
    AMD_APU_SCORE = {'E': 8, 'E1': 12, 'E2': 18, 'A4': 18, 'A6': 26, 'A8': 40, 'A10': 55, 'A12': 62}

    APPLE_GEN_SCORE = {1: 260, 2: 320, 3: 375, 4: 420, 5: 480}
    APPLE_TIER_MULT = {'BASE': 1.0, 'PRO': 1.25, 'MAX': 1.55, 'ULTRA': 2.0}

    SNAPDRAGON_SCORE = {
        'X_ELITE': 310, 'X_PLUS': 240,
        '8CX_GEN3': 130, '8CX_GEN2': 100, '8CX': 85,
        '7C_PLUS_GEN3': 75, '7C_PLUS': 55, '7C': 45,
    }

    def infer_intel_gen_from_model(num_str: str):
        if not num_str:
            return None
        if len(num_str) == 3:
            return 1  # i5-650 class
        if len(num_str) == 4:
            return int(num_str[0])
        if len(num_str) == 5:
            two = int(num_str[:2])
            if 10 <= two <= 14:
                return two
            # OCR can yield malformed 19xxx / 18xxx for 10xxx+ parts.
            if 15 <= two <= 20:
                return 10
            return int(num_str[0])
        return None

    def get_xeon_w_score(n: int):
        if 3500 <= n < 3700:
            if n < 3530:
                return 38
            if n < 3550:
                return 42
            if n < 3570:
                return 46
            if n < 3600:
                return 49
            if n < 3670:
                return 53
            return 61
        if 5580 <= n <= 5599:
            return 55
        if 5500 <= n < 5580:
            return 51
        if 1200 <= n < 1400:
            return round(138 + ((n - 1200) * 20) / 200)
        if 1400 <= n < 2100:
            return round(158 + ((n - 1400) * 4) / 700)
        if 2100 <= n < 2700:
            return round(162 + ((n - 2100) * 20) / 600)
        if 2700 <= n < 3500:
            return round(182 + ((n - 2700) * 50) / 800)
        if 0 < n < 1200:
            return 78
        if 3700 <= n < 5500:
            return 118
        if 7000 <= n < 9200:
            return 162
        return XEON_TIER_SCORE.get('W', 180)

    def get_xeon_nonw_score(tier: str, n: int):
        s = XEON_TIER_SCORE.get(tier, 130)
        if tier == 'E3':
            if n < 1230:
                s -= 20
            elif n >= 1580:
                s += 12
            elif n >= 1285:
                s += 6
        elif tier == 'E5':
            if n < 2400:
                s -= 24
            elif n < 2600:
                s -= 15
            elif 2600 <= n <= 2630:
                s -= 35
            elif n >= 2690:
                s += 14
            elif n >= 2660:
                s += 6
        elif tier == 'E7':
            if n < 4850:
                s -= 18
            elif n >= 8890:
                s += 22
        elif tier == 'D':
            if n < 1530:
                s -= 12
        return max(26, min(295, round(s)))

    def ryzen_sku_offset(series: int, tier: int, mod: int, suffix: str):
        off = 0
        s3d = suffix == 'X3D'
        if series == 1000:
            off -= 6
            if mod >= 900:
                off += 8
            elif mod < 250:
                off -= 6
        elif series == 2000:
            if suffix == 'U':
                if mod < 260:
                    off -= 3
                elif mod < 340:
                    off += 0
                elif mod < 440:
                    off += 4
                elif mod < 540:
                    off += 8
                elif mod < 620:
                    off += 6
                elif mod < 720:
                    off += 12
            else:
                if mod < 520:
                    off -= 14
                elif mod < 620:
                    off -= 8
            if mod >= 950:
                off += 10
            elif mod >= 900:
                off += 5
        elif series == 3000:
            if mod >= 980:
                off += 16
            elif mod >= 950:
                off += 12
            elif mod >= 900:
                off += 7
            elif mod < 420 and tier <= 5:
                off -= 10
            elif mod < 320 and tier == 3:
                off -= 6
        elif series == 4000:
            if mod >= 980:
                off += 14
            elif mod >= 900:
                off += 8
            elif mod < 430:
                off -= 8
        elif series == 5000:
            if mod >= 990:
                off += 22
            elif mod >= 950:
                off += 15
            elif mod >= 900:
                off += 9
            elif mod < 500 and tier <= 5:
                off -= 10
            elif mod < 620 and tier == 5:
                off -= 4
        elif series == 6000:
            if mod >= 980:
                off += 18
            elif mod >= 950:
                off += 12
            elif mod < 430:
                off -= 10
        elif series in (7000, 8000, 9000):
            if mod >= 990:
                off += 24
            elif mod >= 950:
                off += 16
            elif mod >= 900:
                off += 10
            elif mod < 380:
                off -= 10
        elif series >= 10000:
            off += min(40, ((series - 10000) // 1000) * 8)
        if s3d and series >= 5000:
            off += 10
        return off

    def get_ryzen_score(tier: int, series_base: int, model_num: int, suffix: str):
        s0 = RYZEN_SER_SCORE.get(series_base)
        if s0 is None and model_num:
            k = (model_num // 1000) * 1000
            s0 = RYZEN_SER_SCORE.get(k, min(380, 90 + (model_num // 800)))
        if s0 is None:
            s0 = 100
        t_mult = RYZEN_TIER_MULT.get(tier, 1.0)
        s_mult = RYZEN_SUFFIX_MULT.get(suffix, 1.0)
        s = s0 + ryzen_sku_offset(series_base, tier, model_num % 1000, suffix)
        return max(22, round(s * t_mult * s_mult))

    def get_threadripper_score(model_num: int, series_base: int, is_pro: bool):
        base0 = TR_SERIES_SCORE.get(series_base, 300)
        base = round(base0 * 1.15) if is_pro else base0
        mod = model_num % 1000
        off = 0
        if series_base == 1000:
            if mod >= 900:
                off += 22
            elif mod < 200:
                off -= 28
        elif series_base == 2000:
            if mod >= 960:
                off += 30
            elif mod < 380:
                off -= 20
        elif series_base == 3000:
            if mod >= 900:
                off += 36
            elif mod < 280:
                off -= 26
        elif series_base >= 5000:
            if mod >= 980:
                off += 42
            elif mod >= 900:
                off += 30
            elif mod < 360:
                off -= 28
        return max(105, round(base + off))

    def get_fx_score(model_num: str):
        b = FX_CORE_SCORE.get(int(model_num[0]), 60)
        tail = int(re.sub(r'\D', '', model_num)[1:])
        off = 0
        if tail < 320:
            off -= 14
        elif tail >= 750:
            off += 10
        elif tail >= 520:
            off += 5
        return max(26, round(b + off))

    def get_phenom_score(gen_tag: str, cores_tag: str, model_num: int):
        s = PHENOM_SCORE.get(f"{gen_tag}_{cores_tag}", 20)
        if model_num >= 1100:
            s += 10
        elif model_num >= 950:
            s += 5
        elif model_num < 750:
            s -= 6
        return max(10, round(s))

    def get_sempron_score(model_num: int):
        if model_num >= 3600:
            return 26
        if model_num >= 3000:
            return 20
        if model_num >= 2500:
            return 15
        return 10

    def get_amd_legacy_apu_score(series_tag: str, model_num: int):
        b = AMD_APU_SCORE.get(series_tag, 25)
        off = 0
        if model_num >= 9800:
            off += 14
        elif model_num >= 9500:
            off += 10
        elif model_num >= 9000:
            off += 6
        elif model_num < 6200:
            off -= 10
        elif model_num < 7200:
            off -= 4
        return max(12, round(b + off))

    def get_athlon_score(family: str, model_num: int = 0, cores: str = '', dual: bool = False):
        if family == 'athlon_modern':
            if model_num >= 3200:
                return 50
            if model_num >= 3000:
                return 46
            if model_num >= 2450:
                return 41
            if model_num >= 200:
                return 35
            return 28
        if family == 'athlon_ii':
            s = {'X4': 22, 'X3': 18, 'X2': 16}.get(cores, 18)
            if model_num >= 660:
                s += 6
            elif model_num >= 640:
                s += 4
            elif model_num < 220:
                s -= 5
            return max(10, round(s))
        if family == 'athlon_64':
            return 14 if dual else 10
        if family == 'athlon_classic':
            return 12 if model_num >= 4000 else 8
        return 15

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

            # Model number → gen  (supports 3/4/5 digit OCR/model variants)
            mod_m = re.search(r'I[3579][-\s]?(\d{3,5})([A-Z]{0,3})?', t)
            if mod_m:
                num_str = mod_m.group(1)
                suffix  = (mod_m.group(2) or '').strip()
                gen = infer_intel_gen_from_model(num_str)

            # Explicit "Nth Gen" beats model-number detection
            exp_m = re.search(r'(?:(\d{1,2})(?:ST|ND|RD|TH)\s*GEN|GEN\s*(\d{1,2}))', t)
            if exp_m:
                eg = int(exp_m.group(1) or exp_m.group(2))
                if 1 <= eg <= 14:
                    gen = eg

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
        m = re.search(r'XEON\s+(?:CPU\s+|PROCESSOR\s+)*(E3|E5|E7|D|W|GOLD|PLATINUM|SILVER|BRONZE)[-\s]?(\d{4,5})', t)
        if m:
            tier = m.group(1)
            num = int(m.group(2))
            if tier == 'W':
                score = get_xeon_w_score(num)
            elif tier in ('E3', 'E5', 'E7', 'D'):
                score = get_xeon_nonw_score(tier, num)
            else:
                score = XEON_TIER_SCORE.get(tier, 130)
        else:
            m2 = re.search(r'XEON\s+(?:CPU\s+|PROCESSOR\s+)*(W|E3|E5|E7|D)(\d{4,5})', t)
            if m2:
                tier = m2.group(1)
                num = int(m2.group(2))
                if tier == 'W':
                    score = get_xeon_w_score(num)
                else:
                    score = get_xeon_nonw_score(tier, num)
            else:
                m3 = re.search(r'XEON\s+(?:CPU\s+|PROCESSOR\s+)*(\d{4,5})', t)
                if m3:
                    score = get_xeon_nonw_score('E3', int(m3.group(1)))
        if score is None and 'XEON' in t:
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
            model_num  = int(m.group(2))
            suffix     = (m.group(3) or '').strip()
            series_base = (model_num // 1000) * 1000
            score = get_ryzen_score(tier, series_base, model_num, suffix)

    # ── AMD Threadripper ─────────────────────────────────────────────────
    if score is None:
        m = re.search(r'THREADRIPPER\s+(?:PRO\s+)?(\d{4})', t)
        if m:
            model_num  = int(m.group(1))
            series_base = (model_num // 1000) * 1000
            is_pro = 'THREADRIPPER PRO' in t
            score = get_threadripper_score(model_num, series_base, is_pro)

    # ── AMD FX ───────────────────────────────────────────────────────────
    if score is None:
        m = re.search(r'\bFX[-\s](\d{4})', t)
        if m:
            score = get_fx_score(m.group(1))

    # ── AMD Phenom / Phenom II ─────────────────────────────────────────
    if score is None:
        m = re.search(r'PHENOM\s*(II)?\s*(X[2346])\s+(\d{3,4})', t)
        if m:
            gen_tag = 'II' if m.group(1) else 'I'
            cores = m.group(2)
            model_num = int(m.group(3))
            score = get_phenom_score(gen_tag, cores, model_num)

    # ── AMD Athlon ─────────────────────────────────────────────────────
    if score is None:
        m_modern = re.search(r'ATHLON\s+(?:(?:GOLD|SILVER)\s+)?(\d{3,4})([A-Z]{0,3})?', t)
        if m_modern:
            score = get_athlon_score('athlon_modern', model_num=int(m_modern.group(1)))
        else:
            m_ii = re.search(r'ATHLON\s+II\s+(X[234])\s+(\d{3,4})', t)
            if m_ii:
                score = get_athlon_score('athlon_ii', model_num=int(m_ii.group(2)), cores=m_ii.group(1))
            else:
                m_64 = re.search(r'ATHLON\s+64\s*(X2)?\s*(\d{3,4})', t)
                if m_64:
                    score = get_athlon_score('athlon_64', model_num=int(m_64.group(2)), dual=bool(m_64.group(1)))
                else:
                    m_plain = re.search(r'ATHLON\s+(\d{4})\+?', t)
                    if m_plain:
                        score = get_athlon_score('athlon_classic', model_num=int(m_plain.group(1)))

    # ── AMD Sempron ────────────────────────────────────────────────────
    if score is None:
        m = re.search(r'SEMPRON\s+(\d{3,4})', t)
        if m:
            score = get_sempron_score(int(m.group(1)))

    # ── AMD Turion ─────────────────────────────────────────────────────
    if score is None:
        m = re.search(r'TURION\s+(?:(64\s*X2|X2|64|NEO)\s+)?', t)
        if m:
            typ = (m.group(1) or 'STANDARD').replace(' ', '_').upper()
            turion_scores = {'64_X2': 15, 'X2': 15, '64': 10, 'NEO': 8, 'STANDARD': 12}
            score = turion_scores.get(typ, 12)

    # ── AMD Legacy APU (A4/A6/A8/A10/A12, E/E1/E2) ───────────────────
    if score is None:
        m = re.search(r'\b(E2|E1|E|A(?:4|6|8|10|12))(?:\s+PRO)?[-\s](\d{4,5})', t)
        if m:
            score = get_amd_legacy_apu_score(m.group(1), int(m.group(2)))

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
