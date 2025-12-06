"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { Search, Bell, Menu } from 'lucide-react';
import { cn } from '@/lib/utils';
import Logo from '@/components/Logo';
import { useSidebarStore } from '@/lib/store';

export default function NavBar() {
    const [isFocused, setIsFocused] = useState(false);
    const toggleSidebar = useSidebarStore((state) => state.toggle);

    return (
        <nav className="fixed top-0 left-0 right-0 h-16 z-50 glass-nav flex items-center justify-between px-6">
            <div className="flex items-center gap-3">
                {/* Mobile Toggle - Only for small screens where sidebar logic changes */}
                <button
                    onClick={toggleSidebar}
                    className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-800 transition-colors"
                    aria-label="Toggle sidebar"
                >
                    <Menu size={22} />
                </button>

                <Link href="/" className="flex items-center gap-2.5 font-semibold text-lg tracking-tight text-slate-800 hover:opacity-80 transition-opacity">
                    <div>
                        <Logo size={32} />
                    </div>
                    <span>DataPilot AI</span>
                </Link>
            </div>

            <div className="hidden md:block relative w-96">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={18} />
                <input
                    type="text"
                    placeholder="Search uploads, insights..."
                    className={cn(
                        "w-full py-2.5 pl-10 pr-4 rounded-full border border-slate-200/80 bg-white/40 text-sm transition-all duration-200 ease-out",
                        "focus:outline-none focus:bg-white focus:w-[102%] focus:-ml-[1%] focus:shadow-[0_0_0_3px_rgba(37,99,235,0.1)] focus:border-primary"
                    )}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                />
            </div>

            <div className="flex items-center gap-4">
                <button className="p-2 rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors" aria-label="Notifications">
                    <Bell size={20} />
                </button>
                <div className="w-9 h-9 rounded-full bg-slate-200 relative border-2 border-white shadow-[0_0_0_1px_rgba(226,232,240,1)] overflow-hidden">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="https://ui-avatars.com/api/?name=User&background=2563EB&color=fff" alt="User" className="w-full h-full object-cover" />
                    <div className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 border-2 border-white rounded-full"></div>
                </div>
            </div>
        </nav>
    );
}
