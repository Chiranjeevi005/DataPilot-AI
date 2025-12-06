"use client";

import React, { useState } from 'react';
import { useAppStore } from '@/lib/store';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileType, FileText, Database, Layers, ArrowRight, X } from 'lucide-react';
import axios from 'axios';
import { useRouter } from 'next/navigation';

export default function FileSummaryCard() {
    const {
        file, fileName, fileType, fileSize,
        previewColumns, previewRows, reset, startJob
    } = useAppStore();
    const router = useRouter();
    const [isUploading, setIsUploading] = useState(false);

    if (!file) return null;

    const handleRunAnalysis = async () => {
        setIsUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await axios.post('/api/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            startJob(response.data.jobId);
            router.push('/loading');
        } catch (error) {
            console.error("Upload failed", error);
            setIsUploading(false);
        }
    };

    const formatSize = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <Card className="w-full border-blue-100 shadow-lg shadow-blue-900/5 overflow-hidden">
            <div className="h-2 bg-gradient-to-r from-primary to-cyan-400" />
            <CardContent className="p-6">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl bg-blue-50 flex items-center justify-center text-primary">
                            <FileText size={28} />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-slate-800">{fileName}</h3>
                            <div className="flex items-center gap-3 text-sm text-slate-500 mt-1">
                                <span className="uppercase font-medium bg-slate-100 px-2 py-0.5 rounded text-xs tracking-wider">
                                    {fileType}
                                </span>
                                <span>{formatSize(fileSize)}</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-8 w-full md:w-auto p-4 bg-slate-50 rounded-xl border border-slate-100">
                        <div className="flex flex-col">
                            <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Columns</span>
                            <div className="flex items-center gap-2 mt-1">
                                <Layers size={16} className="text-secondary" />
                                <span className="text-lg font-bold text-slate-700">{previewColumns.length}</span>
                            </div>
                        </div>
                        <div className="w-px h-10 bg-slate-200" />
                        <div className="flex flex-col">
                            <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Detected Rows</span>
                            <div className="flex items-center gap-2 mt-1">
                                <Database size={16} className="text-primary" />
                                <span className="text-lg font-bold text-slate-700">
                                    {previewRows.length > 0 ? `${previewRows.length}+` : '0'}
                                    <span className="text-xs text-slate-400 font-normal ml-1">(Sample)</span>
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-3 w-full md:w-auto">
                        <Button variant="ghost" onClick={reset} className="text-slate-400 hover:text-red-500">
                            <X size={20} />
                        </Button>
                        <Button
                            onClick={handleRunAnalysis}
                            disabled={isUploading}
                            className="bg-primary hover:bg-blue-600 text-white shadow-glow px-8 rounded-full"
                        >
                            {isUploading ? 'Uploading...' : 'Run Analysis'}
                            {!isUploading && <ArrowRight size={18} className="ml-2" />}
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
