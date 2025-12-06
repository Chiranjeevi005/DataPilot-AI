"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { Search, Bell, PanelLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import Logo from '@/components/Logo';
import { useSidebarStore } from '@/lib/store';



export default function NavBar() {
    const [isFocused, setIsFocused] = useState(false);
    const toggleSidebar = useSidebarStore((state) => state.toggle);

    return (
        <nav className="fixed top-0 left-0 right-0 h-16 z-50 glass-nav flex items-center justify-between px-4 md:px-6 transition-all duration-300">
            <div className="flex items-center gap-3 md:gap-4">
                {/* Mobile/Tablet Toggle - Visible on screens smaller than lg */}
                <button
                    onClick={toggleSidebar}
                    className="p-2 -ml-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-800 transition-colors focus-visible:ring-2 focus-visible:ring-primary"
                    aria-label="Toggle navigation"
                    aria-controls="mobile-sidebar"
                >
                    <PanelLeft className="w-6 h-6" />
                </button>

                <Link
                    href="/"
                    className="flex items-center gap-2.5 font-semibold text-lg tracking-tight text-slate-800 hover:opacity-80 transition-opacity focus-visible:rounded-lg"
                >
                    <div>
                        <Logo size={32} />
                    </div>
                    <span className="hidden min-[360px]:inline-block">DataPilot AI</span>
                </Link>
            </div>

            {/* Desktop Search - Hidden on mobile/tablet, moved to sidebar/sheet */}
            <div className="hidden lg:block relative w-96 max-w-[50vw]">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={18} />
                <input
                    type="text"
                    placeholder="Search uploads, insights..."
                    className={cn(
                        "w-full py-2.5 pl-10 pr-4 rounded-full border border-slate-200/80 bg-white/40 text-sm transition-all duration-200 ease-out",
                        "focus:outline-none focus:bg-white focus:shadow-[0_0_0_3px_rgba(37,99,235,0.1)] focus:border-primary",
                        "placeholder:text-slate-400"
                    )}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                />
            </div>

            <div className="flex items-center gap-2 md:gap-4">
                <button
                    className="p-2 rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors focus-visible:ring-2 focus-visible:ring-primary relative"
                    aria-label="Notifications"
                >
                    <Bell size={20} />
                    <span className="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full border border-white"></span>
                </button>

                {/* Profile Dropdown Trigger */}
                <button
                    className="w-9 h-9 rounded-full bg-slate-200 relative border-2 border-white shadow-[0_0_0_1px_rgba(226,232,240,1)] overflow-hidden transition-transform active:scale-95 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                    aria-label="User menu"
                >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="https://ui-avatars.com/api/?name=User&background=2563EB&color=fff" alt="User" className="w-full h-full object-cover" />
                </button>
            </div>
        </nav>
    );
}
