module.exports = {
    // NOTE: Update this to include the paths to all of your component files.
    content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
    presets: [require("nativewind/preset")],
    theme: {
        extend: {
            colors: {
                background: "#0B3130", // Deep Green
                surface: "#113835",
                primary: "#FFD700", // Gold
                secondary: "#15423F", // Muted Green
                text: "#FFFFFF", // White for Headings
                "text-muted": "#C0CAC9", // Light Gray for Body
                muted: "#C0CAC9",
            },
            fontFamily: {
                serif: ["PlayfairDisplay_600SemiBold", "serif"],
                sans: ["Inter_400Regular", "sans-serif"],
                "sans-bold": ["Inter_700Bold", "sans-serif"],
            },
        },
    },
    plugins: [],
};
