/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'rf-primary': '#00a020',
        'rf-secondary': '#009e20',
        'rf-accent': '#00c030',
        'rf-bg-dark': '#0a1a0a',
        'rf-bg-light': '#102010',
      },
      fontFamily: {
        mono: ['Terminus', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
