/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        police: {
          dark: '#0B132B',      // Dark midnight blue
          navy: '#1C2541',      // Police uniform navy
          blue: '#3A506B',      // Slate blue
          light: '#5BC0BE',     // Police cyan beacon
          gold: '#DCBA55',      // Premium police batch gold
          red: '#EF4444',       // Emergency siren red
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
