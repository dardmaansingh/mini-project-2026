/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // SOC dark theme palette
        navy: {
          950: '#030712',
          900: '#0a0f1e',
          850: '#0d1426',
          800: '#111827',
          700: '#1a2540',
          600: '#1e2d4a',
          500: '#243358',
        },
        accent: {
          blue:   '#3b82f6',
          cyan:   '#06b6d4',
          teal:   '#14b8a6',
          purple: '#8b5cf6',
          orange: '#f97316',
        },
        severity: {
          critical:      '#ef4444',
          high:          '#f97316',
          medium:        '#eab308',
          low:           '#3b82f6',
          informational: '#6b7280',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(rgba(59,130,246,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.03) 1px, transparent 1px)",
      },
      backgroundSize: {
        'grid': '32px 32px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateX(-10px)', opacity: 0 },
          '100%': { transform: 'translateX(0)', opacity: 1 },
        },
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
      },
    },
  },
  plugins: [],
}
