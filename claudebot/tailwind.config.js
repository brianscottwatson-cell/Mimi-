module.exports = {
  content: [
    "./client/src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        neon: {
          green: "#00ff00",
          pink: "#ff00ff",
          cyan: "#00ffff",
        },
      },
      fontFamily: {
        mono: ["Courier New", "monospace"],
      },
    },
  },
  plugins: [],
};
