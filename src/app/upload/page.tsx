"use client";

import FileUpload from '@/components/upload/FileUpload';
import FileSummaryCard from '@/components/upload/FileSummaryCard';
import PreviewTable from '@/components/upload/PreviewTable';
import { useAppStore } from '@/lib/store';
import NavBar from '@/components/NavBar';
import Sidebar from '@/components/Sidebar';

export default function UploadPage() {
    const file = useAppStore((state) => state.file);

    return (
        <div className="min-h-screen bg-background font-sans text-slate-900">
            <Sidebar />
            <NavBar />

            <main className="pt-24 pl-4 pr-4 lg:pl-[300px] lg:pr-8 py-10 transition-all duration-300">
                <div className="max-w-6xl mx-auto space-y-8">

                    <div className="space-y-2">
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">New Analysis</h1>
                        <p className="text-slate-500">Upload your raw data to generate AI-powered insights instantly.</p>
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
            </main>
        </div>
    );
}
