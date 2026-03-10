/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["system-ui", "ui-sans-serif", "Inter", "sans-serif"]
      },
      colors: {
        brand: {
          500: "#3b82f6",
          600: "#2563eb"
        }
      },
      boxShadow: {
        glow: "0 0 40px rgba(59, 130, 246, 0.35)",
        "glow-lg": "0 0 60px rgba(59, 130, 246, 0.4)",
        "glow-pulse": "0 0 50px rgba(59, 130, 246, 0.5)"
      },
      keyframes: {
        "glow-pulse": {
          "0%, 100%": { opacity: "0.6", filter: "brightness(1)" },
          "50%": { opacity: "1", filter: "brightness(1.2)" }
        },
        "gradient-shift": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" }
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" }
        },
        "scan-line": {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" }
        },
        float: {
          "0%, 100%": { transform: "translateY(0) translateX(0)" },
          "33%": { transform: "translateY(-6px) translateX(3px)" },
          "66%": { transform: "translateY(3px) translateX(-4px)" }
        },
        "border-glow": {
          "0%, 100%": { borderColor: "rgba(59, 130, 246, 0.3)", boxShadow: "0 0 20px rgba(59, 130, 246, 0.15)" },
          "50%": { borderColor: "rgba(59, 130, 246, 0.5)", boxShadow: "0 0 35px rgba(59, 130, 246, 0.25)" }
        },
        "cta-glow": {
          "0%, 100%": { boxShadow: "0 0 30px rgba(59, 130, 246, 0.4), 0 0 60px rgba(59, 130, 246, 0.15)" },
          "50%": { boxShadow: "0 0 45px rgba(59, 130, 246, 0.55), 0 0 80px rgba(59, 130, 246, 0.2)" }
        }
      },
      animation: {
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "gradient-shift": "gradient-shift 8s ease infinite",
        shimmer: "shimmer 4s ease-in-out infinite",
        "scan-line": "scan-line 6s linear infinite",
        float: "float 8s ease-in-out infinite",
        "border-glow": "border-glow 2.5s ease-in-out infinite",
        "cta-glow": "cta-glow 2.5s ease-in-out infinite"
      }
    }
  },
  plugins: []
};

