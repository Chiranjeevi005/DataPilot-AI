"use client";

import FileUpload from '@/components/upload/FileUpload';
import FileSummaryCard from '@/components/upload/FileSummaryCard';
import PreviewTable from '@/components/upload/PreviewTable';
import { useAppStore, useSidebarStore } from '@/lib/store';
import NavBar from '@/components/NavBar';
import Sidebar from '@/components/Sidebar';
import ResponsiveContainer from '@/components/ResponsiveContainer';
import { cn } from '@/lib/utils';

export default function UploadPage() {
    const file = useAppStore((state) => state.file);
    const isOpen = useSidebarStore((state) => state.isOpen);

    return (
        <div className="min-h-screen bg-background font-sans text-slate-900">
            {/* Navbar first to ensure it's at the top of accessibility tree, 
                Sidebar second so its higher z-index (if any) naturally stacks on top 
                OR standard layout requires this order for visual layering if z-indices are equal */}
            <NavBar />
            <Sidebar />

            {/* Main Content Area */}
            <main className={cn("pt-24 pb-12 transition-all duration-300 ease-in-out", isOpen ? "md:ml-20 lg:ml-72" : "ml-0")}>
                <ResponsiveContainer maxWidth="2xl">
                    <div className="space-y-8">

                        <div className="space-y-2">
                            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">New Analysis</h1>
                            <p className="text-slate-500 text-lg">Upload your raw data to generate AI-powered insights instantly.</p>
                        </div>

                        {!file ? (
                            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                                <FileUpload />
                            </div>
                        ) : (
                            <div className="space-y-8 animate-in fade-in zoom-in-95 duration-300">
                                <FileSummaryCard />
                                <PreviewTable />
                            </div>
                        )}

                    </div>
                </ResponsiveContainer>
            </main>
        </div>
    );
}
