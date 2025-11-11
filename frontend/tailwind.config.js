/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '0.75rem',
      },
      colors: {
        // Light theme colors (from design_tokens.json)
        'bg-light': '#FFFFFF',
        'surface-light': '#F2F2F7',
        'text-primary-light': '#000000',
        'text-secondary-light': '#6E6E73',
        'accent-light': '#007AFF',
        'accent-text-light': '#FFFFFF',
        'border-light': '#D1D1D6',
        
        // Dark theme colors (from design_tokens.json)
        'bg-dark': '#000000',
        'surface-dark': '#1C1C1E',
        'text-primary-dark': '#FFFFFF',
        'text-secondary-dark': '#8E8E93',
        'accent-dark': '#0D84FF',
        'accent-text-dark': '#FFFFFF',
        'border-dark': '#38383A',
      },
    },
  },
  plugins: [],
}
