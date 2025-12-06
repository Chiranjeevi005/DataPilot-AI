/**
 * ResponsiveContainer Component
 * 
 * Provides consistent padding, centered content, and optional maxWidth
 * for responsive layouts across all breakpoints.
 * 
 * Usage:
 * <ResponsiveContainer maxWidth="lg">
 *   <YourContent />
 * </ResponsiveContainer>
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface ResponsiveContainerProps {
    children: React.ReactNode;
    className?: string;
    maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
    noPadding?: boolean;
}

const maxWidthClasses = {
    sm: 'max-w-screen-sm',   // 640px
    md: 'max-w-screen-md',   // 768px
    lg: 'max-w-screen-lg',   // 1024px
    xl: 'max-w-screen-xl',   // 1280px
    '2xl': 'max-w-screen-2xl', // 1536px
    full: 'max-w-full',
};

export default function ResponsiveContainer({
    children,
    className,
    maxWidth = 'xl',
    noPadding = false,
}: ResponsiveContainerProps) {
    return (
        <div
            className={cn(
                'w-full mx-auto',
                maxWidthClasses[maxWidth],
                !noPadding && 'px-4 sm:px-6 md:px-8 lg:px-10 xl:px-12',
                className
            )}
        >
            {children}
        </div>
    );
}
