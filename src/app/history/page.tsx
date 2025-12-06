"use client";

import React from 'react';
import NavBar from '@/components/NavBar';
import Sidebar from '@/components/Sidebar';
import ResponsiveContainer from '@/components/ResponsiveContainer';
import RecentUploadsPanel from '@/components/RecentUploadsPanel';
import { useSidebarStore } from '@/lib/store';
import { cn } from '@/lib/utils';

export default function HistoryPage() {
    const isOpen = useSidebarStore((state) => state.isOpen);

    return (
        <div className="min-h-screen bg-background font-sans text-slate-900">
            <NavBar />
            <Sidebar />

            {/* Main Content Area */}
            <main className={cn("pt-24 pb-12 transition-all duration-300 ease-in-out", isOpen ? "md:ml-20 lg:ml-72" : "ml-0")}>
                <ResponsiveContainer maxWidth="2xl">
                    <div className="space-y-6">
                        {/* Page Header */}
                        <div className="space-y-2">
                            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
                                Upload History
                            </h1>
                            <p className="text-slate-500 text-lg">
                                View and manage your recent data uploads and analyses.
                            </p>
                        </div>

                        {/* Recent Uploads Panel */}
                        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <RecentUploadsPanel />
                        </div>
                    </div>
                </ResponsiveContainer>
            </main>
        </div>
    );
}
