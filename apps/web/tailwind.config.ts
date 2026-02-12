import type { Config } from 'tailwindcss'

export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
        "./pages/**/*.{js,ts,jsx,tsx}",
        "./components/**/*.{js,ts,jsx,tsx}",
        "./lib/**/*.{js,ts,jsx,tsx}",
        "./*.{js,ts,jsx,tsx}", // For App.tsx if it's in root
    ],
    theme: {
        extend: {},
    },
    plugins: [],
} satisfies Config
