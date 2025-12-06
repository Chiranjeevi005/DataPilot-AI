"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Plus, Settings, FileText, BarChart2, Table, Search, X, Clock, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSidebarStore, useAppStore } from '@/lib/store';

export default function Sidebar() {
    const isOpen = useSidebarStore((state) => state.isOpen);
    const closeSidebar = useSidebarStore((state) => state.close);
    const openSidebar = useSidebarStore((state) => state.open);
    const recentUploads = useAppStore((state) => state.recentUploads);
    const router = useRouter();

    // Initial State: Open on Desktop/Tablet, Closed on Mobile
    useEffect(() => {
        if (window.innerWidth >= 768) {
            openSidebar();
        }
    }, [openSidebar]);

    const getBadgeClass = (type: string) => {
        if (type === 'csv') return 'text-emerald-700 bg-emerald-100';
        if (type === 'pdf') return 'text-rose-700 bg-rose-100';
        if (type === 'xlsx') return 'text-blue-700 bg-blue-100';
        return 'text-amber-700 bg-amber-100';
    };

    const getRelativeTime = (isoString: string) => {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    const getStatusIcon = (status: 'processing' | 'completed' | 'error') => {
        switch (status) {
            case 'processing':
                return <Loader2 size={12} className="text-blue-500 animate-spin" />;
            case 'completed':
                return <CheckCircle2 size={12} className="text-green-500" />;
            case 'error':
                return <AlertCircle size={12} className="text-red-500" />;
        }
    };

    const handleRecentUploadClick = (jobId: string, status: 'processing' | 'completed' | 'error') => {
        closeSidebar();

        if (status === 'completed') {
            router.push(`/results?jobId=${jobId}`);
        } else if (status === 'processing') {
            router.push(`/loading?jobId=${jobId}`);
        } else {
            // For error status, could navigate to an error page or show a message
            router.push(`/upload`);
        }
    };

    return (
        <>
            {/* Mobile Backdrop */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-40 md:hidden transition-opacity"
                    onClick={closeSidebar}
                    aria-hidden="true"
                />
            )}

            {/* Sidebar Container */}
            <aside className={cn(
                "fixed left-0 top-0 bottom-0 z-50 flex flex-col bg-slate-50/95 backdrop-blur-xl border-r border-slate-200 shadow-2xl transition-all duration-300 ease-in-out md:shadow-none",
                // Base: Full height, transform controlled by isOpen
                "w-[85vw] max-w-[300px] h-full transform",
                isOpen ? "translate-x-0" : "-translate-x-full",
                // Tablet/Desktop specifics (Width/Position), distinct from Visibility (transform)
                "md:top-16 md:h-[calc(100vh-64px)] md:z-30",
                "md:w-20 lg:w-72"
            )}>
                {/* Mobile Header: Logo/Close */}
                <div className="flex items-center justify-between p-4 md:hidden border-b border-slate-200/50">
                    <span className="font-semibold text-lg text-slate-800">Menu</span>
                    <button
                        onClick={closeSidebar}
                        className="p-2 text-slate-500 hover:bg-slate-200 rounded-full"
                        aria-label="Close menu"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Mobile Search */}
                <div className="p-4 md:hidden">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                        <input
                            type="text"
                            placeholder="Search files..."
                            className="w-full bg-white border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                        />
                    </div>
                </div>

                {/* Main Action - New File */}
                <div className="p-4 md:p-3 lg:p-6">
                    <Link
                        href="/upload"
                        onClick={() => closeSidebar()}
                        className={cn(
                            "flex items-center justify-center gap-2 bg-primary hover:bg-blue-600 text-white font-medium transition-all shadow-lg hover:shadow-blue-500/25",
                            // Mobile: Sticky bottom prominent CTA is handled in mobile-only section below, 
                            // this one is for Desktop/Tablet top placement
                            "rounded-xl py-3 w-full",
                            // Tablet: Icon only
                            "md:w-12 md:h-12 md:p-0 lg:w-full lg:h-auto lg:py-3 lg:px-4"
                        )}
                        title="New Upload"
                    >
                        <Plus size={24} strokeWidth={2.5} />
                        <span className="md:hidden lg:inline">New Upload</span>
                    </Link>
                </div>

                {/* Navigation Items */}
                <div className="flex-1 overflow-y-auto overflow-x-hidden py-2 px-3 space-y-1">
                    {/* Recent Files Label */}
                    <div className="flex items-center justify-between px-2 mb-2">
                        <div className="md:hidden lg:block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                            Recent Uploads
                        </div>
                        {recentUploads.length > 0 && (
                            <Link
                                href="/history"
                                onClick={() => closeSidebar()}
                                className="md:hidden lg:block text-xs text-primary hover:text-blue-600 font-medium transition-colors"
                            >
                                View All
                            </Link>
                        )}
                    </div>

                    {/* Recent Files List */}
                    <div className="space-y-1 md:space-y-3 lg:space-y-1">
                        {recentUploads.length === 0 ? (
                            <div className="px-2 py-8 text-center md:hidden lg:block">
                                <p className="text-sm text-slate-400">No recent uploads</p>
                                <p className="text-xs text-slate-300 mt-1">Upload a file to get started</p>
                            </div>
                        ) : (
                            recentUploads.map((upload) => (
                                <button
                                    key={upload.jobId}
                                    onClick={() => handleRecentUploadClick(upload.jobId, upload.status)}
                                    className={cn(
                                        "flex items-center gap-3 w-full p-2 text-left rounded-lg transition-colors group relative",
                                        "hover:bg-white hover:shadow-sm md:justify-center lg:justify-start"
                                    )}
                                >
                                    <div className={cn(
                                        "w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 text-[10px] font-bold border border-transparent",
                                        getBadgeClass(upload.fileType)
                                    )}>
                                        {upload.fileType.toUpperCase()}
                                    </div>

                                    <div className="min-w-0 md:hidden lg:block flex-1">
                                        <div className="flex items-center gap-2">
                                            <div className="text-sm font-medium text-slate-700 truncate group-hover:text-primary">
                                                {upload.fileName}
                                            </div>
                                            {getStatusIcon(upload.status)}
                                        </div>
                                        <div className="text-xs text-slate-400">
                                            {getRelativeTime(upload.uploadedAt)}
                                        </div>
                                    </div>

                                    {/* Tablet Tooltip */}
                                    <div className="hidden md:block lg:hidden absolute left-full top-1/2 -translate-y-1/2 ml-3 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                                        {upload.fileName}
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </div>

                {/* Bottom Actions */}
                <div className="p-4 border-t border-slate-200 mt-auto bg-slate-50/50">
                    <button className={cn(
                        "flex items-center gap-3 w-full p-2 text-slate-600 hover:text-slate-900 hover:bg-white rounded-lg transition-all group relative",
                        "md:justify-center lg:justify-start"
                    )}>
                        <Settings size={20} />
                        <span className="md:hidden lg:inline font-medium">Settings</span>

                        {/* Tablet Tooltip */}
                        <div className="hidden md:block lg:hidden absolute left-full top-1/2 -translate-y-1/2 ml-3 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                            Settings
                        </div>
                    </button>

                    {/* Mobile Only: Extra CTA space filler if needed or version info */}
                    <div className="md:hidden mt-4 text-center text-xs text-slate-400">
                        v1.0.2 · DataPilot AI
                    </div>
                </div>
            </aside>
        </>
    );
}
