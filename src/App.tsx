import React from "react";
import { Download, ShieldCheck, Gauge, Cpu, CheckCircle2 } from "lucide-react";
import { Reveal } from "./components/Reveal";

const ANIMATE_EVEN_IF_REDUCE_MOTION = true;
const DOWNLOAD_URL = "/downloads/vos.exe";

const features = [
  {
    icon: ShieldCheck,
    title: "Smart health checks",
    description:
      "Instant scan of CPU, RAM, storage, key Windows settings, and device readiness."
  },
  {
    icon: Gauge,
    title: "Performance insights",
    description: "See what slows your PC down and get clear suggestions to fix it."
  },
  {
    icon: Cpu,
    title: "Lightweight & fast",
    description: "No bloat, no ads – just a tiny tool that runs in seconds."
  }
];

const steps = [
  "Download VOS for Windows.",
  "Run the tool (no install needed).",
  "Read the simple report and follow the tips."
];

const checks = [
  { title: "Computer", description: "CPU, RAM, OS version, and key system settings." },
  { title: "Disk space", description: "System drive usage and available free space." },
  { title: "Browser status", description: "Detect common browser readiness for work calls." },
  { title: "Connection stability", description: "Basic stability signals to spot drops or jitter." },
  { title: "Microphone levels", description: "Confirm input activity and level response." },
  { title: "Connection type", description: "Wi‑Fi or Ethernet, so you know what to optimize." }
];

const faqs = [
  { q: "Is VOS safe to run?", a: "Yes. VOS reads system information and shows a report — it doesn’t change settings without you." },
  { q: "Windows says \"unknown publisher\" or \"Windows protected your PC\" — what do I do?", a: "VOS is not code-signed. Click More info, then Run anyway. The app is safe; the warning appears because it's from an unsigned developer." },
  { q: "Do I need to install it?", a: "No. VOS is portable — download and run." },
  { q: "Does it work offline?", a: "Most checks work offline. Connection checks need a network to measure stability." }
];

function App() {
  const [scrollProgress, setScrollProgress] = React.useState(0);

  React.useEffect(() => {
    const root = document.documentElement;
    if (ANIMATE_EVEN_IF_REDUCE_MOTION) root.classList.add("force-motion");
    else root.classList.remove("force-motion");
  }, []);

  React.useEffect(() => {
    const onScroll = () => {
      const winScroll = document.documentElement.scrollTop;
      const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      setScrollProgress(height > 0 ? (winScroll / height) * 100 : 0);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 font-sans overflow-x-hidden">
      {/* Scroll progress bar */}
      <div
        className="fixed left-0 top-0 z-50 h-0.5 bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-150 ease-out"
        style={{ width: `${scrollProgress}%` }}
        aria-hidden
      />
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,_#1d4ed833,_transparent_50%),radial-gradient(ellipse_60%_80%_at_80%_50%,_#1e40af22,_transparent_45%),radial-gradient(ellipse_60%_80%_at_20%_80%,_#0e749022,_transparent_45%)] bg-gradient-tech" />
      <div className="absolute inset-0 -z-10 bg-grid-tech" />
      <div className="pointer-events-none fixed inset-0 z-0 h-px w-full bg-gradient-to-b from-transparent via-blue-500/10 to-transparent opacity-30 animate-scan-line" aria-hidden />

      <header className="border-b border-slate-800/70 bg-slate-950/70 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 md:max-w-[1400px] md:px-8 md:py-5 xl:max-w-[1600px] xl:px-10">
            <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500 shadow-glow transition-transform duration-300 hover:scale-105">
              <span className="text-[11px] font-extrabold tracking-wide text-slate-950">VOS</span>
            </div>
            <span className="text-sm font-semibold tracking-tight text-slate-100 md:text-base">
              VOS
            </span>
          </div>
          <a
            href="#download"
            className="hidden rounded-full border border-blue-500/50 bg-blue-500/10 px-4 py-1.5 text-xs font-medium text-blue-200 shadow-sm transition-all duration-300 hover:border-blue-400/60 hover:bg-blue-500/20 hover:shadow-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 md:inline-block"
          >
            Download tool
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-5 pb-20 pt-6 md:max-w-[1400px] md:px-8 md:pt-10 xl:max-w-[1600px] xl:px-10">
        {/* Hero – main focus */}
        <section className="relative mb-4 md:mb-6">
          <div className="pointer-events-none absolute -inset-4 -z-10 rounded-[40px] bg-gradient-to-b from-blue-500/10 via-transparent to-transparent md:-inset-8" />
          <Reveal
            tier="primary"
            liftPx={24}
            scale={0.98}
            durationMs={1200}
            respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
          >
            <div className="relative overflow-hidden rounded-[28px] border border-white/15 bg-white/[0.04] shadow-[0_0_0_1px_rgba(255,255,255,0.06),0_32px_80px_rgba(0,0,0,0.5),0_0_80px_rgba(59,130,246,0.12)] backdrop-blur-2xl transition-all duration-500 hover:border-blue-500/30 hover:shadow-[0_0_0_1px_rgba(255,255,255,0.08),0_32px_80px_rgba(0,0,0,0.5),0_0_100px_rgba(59,130,246,0.18)]">
              <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(160deg,_rgba(255,255,255,0.09)_0%,_rgba(255,255,255,0.02)_40%,_rgba(59,130,246,0.06)_70%,_transparent_100%)]" />
              <div className="pointer-events-none absolute inset-0 rounded-[28px] ring-1 ring-inset ring-white/10" />
              <div className="pointer-events-none absolute -left-40 -top-20 h-80 w-80 rounded-full bg-blue-500/15 blur-3xl animate-float" />
              <div className="pointer-events-none absolute -right-24 -bottom-16 h-72 w-72 rounded-full bg-cyan-500/12 blur-3xl animate-float" style={{ animationDelay: "1.5s" }} />
              <div className="pointer-events-none absolute bottom-0 left-1/2 h-48 w-96 -translate-x-1/2 rounded-full bg-blue-500/10 blur-3xl" />

              <div className="relative grid items-center gap-12 px-6 py-10 md:grid-cols-[1.05fr_1fr] md:gap-14 md:px-12 md:py-14 lg:px-14 lg:py-16 xl:gap-16 xl:px-16">
                <div className="relative">
                  <div className="pointer-events-none absolute -left-12 -top-12 hidden h-32 w-32 rounded-3xl border border-blue-500/20 bg-blue-500/5 blur-2xl md:block" />
                <Reveal
                  tier="secondary"
                  delayMs={80}
                  durationMs={900}
                  liftPx={12}
                  respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
                >
                  <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/35 bg-blue-950/70 px-3.5 py-1.5 text-[11px] font-medium text-blue-200 shadow-sm">
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-400 shadow-[0_0_12px_#3b82f6] animate-glow-pulse" />
                    Runs on Windows · No bloat
                  </div>
                </Reveal>

                <Reveal
                  tier="primary"
                  delayMs={140}
                  durationMs={1200}
                  liftPx={32}
                  scale={0.98}
                  respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
                >
                  <h1 className="mt-5 text-4xl font-bold tracking-tight text-slate-50 sm:text-5xl md:text-[3.25rem] md:leading-[1.15] lg:text-[3.5rem]">
                    Check your PC&apos;s health
                    <span className="mt-2 block bg-[linear-gradient(90deg,_#93c5fd,_#c7d2fe,_#f0f9ff,_#c7d2fe,_#93c5fd)] bg-clip-text text-transparent bg-[length:300%_auto] text-shimmer">
                      in 1 minute.
                    </span>
                  </h1>
                </Reveal>

                <Reveal
                  tier="secondary"
                  delayMs={240}
                  durationMs={900}
                  liftPx={14}
                  respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
                >
                  <p className="mt-5 max-w-lg text-base leading-relaxed text-slate-300/95 md:text-[1.0625rem]">
                    VOS (Vital Operations Scanner) is a tiny Windows tool that runs a quick health
                    check on your computer – performance, storage, and key settings – and gives you a
                    clean, readable report you can act on instantly.
                  </p>
                </Reveal>

                <Reveal
                  tier="primary"
                  delayMs={320}
                  durationMs={1050}
                  liftPx={22}
                  respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
                >
                  <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center">
                    <a
                      id="download"
                      href={DOWNLOAD_URL}
                      download
                      className="inline-flex w-full items-center justify-center gap-2.5 rounded-full bg-blue-500 px-6 py-3.5 text-base font-semibold text-slate-50 shadow-[0_0_30px_rgba(59,130,246,0.45)] transition-all duration-300 hover:scale-[1.03] hover:bg-blue-400 hover:shadow-[0_0_50px_rgba(59,130,246,0.5)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 sm:w-auto animate-cta-glow"
                    >
                      <Download className="h-5 w-5" />
                      Download VOS
                    </a>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                      <span className="font-medium text-slate-400">Simple. Fast. No fluff.</span>
                      <span className="text-slate-500">Windows 10 & 11 · Free</span>
                    </div>
                  </div>
                  <p className="mt-3 text-xs text-slate-500">
                    If Windows shows a warning: click <strong className="text-slate-400">More info</strong> → <strong className="text-slate-400">Run anyway</strong>.
                  </p>
                </Reveal>

                <Reveal
                  tier="secondary"
                  delayMs={420}
                  durationMs={900}
                  liftPx={12}
                  respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
                >
                  <div className="mt-6 grid gap-3 text-xs text-slate-400 sm:grid-cols-2 lg:grid-cols-3">
                    <div className="flex w-full items-center gap-1.5 rounded-full bg-slate-900/80 px-3 py-1">
                      <CheckCircle2 className="h-3.5 w-3.5 text-blue-400" />
                      Portable .exe – no install
                    </div>
                    <div className="flex w-full items-center gap-1.5 rounded-full bg-slate-900/80 px-3 py-1">
                      <CheckCircle2 className="h-3.5 w-3.5 text-blue-400" />
                      Clean, readable health report
                    </div>
                    <div className="flex w-full items-center gap-1.5 rounded-full bg-slate-900/80 px-3 py-1">
                      <CheckCircle2 className="h-3.5 w-3.5 text-blue-400" />
                      Connection stability check
                    </div>
                    <div className="flex w-full items-center gap-1.5 rounded-full bg-slate-900/80 px-3 py-1">
                      <CheckCircle2 className="h-3.5 w-3.5 text-blue-400" />
                      Microphone levels
                    </div>
                    <div className="flex w-full items-center gap-1.5 rounded-full bg-slate-900/80 px-3 py-1">
                      <CheckCircle2 className="h-3.5 w-3.5 text-blue-400" />
                      Connection type (Wi‑Fi/Ethernet)
                    </div>
                  </div>
                </Reveal>
              </div>

              <Reveal
                tier="primary"
                delayMs={220}
                durationMs={1150}
                liftPx={26}
                slideX={20}
                scale={0.97}
                className="relative"
                respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
              >
                <div className="pointer-events-none absolute -inset-6 -z-10 rounded-[32px] bg-gradient-to-b from-blue-500/15 via-blue-500/5 to-transparent blur-3xl" />
                <div className="relative overflow-hidden rounded-3xl border border-blue-500/35 bg-slate-900/85 p-4 shadow-[0_25px_60px_rgba(0,0,0,0.4),0_0_40px_rgba(59,130,246,0.15)]">
                  <div className="flex items-center justify-between rounded-2xl bg-slate-900/90 px-3 py-2">
                    <div className="flex gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-red-500/80" />
                      <span className="h-2 w-2 rounded-full bg-amber-400/80" />
                      <span className="h-2 w-2 rounded-full bg-blue-500/80" />
                    </div>
                    <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] text-slate-300">
                      VOS · Report
                    </span>
                  </div>

                  <div className="mt-4 grid gap-4 rounded-2xl bg-slate-900/90 p-4 text-xs text-slate-100">
                    <div className="flex items-center justify-between rounded-xl border border-blue-500/40 bg-gradient-to-r from-blue-500/20 to-blue-500/5 px-3 py-2">
                      <div>
                        <div className="text-[11px] text-blue-300/90">Overall health</div>
                        <div className="text-lg font-semibold text-blue-400">Good</div>
                      </div>
                      <div className="h-12 w-12 rounded-full border border-blue-500/70 bg-slate-950/70 shadow-[0_0_30px_rgba(59,130,246,0.7)] animate-glow-pulse" />
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-3 transition-colors duration-200 hover:border-blue-500/60">
                        <div className="text-[11px] text-slate-400">CPU usage</div>
                        <div className="mt-1 text-base font-semibold">18%</div>
                        <div className="mt-0.5 h-1 rounded-full bg-slate-800">
                          <div className="h-1 w-2/5 rounded-full bg-blue-500" />
                        </div>
                      </div>
                      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-3 transition-colors duration-200 hover:border-blue-500/60">
                        <div className="text-[11px] text-slate-400">Memory</div>
                        <div className="mt-1 text-base font-semibold">42%</div>
                        <div className="mt-0.5 h-1 rounded-full bg-slate-800">
                          <div className="h-1 w-3/5 rounded-full bg-blue-400" />
                        </div>
                      </div>
                      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-3 transition-colors duration-200 hover:border-amber-400/70">
                        <div className="text-[11px] text-slate-400">Storage</div>
                        <div className="mt-1 text-base font-semibold">71%</div>
                        <div className="mt-0.5 h-1 rounded-full bg-slate-800">
                          <div className="h-1 w-4/5 rounded-full bg-amber-400" />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-1.5 rounded-xl border border-slate-800 bg-slate-900/90 p-3">
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span>Quick recommendations</span>
                        <span className="text-blue-300">3 passed · 1 warning</span>
                      </div>
                      <ul className="space-y-1.5 text-[11px]">
                        <li className="flex items-center gap-1.5 text-blue-300">
                          <CheckCircle2 className="h-3 w-3" />
                          Startup apps look good.
                        </li>
                        <li className="flex items-center gap-1.5 text-blue-300">
                          <CheckCircle2 className="h-3 w-3" />
                          Windows updates are up to date.
                        </li>
                        <li className="flex items-center gap-1.5 text-amber-300">
                          <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                          Storage above 70% – consider cleaning up large files.
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </Reveal>
            </div>
            </div>
          </Reveal>
        </section>

        {/* Features */}
        <section className="mt-16 -mx-5 border-y border-slate-800/70 py-10 md:-mx-8 md:mt-20 md:py-12 xl:-mx-10">
          <div className="mx-auto grid max-w-7xl gap-8 px-5 md:max-w-[1400px] md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] md:items-center md:px-8 xl:max-w-[1600px] xl:px-10">
            <Reveal respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}>
              <div>
              <h2 className="text-xl font-semibold tracking-tight text-slate-50 md:text-2xl">
                Everything you need to quickly understand your PC.
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-slate-300/90 md:text-[15px]">
                Whether you&apos;re troubleshooting your own machine or helping someone remotely,
                VOS runs the same core checks every time and gives you a clean summary you can
                trust.
              </p>

              <div className="mt-6 grid gap-4 md:grid-cols-3">
                {features.map((feature, idx) => (
                  <Reveal
                    key={feature.title}
                    delayMs={idx * 90}
                    lift
                    respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
                  >
                    <div className="group rounded-2xl border border-slate-800 bg-slate-900/80 p-4 transition-all duration-300 hover:-translate-y-1 hover:border-blue-500/30 hover:shadow-lg hover:shadow-blue-500/5">
                      <div className="inline-flex rounded-full bg-slate-900/90 p-2 text-blue-400 transition-transform duration-300 group-hover:scale-110">
                        <feature.icon className="h-4 w-4" />
                      </div>
                      <h3 className="mt-3 text-sm font-semibold text-slate-50">
                        {feature.title}
                      </h3>
                      <p className="mt-2 text-xs leading-relaxed text-slate-400">
                        {feature.description}
                      </p>
                    </div>
                  </Reveal>
                ))}
              </div>
              </div>
            </Reveal>

            <Reveal delayMs={120} lift={false} slideX={15} scale={0.98} respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}>
              <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5 transition-all duration-300 hover:border-blue-500/25 hover:shadow-lg hover:shadow-blue-500/5">
              <h3 className="text-sm font-semibold text-slate-100">
                How it works
              </h3>
              <ol className="mt-3 space-y-2.5 text-xs text-slate-300">
                {steps.map((step, index) => (
                  <li key={step} className="flex gap-3">
                    <span className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full border border-slate-700 bg-slate-900 text-[11px] text-slate-200">
                      {index + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
              <a
                href={DOWNLOAD_URL}
                download
                className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-blue-500 px-4 py-2 text-xs font-semibold text-slate-50 shadow-glow transition-all duration-300 hover:bg-blue-400 hover:shadow-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
              >
                <Download className="h-3.5 w-3.5" />
                Download VOS
              </a>
              </div>
            </Reveal>
          </div>
        </section>

        {/* What VOS checks */}
        <section className="mt-16 md:mt-20">
          <Reveal tier="primary" respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}>
            <div className="rounded-[28px] border border-slate-800 bg-slate-950/40 p-6 backdrop-blur md:p-8">
              <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
                <div>
                  <h2 className="text-xl font-semibold tracking-tight text-slate-50 md:text-2xl">
                    What VOS checks
                  </h2>
                  <p className="mt-2 max-w-2xl text-sm text-slate-300/90">
                    A single scan gives you fast signals for remote work readiness — system health,
                    disk space, connection stability, and audio input.
                  </p>
                </div>
                <div className="text-xs text-slate-400">
                  Designed to match the in-app report layout.
                </div>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-3">
                {checks.map((c, idx) => (
                  <Reveal
                    key={c.title}
                    tier={idx < 3 ? "primary" : "secondary"}
                    delayMs={idx * 90}
                    durationMs={idx < 3 ? 1050 : 900}
                    liftPx={idx < 3 ? 22 : 14}
                    respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
                  >
                    <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-blue-500/25 hover:shadow-md hover:shadow-blue-500/5">
                      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.14),_transparent_55%)]" />
                      <div className="relative">
                        <div className="text-sm font-semibold text-slate-50">{c.title}</div>
                        <div className="mt-2 text-xs leading-relaxed text-slate-400">
                          {c.description}
                        </div>
                      </div>
                    </div>
                  </Reveal>
                ))}
              </div>
            </div>
          </Reveal>
        </section>

        {/* FAQ */}
        <section className="mt-16 md:mt-20">
          <Reveal tier="primary" respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}>
            <div className="rounded-[28px] border border-slate-800 bg-slate-900/40 p-6 backdrop-blur md:p-8">
              <h2 className="text-xl font-semibold tracking-tight text-slate-50 md:text-2xl">
                FAQ
              </h2>
              <div className="mt-6 grid gap-3">
                {faqs.map((f, idx) => (
                  <Reveal
                    key={f.q}
                    tier="secondary"
                    delayMs={idx * 90}
                    liftPx={14}
                    respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
                  >
                    <details className="group rounded-2xl border border-slate-800 bg-slate-900/70 px-4 py-3 transition-all duration-300 hover:border-slate-700 hover:bg-slate-900/80">
                      <summary className="cursor-pointer list-none text-sm font-semibold text-slate-100">
                        {f.q}
                      </summary>
                      <p className="mt-2 text-xs leading-relaxed text-slate-400">
                        {f.a}
                      </p>
                    </details>
                  </Reveal>
                ))}
              </div>
            </div>
          </Reveal>
        </section>

        {/* Final CTA */}
        <section className="mt-16 md:mt-20">
          <Reveal tier="primary" liftPx={28} durationMs={1200} respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}>
            <div className="relative overflow-hidden rounded-[32px] border border-blue-500/25 bg-white/[0.035] p-6 shadow-[0_30px_120px_rgba(15,23,42,0.9)] backdrop-blur-2xl transition-all duration-500 hover:border-blue-500/40 hover:shadow-[0_30px_120px_rgba(15,23,42,0.95),0_0_50px_rgba(59,130,246,0.12)] md:p-10">
              <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.18),_transparent_60%)]" />
              <div className="relative flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-2xl font-semibold tracking-tight text-slate-50">
                    Ready to run VOS?
                  </h2>
                  <p className="mt-2 max-w-xl text-sm text-slate-300/90">
                    Download the tool, run a scan, and get a clean report in seconds.
                  </p>
                </div>
                <a
                  href={DOWNLOAD_URL}
                  download
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-blue-500 px-5 py-2.5 text-sm font-semibold text-slate-50 shadow-glow shadow-blue-500/40 transition-all duration-300 hover:scale-105 hover:bg-blue-400 hover:shadow-glow-lg hover:shadow-blue-500/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 animate-cta-glow"
                >
                  <Download className="h-4 w-4" />
                  Download VOS
                </a>
              </div>
            </div>
          </Reveal>
        </section>

        {/* Footer */}
        <footer className="mt-10 flex flex-col gap-3 text-[11px] text-slate-500 md:mt-12 md:flex-row md:items-center md:justify-between">
          <p>© {new Date().getFullYear()} VOS. All rights reserved.</p>
        </footer>
      </main>
    </div>
  );
}

export default App;

