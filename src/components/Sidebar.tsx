"use client";

import React from 'react';
import Link from 'next/link';
import { Plus, Settings, PanelLeftClose, PanelLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSidebarStore } from '@/lib/store';

export default function Sidebar() {
    const isOpen = useSidebarStore((state) => state.isOpen);
    const toggleSidebar = useSidebarStore((state) => state.toggle);

    const recentFiles = [
        { name: 'sales_oct.csv', type: 'csv', time: '2 hours ago' },
        { name: 'invoices_batch.pdf', type: 'pdf', time: '5 hours ago' },
        { name: 'customers.json', type: 'json', time: '1 day ago' },
        { name: 'q3_metrics.xlsx', type: 'xls', time: '2 days ago' }
    ];

    const getBadgeClass = (type: string) => {
        if (type === 'csv') return 'text-emerald-500 bg-emerald-50';
        if (type === 'pdf') return 'text-rose-500 bg-rose-50';
        return 'text-amber-500 bg-amber-50';
    };

    return (
        <>
            {/* Toggle Button - Fixed position, always visible */}
            <button
                onClick={toggleSidebar}
                className={cn(
                    "fixed top-20 p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-800 transition-all shadow-sm z-50",
                    isOpen ? "left-[280px]" : "left-3"
                )}
                aria-label={isOpen ? "Close sidebar" : "Open sidebar"}
            >
                {isOpen ? <PanelLeftClose size={18} /> : <PanelLeft size={18} />}
            </button>

            {/* Sidebar */}
            <aside className={cn(
                "bg-slate-50/80 backdrop-blur-xl border-r border-slate-200 h-[calc(100vh-64px)] fixed left-0 top-16 flex flex-col z-40 transition-all duration-300 ease-in-out overflow-hidden shadow-2xl lg:shadow-none",
                isOpen ? "w-[280px] p-6 shadow-xl" : "w-0 p-0"
            )}>
                {/* Sidebar Content */}
                <div className={cn(
                    "flex flex-col h-full min-w-[260px] transition-opacity duration-200",
                    isOpen ? "opacity-100" : "opacity-0"
                )}>
                    <Link href="/upload" className="w-full bg-gradient-to-br from-blue-500 to-blue-600 hover:to-blue-700 text-white px-3 py-3 rounded-xl font-medium flex items-center justify-center gap-2 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/30 hover:-translate-y-0.5 transition-all duration-200 mb-8">
                        <Plus size={20} strokeWidth={3} />
                        <span>New File</span>
                    </Link>

                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 pl-2">Recent Uploads</div>

                    <div className="flex flex-col gap-2 flex-1 overflow-y-auto">
                        {recentFiles.map((file, index) => (
                            <div key={index} className="flex items-center gap-3 p-2.5 bg-white/80 rounded-lg border border-transparent hover:border-cyan-500/20 hover:shadow-soft hover:-translate-y-0.5 transition-all cursor-pointer group">
                                <div className={cn("w-8 h-8 rounded-md flex items-center justify-center text-[10px] font-bold", getBadgeClass(file.type))}>
                                    {file.type.toUpperCase()}
                                </div>
                                <div className="flex flex-col min-w-0">
                                    <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 truncate">{file.name}</span>
                                    <span className="text-xs text-slate-400">{file.time}</span>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="mt-auto pt-4 border-t border-slate-200/50">
                        <button className="flex items-center gap-2.5 w-full p-2.5 text-slate-500 font-medium hover:bg-slate-200/50 hover:text-slate-800 rounded-lg transition-all">
                            <Settings size={18} />
                            <span>Settings</span>
                        </button>
                    </div>
                </div>
            </aside>
        </>
    );
}
