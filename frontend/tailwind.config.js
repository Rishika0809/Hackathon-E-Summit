/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#1a73e8",
        danger: "#ea4335",
        warning: "#fbbc04",
        success: "#34a853",
      },
    },
  },
  plugins: [],
};
