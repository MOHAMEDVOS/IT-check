import React from "react";

type RevealProps = {
  children: React.ReactNode;
  className?: string;
  /**
   * Delay in ms for a subtle stagger effect.
   */
  delayMs?: number;
  /**
   * If true, slightly translates upward when revealing.
   */
  lift?: boolean;
  /**
   * Primary = bigger motion + slightly longer ease.
   * Secondary = smaller motion + slightly snappier.
   */
  tier?: "primary" | "secondary";
  /**
   * Override motion distance (px) when lift=true.
   */
  liftPx?: number;
  /**
   * Slight horizontal slide (px) when out. Positive = from right, negative = from left.
   */
  slideX?: number;
  /**
   * Scale when out (0–1). Slightly < 1 gives a subtle zoom-in on reveal.
   */
  scale?: number;
  /**
   * Override duration (ms) for the reveal transition.
   */
  durationMs?: number;
  /**
   * If false, animations still run even when OS asks to reduce motion.
   */
  respectReducedMotion?: boolean;
};

function useInView<T extends Element>(
  options?: IntersectionObserverInit,
  respectReducedMotion: boolean = true
) {
  const ref = React.useRef<T | null>(null);
  const [inView, setInView] = React.useState(false);

  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // If the user prefers reduced motion, render immediately (unless overridden).
    if (
      respectReducedMotion &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    ) {
      setInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            // Ensure the "out" styles paint first, then animate in.
            requestAnimationFrame(() => {
              requestAnimationFrame(() => setInView(true));
            });
          } else {
            // When leaving the viewport, go back to "out" so it can animate again when coming back.
            setInView(false);
          }
        }
      },
      { threshold: 0.18, rootMargin: "0px 0px -10% 0px", ...(options ?? {}) }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [options]);

  return { ref, inView };
}

export function Reveal({
  children,
  className,
  delayMs = 0,
  lift = true,
  tier = "secondary",
  liftPx,
  slideX,
  scale,
  durationMs,
  respectReducedMotion = true
}: RevealProps) {
  const { ref, inView } = useInView<HTMLDivElement>(undefined, respectReducedMotion);

  const style: React.CSSProperties = {
    transitionDelay: `${delayMs}ms`,
    ...(durationMs ? { transitionDuration: `${durationMs}ms` } : {}),
    ...(liftPx != null ? { ["--reveal-lift" as string]: `${liftPx}px` } : {}),
    ...(slideX != null ? { ["--reveal-x" as string]: `${slideX}px` } : {}),
    ...(scale != null ? { ["--reveal-scale" as string]: String(scale) } : {})
  };

  return (
    <div
      ref={ref}
      className={[
        "reveal",
        tier === "primary" ? "reveal--primary" : "reveal--secondary",
        inView ? "reveal--in" : "reveal--out",
        lift ? "reveal--lift" : "",
        className ?? ""
      ].join(" ")}
      style={style}
    >
      {children}
    </div>
  );
}

