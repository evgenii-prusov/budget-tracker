import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', 'Inter', 'system-ui', 'sans-serif'],
        body: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        base: {
          900: '#0a0c18',
          800: '#0f1324',
          700: '#161b31',
          600: '#1d2540',
        },
        neon: {
          pink: '#ff3c8f',
          violet: '#9b5cff',
          cyan: '#3ff0ff',
          amber: '#f9b248',
        },
        accent: '#9b5cff',
      },
      boxShadow: {
        glow: '0 0 25px rgba(159, 92, 255, 0.25)',
        card: '0 10px 40px rgba(0,0,0,0.25)',
      },
      backgroundImage: {
        'grid-dots':
          'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.08) 1px, transparent 0)',
      },
    },
  },
  plugins: [],
};

export default config;
