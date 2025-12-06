"use client";

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
    FileText,
    CheckCircle2,
    Loader2,
    AlertCircle,
    Trash2,
    ExternalLink,
    Clock
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function RecentUploadsPanel() {
    const recentUploads = useAppStore((state) => state.recentUploads);
    const clearRecentUploads = useAppStore((state) => state.clearRecentUploads);
    const router = useRouter();

    const getBadgeClass = (type: string) => {
        if (type === 'csv') return 'text-emerald-700 bg-emerald-100 border-emerald-200';
        if (type === 'pdf') return 'text-rose-700 bg-rose-100 border-rose-200';
        if (type === 'xlsx') return 'text-blue-700 bg-blue-100 border-blue-200';
        return 'text-amber-700 bg-amber-100 border-amber-200';
    };

    const getStatusIcon = (status: 'processing' | 'completed' | 'error') => {
        switch (status) {
            case 'processing':
                return <Loader2 size={16} className="text-blue-500 animate-spin" />;
            case 'completed':
                return <CheckCircle2 size={16} className="text-green-500" />;
            case 'error':
                return <AlertCircle size={16} className="text-red-500" />;
        }
    };

    const getStatusText = (status: 'processing' | 'completed' | 'error') => {
        switch (status) {
            case 'processing':
                return 'Processing...';
            case 'completed':
                return 'Completed';
            case 'error':
                return 'Failed';
        }
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

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const handleUploadClick = (jobId: string, status: 'processing' | 'completed' | 'error') => {
        if (status === 'completed') {
            router.push(`/results?jobId=${jobId}`);
        } else if (status === 'processing') {
            router.push(`/loading?jobId=${jobId}`);
        } else {
            router.push(`/upload`);
        }
    };

    const handleClearAll = () => {
        if (confirm('Are you sure you want to clear all recent uploads? This action cannot be undone.')) {
            clearRecentUploads();
        }
    };

    return (
        <Card className="w-full">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                <CardTitle className="text-2xl font-bold">
                    Recent Uploads
                    <span className="ml-2 text-sm font-normal text-slate-500">
                        ({recentUploads.length} {recentUploads.length === 1 ? 'upload' : 'uploads'})
                    </span>
                </CardTitle>
                {recentUploads.length > 0 && (
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleClearAll}
                        className="text-slate-500 hover:text-red-600"
                    >
                        <Trash2 size={16} className="mr-2" />
                        Clear All
                    </Button>
                )}
            </CardHeader>
            <CardContent>
                {recentUploads.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                            <FileText size={32} className="text-slate-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-700 mb-2">No recent uploads</h3>
                        <p className="text-sm text-slate-500 mb-6 max-w-sm">
                            Upload your first file to start analyzing your data with AI-powered insights.
                        </p>
                        <Button
                            onClick={() => router.push('/upload')}
                            className="bg-primary hover:bg-blue-600"
                        >
                            Upload File
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {recentUploads.map((upload) => (
                            <div
                                key={upload.jobId}
                                className="group relative flex items-center gap-4 p-4 rounded-lg border border-slate-200 hover:border-primary/50 hover:bg-slate-50 transition-all cursor-pointer"
                                onClick={() => handleUploadClick(upload.jobId, upload.status)}
                            >
                                {/* File Type Badge */}
                                <div className={cn(
                                    "w-12 h-12 rounded-lg flex items-center justify-center text-xs font-bold border flex-shrink-0",
                                    getBadgeClass(upload.fileType)
                                )}>
                                    {upload.fileType.toUpperCase()}
                                </div>

                                {/* File Info */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <h4 className="font-semibold text-slate-800 truncate">
                                            {upload.fileName}
                                        </h4>
                                        {getStatusIcon(upload.status)}
                                    </div>
                                    <div className="flex items-center gap-3 text-xs text-slate-500">
                                        <span className="flex items-center gap-1">
                                            <Clock size={12} />
                                            {getRelativeTime(upload.uploadedAt)}
                                        </span>
                                        <span>•</span>
                                        <span>{formatFileSize(upload.fileSize)}</span>
                                        <span>•</span>
                                        <span className={cn(
                                            "font-medium",
                                            upload.status === 'completed' && "text-green-600",
                                            upload.status === 'processing' && "text-blue-600",
                                            upload.status === 'error' && "text-red-600"
                                        )}>
                                            {getStatusText(upload.status)}
                                        </span>
                                    </div>
                                </div>

                                {/* Action Icon */}
                                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                                    <ExternalLink size={18} className="text-slate-400" />
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
