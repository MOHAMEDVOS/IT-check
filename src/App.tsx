import React from "react";
import { Download, ShieldCheck, Gauge, Cpu, CheckCircle2 } from "lucide-react";
import heroImage from "./assets/pc-glow.svg";
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
  React.useEffect(() => {
    const root = document.documentElement;
    if (ANIMATE_EVEN_IF_REDUCE_MOTION) root.classList.add("force-motion");
    else root.classList.remove("force-motion");
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 font-sans">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_#1d4ed822,_transparent_60%),radial-gradient(circle_at_bottom,_#1e40af22,_transparent_55%)]" />

      <header className="border-b border-slate-800/70 bg-slate-950/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 md:py-5">
            <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500 shadow-glow">
              <span className="text-[11px] font-extrabold tracking-wide text-slate-950">VOS</span>
            </div>
            <span className="text-sm font-semibold tracking-tight text-slate-100 md:text-base">
              VOS
            </span>
          </div>
          <a
            href="#download"
            className="hidden rounded-full border border-blue-500/50 bg-blue-500/10 px-4 py-1.5 text-xs font-medium text-blue-200 shadow-sm hover:bg-blue-500/20 md:inline-block"
          >
            Download tool
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 pb-20 pt-10 md:pt-16">
        {/* Hero */}
        <section className="mt-2">
          <Reveal
            tier="primary"
            liftPx={22}
            durationMs={1100}
            respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
          >
            <div className="relative overflow-hidden rounded-[32px] border border-white/10 bg-white/[0.035] shadow-[0_30px_120px_rgba(15,23,42,0.9)] backdrop-blur-2xl">
              <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(135deg,_rgba(255,255,255,0.08),_rgba(255,255,255,0.02)_35%,_rgba(59,130,246,0.05)_70%,_rgba(0,0,0,0)_100%)]" />
              <div className="pointer-events-none absolute inset-0 rounded-[32px] ring-1 ring-inset ring-blue-500/20" />
            <div className="pointer-events-none absolute -left-32 top-0 h-64 w-64 rounded-full bg-blue-500/10 blur-3xl" />
            <div className="pointer-events-none absolute -right-20 -bottom-10 h-64 w-64 rounded-full bg-cyan-500/10 blur-3xl" />

            <div className="relative grid items-center gap-10 px-5 py-8 md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] md:gap-12 md:px-10 md:py-10">
              <div className="relative">
                <div className="pointer-events-none absolute -left-10 -top-10 hidden h-28 w-28 rounded-3xl border border-blue-500/25 bg-blue-500/5 blur-xl md:block" />
                <Reveal
                  tier="secondary"
                  delayMs={80}
                  durationMs={900}
                  liftPx={12}
                  respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
                >
                  <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-950/60 px-3 py-1 text-[11px] text-blue-200 shadow-sm">
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-400 shadow-[0_0_12px_#3b82f6]" />
                    Runs on Windows · No bloat
                  </div>
                </Reveal>

                <Reveal
                  tier="primary"
                  delayMs={140}
                  durationMs={1150}
                  liftPx={30}
                  respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
                >
                  <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-50 sm:text-4xl md:text-[2.85rem]">
                    Check your PC&apos;s health
                    <span className="block bg-gradient-to-r from-blue-400 via-indigo-300 to-blue-400 bg-clip-text text-transparent">
                      in under 30 seconds.
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
                  <p className="mt-4 max-w-xl text-sm leading-relaxed text-slate-300/90 md:text-base">
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
                  <div className="mt-6 flex flex-wrap items-center gap-3">
                    <a
                      id="download"
                      href={DOWNLOAD_URL}
                      download
                      className="inline-flex items-center gap-2 rounded-full bg-blue-500 px-4 py-2 text-sm font-semibold text-slate-50 shadow-glow shadow-blue-500/40 hover:bg-blue-400"
                    >
                      <Download className="h-4 w-4" />
                      Download VOS
                    </a>
                    <span className="block text-xs text-slate-400">
                      Works on Windows 10 and 11 · Free
                    </span>
                    <span className="block text-xs text-slate-500">
                      If Windows shows a warning: click <strong className="text-slate-400">More info</strong> → <strong className="text-slate-400">Run anyway</strong>.
                    </span>
                  </div>
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
                className="relative"
                respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}
              >
                <div className="pointer-events-none absolute -inset-6 -z-10 rounded-[32px] bg-gradient-to-b from-blue-500/15 via-blue-500/5 to-transparent blur-3xl" />
                <div className="relative overflow-hidden rounded-3xl border border-blue-500/30 bg-slate-900/80 p-4 shadow-2xl shadow-blue-500/20">
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
                      <div className="h-12 w-12 rounded-full border border-blue-500/70 bg-slate-950/70 shadow-[0_0_30px_rgba(59,130,246,0.7)]" />
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
                  <img
                    src={heroImage}
                    alt=""
                    className="pointer-events-none absolute -bottom-10 -right-10 w-40 opacity-60"
                  />
                </div>
              </Reveal>
            </div>
            </div>
          </Reveal>
        </section>

        {/* Features */}
        <section className="mt-16 border-y border-slate-800/70 py-10 md:mt-20 md:py-12">
          <div className="grid gap-8 md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] md:items-center">
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
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
                      <div className="inline-flex rounded-full bg-slate-900/90 p-2 text-blue-400">
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

            <Reveal delayMs={120} lift={false} respectReducedMotion={!ANIMATE_EVEN_IF_REDUCE_MOTION}>
              <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5">
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
                className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-blue-500 px-4 py-2 text-xs font-semibold text-slate-50 shadow-glow hover:bg-blue-400"
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
                    <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
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
                    <details className="group rounded-2xl border border-slate-800 bg-slate-900/70 px-4 py-3">
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
            <div className="relative overflow-hidden rounded-[32px] border border-blue-500/25 bg-white/[0.035] p-6 shadow-[0_30px_120px_rgba(15,23,42,0.9)] backdrop-blur-2xl md:p-10">
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
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-blue-500 px-5 py-2.5 text-sm font-semibold text-slate-50 shadow-glow shadow-blue-500/40 hover:bg-blue-400"
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

