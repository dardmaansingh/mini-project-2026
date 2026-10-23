/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Fortinet FortiGate authentic light-canvas palette
        fg: {
          green:  '#237A3B',  // FortiGate header forest green
          light:  '#16A34A',  // Active green accent
          dark:   '#1A5C2C',  // Dark green
        },
        bg: {
          base:   '#F0F2F6',  // Main light canvas background (from FortiGate screenshots)
          panel:  '#22262E',  // Dark charcoal sidebar
          card:   '#FFFFFF',  // Pure white card surfaces
          raised: '#F8FAFC',  // Slightly elevated / table header
          hover:  '#F1F5F9',  // Table row hover
        },
        border: {
          DEFAULT: '#D8DEE4',
          light:   '#E5E7EB',
          dark:    '#CBD5E1',
          focus:   '#237A3B',
        },
        accent: {
          green:  '#16A34A',  // healthy / active
          sky:    '#0284C7',  // info
          orange: '#EA580C',  // warning / support
          red:    '#DC2626',  // critical
          purple: '#9333EA',  // routing
        },
        sev: {
          critical: '#DC2626',
          high:     '#EA580C',
          medium:   '#D97706',
          low:      '#0284C7',
          info:     '#64748B',
        },
        text: {
          primary:   '#0F172A',  // Dark slate primary text on white
          secondary: '#475569',  // Medium slate
          muted:     '#64748B',  // Muted gray labels
          accent:    '#16A34A',
        },
        // Keep navy token aliased to slate for compatibility
        navy: {
          950: '#0F172A',
          900: '#1E293B',
          850: '#334155',
          800: '#475569',
          700: '#64748B',
          600: '#94A3B8',
          500: '#CBD5E1',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Courier New', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.65rem', { lineHeight: '1rem' }],
      },
      animation: {
        'pulse-slow':  'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-green': 'pulseGreen 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in':     'fadeIn 0.2s ease-out',
        'slide-down':  'slideDown 0.2s ease-out',
      },
      keyframes: {
        slideDown: {
          '0%':   { transform: 'translateY(-6px)', opacity: '0' },
          '100%': { transform: 'translateY(0)',    opacity: '1' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseGreen: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.4' },
        },
      },
      boxShadow: {
        'card':   '0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.04)',
        'panel':  '0 4px 6px -1px rgba(0,0,0,0.08)',
        'widget': '0 1px 2px rgba(0,0,0,0.05)',
      },
    },
  },
  plugins: [],
}
