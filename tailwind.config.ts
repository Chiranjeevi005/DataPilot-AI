import { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/**/*.{js,ts,jsx,tsx,mdx}"
    ],
    theme: {
        extend: {
            colors: {
                background: "#F3F6F9",
                foreground: "#1E293B",
                primary: {
                    DEFAULT: "#2563EB",
                    foreground: "#FFFFFF",
                    glow: "rgba(37, 99, 235, 0.4)"
                },
                secondary: {
                    DEFAULT: "#06B6D4",
                    foreground: "#FFFFFF",
                    glow: "rgba(6, 182, 212, 0.3)"
                },
                muted: {
                    DEFAULT: "#F1F5F9",
                    foreground: "#64748B",
                },
                accent: {
                    DEFAULT: "#F8FAFC",
                    foreground: "#1E293B",
                },
                card: {
                    DEFAULT: "#FFFFFF",
                    foreground: "#1E293B",
                },
                slate: {
                    50: '#F8FAFC',
                    100: '#F1F5F9',
                    200: '#E2E8F0',
                    300: '#CBD5E1',
                    400: '#94A3B8',
                    500: '#64748B',
                    600: '#475569',
                    700: '#334155',
                    800: '#1E293B',
                    900: '#0F172A',
                }
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
            },
            fontFamily: {
                sans: ["var(--font-inter)", "sans-serif"],
            },
            boxShadow: {
                'soft': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
                'hover': '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)',
                'glow': '0 0 15px rgba(37, 99, 235, 0.3)',
            },
        },
    },
    plugins: [],
};
export default config;
