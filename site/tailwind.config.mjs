/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: '#05070a',
          900: '#0a0d14',
          850: '#0f141f',
          800: '#141a29',
          700: '#1f293d',
          600: '#2a3752',
        },
        amber: {
          glow: '#ff9900',
          accent: '#f59e0b',
        },
        steel: {
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
        },
      },
      fontFamily: {
        mono: [
          'JetBrains Mono',
          'Fira Code',
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Monaco',
          'Consolas',
          'monospace',
        ],
        sans: [
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
      },
      boxShadow: {
        'amber-glow': '0 0 20px -5px rgba(255, 153, 0, 0.3)',
        'amber-glow-lg': '0 0 35px -5px rgba(255, 153, 0, 0.45)',
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, rgba(255, 153, 0, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 153, 0, 0.05) 1px, transparent 1px)",
      },
      backgroundSize: {
        'grid-pattern': '32px 32px',
      },
    },
  },
  plugins: [],
};
