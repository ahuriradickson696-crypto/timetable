/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        aviu: {
          50:  '#f4f2fb',
          100: '#e8e4f5',
          200: '#d0c9eb',
          300: '#b1a4dc',
          400: '#8f7bc8',
          500: '#7055b0',
          600: '#5b3f98',
          700: '#4d3489',
          800: '#492983',
          900: '#3a1f6b',
          950: '#221042',
        },
      },
    },
  },
  plugins: [],
};