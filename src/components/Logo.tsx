export default function Logo({ size = 32, className = "" }: { size?: number, className?: string }) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 40 40"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className={className}
        >
            <defs>
                <linearGradient id="logoGradient" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#2563EB" />
                    <stop offset="1" stopColor="#06B6D4" />
                </linearGradient>
                <filter id="glow" x="-4" y="-4" width="48" height="48" filterUnits="userSpaceOnUse">
                    <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                    <feMerge>
                        <feMergeNode in="coloredBlur" />
                        <feMergeNode in="SourceGraphic" />
                    </feMerge>
                </filter>
            </defs>

            {/* Central Hexagon - Data Core */}
            <path
                d="M20 5L33 12.5V27.5L20 35L7 27.5V12.5L20 5Z"
                stroke="url(#logoGradient)"
                strokeWidth="2.5"
                fill="white"
                filter="url(#glow)"
            />

            {/* Internal Connectivity - Automation */}
            <path
                d="M20 12V28M13 16.5L27 24.5M27 16.5L13 24.5"
                stroke="url(#logoGradient)"
                strokeWidth="2"
                strokeLinecap="round"
                opacity="0.8"
            />

            {/* Orbiting Dots - Intelligence */}
            <circle cx="20" cy="5" r="2.5" fill="#06B6D4" className="animate-pulse" />
            <circle cx="33" cy="27.5" r="2.5" fill="#2563EB" className="animate-pulse" style={{ animationDelay: '0.5s' }} />
            <circle cx="7" cy="27.5" r="2.5" fill="#2563EB" className="animate-pulse" style={{ animationDelay: '1s' }} />

        </svg>
    );
}
