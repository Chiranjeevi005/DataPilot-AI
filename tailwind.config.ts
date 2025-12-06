import { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/**/*.{js,ts,jsx,tsx,mdx}"
    ],
    theme: {
        // Explicit responsive breakpoints (mobile-first)
        screens: {
            'sm': '640px',   // Small tablets and large phones
            'md': '768px',   // Tablets
            'lg': '1024px',  // Laptops and small desktops
            'xl': '1280px',  // Desktops
            '2xl': '1536px', // Large desktops
        },
        // Custom container widths per breakpoint
        container: {
            center: true,
            padding: {
                DEFAULT: '1rem',
                sm: '1.5rem',
                md: '2rem',
                lg: '2.5rem',
                xl: '3rem',
                '2xl': '4rem',
            },
            screens: {
                sm: '640px',
                md: '768px',
                lg: '1024px',
                xl: '1280px',
                '2xl': '1536px',
            },
        },
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
                // Semantic tokens
                surface: {
                    DEFAULT: "#FFFFFF",
                    secondary: "#F8FAFC",
                    tertiary: "#F1F5F9",
                },
                danger: {
                    DEFAULT: "#EF4444",
                    foreground: "#FFFFFF",
                },
                success: {
                    DEFAULT: "#10B981",
                    foreground: "#FFFFFF",
                },
                warning: {
                    DEFAULT: "#F59E0B",
                    foreground: "#FFFFFF",
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
            // Responsive typography using clamp()
            fontSize: {
                'xs': ['0.75rem', { lineHeight: '1rem' }],
                'sm': ['0.875rem', { lineHeight: '1.25rem' }],
                'base': ['1rem', { lineHeight: '1.5rem' }],
                'lg': ['1.125rem', { lineHeight: '1.75rem' }],
                'xl': ['1.25rem', { lineHeight: '1.75rem' }],
                '2xl': ['1.5rem', { lineHeight: '2rem' }],
                '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
                '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
                '5xl': ['3rem', { lineHeight: '1' }],
                // Fluid typography
                'h1': ['clamp(1.875rem, 4vw, 3rem)', { lineHeight: '1.2', fontWeight: '700' }],
                'h2': ['clamp(1.5rem, 3vw, 2.25rem)', { lineHeight: '1.3', fontWeight: '600' }],
                'h3': ['clamp(1.25rem, 2.5vw, 1.875rem)', { lineHeight: '1.4', fontWeight: '600' }],
                'h4': ['clamp(1.125rem, 2vw, 1.5rem)', { lineHeight: '1.5', fontWeight: '600' }],
                'body-lg': ['clamp(1rem, 1.5vw, 1.125rem)', { lineHeight: '1.6' }],
                'body': ['clamp(0.875rem, 1.2vw, 1rem)', { lineHeight: '1.6' }],
            },
            // Consistent spacing tokens
            spacing: {
                'xs': '0.5rem',    // 8px
                'sm': '0.75rem',   // 12px
                'md': '1rem',      // 16px
                'lg': '1.5rem',    // 24px
                'xl': '2rem',      // 32px
                '2xl': '3rem',     // 48px
                '3xl': '4rem',     // 64px
                '4xl': '6rem',     // 96px
                // Touch target minimum
                'touch': '2.75rem', // 44px minimum touch target
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
                'card': '0.75rem',
                'button': '0.5rem',
            },
            fontFamily: {
                sans: ["var(--font-inter)", "sans-serif"],
            },
            boxShadow: {
                'soft': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
                'hover': '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)',
                'glow': '0 0 15px rgba(37, 99, 235, 0.3)',
                'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
                'card-hover': '0 10px 20px -5px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            },
            // Minimum touch target size
            minHeight: {
                'touch': '2.75rem', // 44px
            },
            minWidth: {
                'touch': '2.75rem', // 44px
            },
        },
    },
    plugins: [],
};
export default config;
