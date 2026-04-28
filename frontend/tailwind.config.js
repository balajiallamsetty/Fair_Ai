export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Poppins', 'ui-sans-serif', 'system-ui'],
      },
      colors: {
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(129,140,248,0.2), 0 20px 45px -20px rgba(79,70,229,0.5)',
      },
      backgroundImage: {
        'hero-gradient': 'radial-gradient(circle at top left, rgba(99,102,241,0.22), transparent 30%), radial-gradient(circle at 80% 20%, rgba(14,165,233,0.16), transparent 25%), linear-gradient(135deg, rgba(15,23,42,0.96), rgba(2,6,23,0.98))',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.8s linear infinite',
      },
    },
  },
  plugins: [],
};
