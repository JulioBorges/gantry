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
      },
    },
  },
  plugins: [],
};
