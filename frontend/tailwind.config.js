/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        sage: {
          50: '#F6F5F1',
          100: '#EFEEE7',
          200: '#D8DED9',
          300: '#BFC9C2',
        },
        ink: {
          DEFAULT: '#1F2C2B',
          soft: '#3E4C4A',
          faint: '#6B7B78',
        },
        teal: {
          50: '#EAF2EF',
          100: '#CFE3DC',
          400: '#3F8778',
          500: '#2F6F62',
          600: '#255A50',
          700: '#1C453D',
        },
        clay: {
          400: '#D9A08F',
          500: '#C98B7A',
          600: '#B06F5D',
        },
        amber: {
          100: '#FBEFDA',
          400: '#E3A857',
          600: '#B9822F',
        },
      },
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        xl2: '1.25rem',
      },
      boxShadow: {
        quiet: '0 1px 2px rgba(31, 44, 43, 0.04)',
      },
    },
  },
  plugins: [],
}
