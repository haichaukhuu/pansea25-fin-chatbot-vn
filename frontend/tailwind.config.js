/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        // Custom color palette
        primary: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#21A691', // Main teal color
          600: '#1d9485',
          700: '#1a7a6b',
          800: '#176155',
          900: '#144e47',
        },
        accent: {
          50: '#f7fee7',
          100: '#ecfccb',
          200: '#d9f99d',
          300: '#bef264',
          400: '#a3e635',
          500: '#87DF2C', // Bright lime green
          600: '#75c227',
          700: '#5da61e',
          800: '#4a8319',
          900: '#3d6b16',
        },
        dark: {
          50: '#f6f7f6',
          100: '#e1e4e1',
          200: '#c3c9c2',
          300: '#9ca49b',
          400: '#768075',
          500: '#5a655a',
          600: '#4a524a',
          700: '#3d443d',
          800: '#343936',
          900: '#27403E', // Dark forest green
        },
        neutral: {
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#e5e5e5',
          300: '#d4d4d4',
          400: '#B4B4B2', // Light gray
          500: '#9ca3af',
          600: '#6b7280',
          700: '#4b5563',
          800: '#374151',
          900: '#1f2937',
        },
        gray: {
          850: '#1f2937',
          950: '#111827',
        },
      },
    },
  },
  plugins: [],
}
