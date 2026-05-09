/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          background: '#FDFDFD',
          surface: '#F5F5F5',
          ink: '#1A1A1A',
          muted: '#666666',
          accent: '#0F766E',
          highlight: '#CCFBF1',
        },
      },
      fontFamily: {
        serif: ['"Young Serif"', 'serif'],
        sans: ['"Inter"', 'sans-serif'],
      },
      animation: {
        "slide-in": "slideIn 0.2s ease-out",
        "pulse-dot": "pulseDot 1.4s ease-in-out infinite",
      },
      keyframes: {
        slideIn: {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        pulseDot: {
          "0%, 80%, 100%": { transform: "scale(0)", opacity: "0.3" },
          "40%": { transform: "scale(1)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
}
