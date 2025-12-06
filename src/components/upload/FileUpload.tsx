"use client";

import React, { useCallback, useState } from 'react';

// Prompt didn't mention react-dropzone. I'll use standard HTML5 API or install it.
// "OnDrop: parse CSV/XLSX".
// I'll use standard DragEvent to avoid extra dependency if not requested, but react-dropzone is safer.
// I will implement manual DnD to keep dependencies low as per initial plan which didn't verify react-dropzone.
// But I can implement a nice one.

import { Upload, FileText, FileSpreadsheet, FileJson } from 'lucide-react';
import { cn } from '@/lib/utils';
import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import { useAppStore } from '@/lib/store';
import { Button } from '@/components/ui/button';

export default function FileUpload() {
    const [isDragActive, setIsDragActive] = useState(false);
    const setFile = useAppStore(s => s.setFile);
    const setPreview = useAppStore(s => s.setPreviewData);

    const processFile = useCallback((file: File) => {
        setFile(file);

        // Parse Preview
        if (file.name.endsWith('.csv')) {
            Papa.parse(file, {
                preview: 10,
                header: true,
                complete: (results) => {
                    setPreview(
                        results.data,
                        results.meta.fields || [],
                        0
                    );
                }
            });
        } else if (file.name.endsWith('.xlsx')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const data = e.target?.result;
                const workbook = XLSX.read(data, { type: 'binary' });
                const sheetName = workbook.SheetNames[0];
                const sheet = workbook.Sheets[sheetName];
                const json = XLSX.utils.sheet_to_json(sheet, { header: 1 });
                const headers = json[0] as string[];
                const rows = json.slice(1, 11).map(row => {
                    const obj: any = {};
                    headers.forEach((h, i) => obj[h] = (row as any)[i]);
                    return obj;
                });
                setPreview(rows, headers, 0);
            };
            reader.readAsBinaryString(file);
        } else if (file.name.endsWith('.json')) {
            // Handle JSON file preview
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const text = e.target?.result as string;
                    const jsonData = JSON.parse(text);

                    // Handle array of objects
                    if (Array.isArray(jsonData)) {
                        const preview = jsonData.slice(0, 10);
                        const headers = preview.length > 0 ? Object.keys(preview[0]) : [];
                        setPreview(preview, headers, jsonData.length);
                    }
                    // Handle single object - wrap in array
                    else if (typeof jsonData === 'object' && jsonData !== null) {
                        const headers = Object.keys(jsonData);
                        setPreview([jsonData], headers, 1);
                    }
                    // Handle other JSON types
                    else {
                        setPreview(
                            [{ value: jsonData }],
                            ['value'],
                            1
                        );
                    }
                } catch (error) {
                    console.error('Failed to parse JSON:', error);
                    // Show error preview
                    setPreview(
                        [{ error: 'Invalid JSON file', details: String(error) }],
                        ['error', 'details'],
                        0
                    );
                }
            };
            reader.readAsText(file);
        } else if (file.name.endsWith('.pdf')) {
            // Handle PDF file preview - show file info
            // Note: Full PDF parsing happens on the backend
            const fileSizeKB = (file.size / 1024).toFixed(2);
            const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
            const sizeDisplay = file.size > 1024 * 1024 ? `${fileSizeMB} MB` : `${fileSizeKB} KB`;

            setPreview(
                [
                    {
                        property: 'File Name',
                        value: file.name
                    },
                    {
                        property: 'File Size',
                        value: sizeDisplay
                    },
                    {
                        property: 'File Type',
                        value: 'PDF Document'
                    },
                    {
                        property: 'Last Modified',
                        value: new Date(file.lastModified).toLocaleString()
                    },
                    {
                        property: 'Status',
                        value: 'Ready for upload - Tables will be extracted on server'
                    }
                ],
                ['property', 'value'],
                5
            );
        }
    }, [setFile, setPreview]);

    const onDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragActive(true);
    };

    const onDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragActive(false);
    };

    const onDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            processFile(e.dataTransfer.files[0]);
        }
    };

    const onFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            processFile(e.target.files[0]);
        }
    };

    return (
        <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            className={cn(
                "relative group cursor-pointer flex flex-col items-center justify-center w-full min-h-[320px] rounded-3xl border-2 border-dashed transition-all duration-300 ease-out overflow-hidden hover:border-primary/50",
                isDragActive
                    ? "border-primary bg-primary/5 scale-[1.01] shadow-2xl shadow-primary/10"
                    : "border-slate-300 bg-slate-50/50"
            )}
            role="button"
            tabIndex={0}
            aria-label="Upload file area. Drag and drop or click to browse."
            onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    document.getElementById('file-upload-input')?.click();
                }
            }}
        >
            <div className="z-20 flex flex-col items-center space-y-6 text-center p-6 w-full max-w-lg mx-auto">
                <div className={cn(
                    "w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300",
                    isDragActive ? "bg-white shadow-xl scale-110" : "bg-white shadow-soft"
                )}>
                    <Upload className={cn("w-10 h-10 transition-colors", isDragActive ? "text-primary" : "text-slate-400")} />
                </div>

                <div className="space-y-3 w-full">
                    <h3 className="text-xl md:text-2xl font-semibold text-slate-800">
                        {isDragActive ? "Drop to upload" : "Upload Data File"}
                    </h3>

                    {/* Desktop Hint */}
                    <p className="hidden md:block text-slate-500">
                        Drag & drop your CSV, Excel, or PDF here, or click to browse.
                    </p>

                    {/* Mobile Button - Prominent CTA */}
                    <div className="md:hidden w-full px-4">
                        <Button
                            className="w-full h-12 text-base font-medium shadow-lg shadow-primary/20"
                            variant="default"
                        >
                            Browse Files
                        </Button>
                        <p className="mt-3 text-xs text-slate-400">
                            Supports CSV, Excel, PDF, JSON
                        </p>
                    </div>
                </div>

                {/* Icons - Desktop only to reduce mobile clutter */}
                <div className="hidden md:flex gap-6 mt-2 text-slate-300">
                    <div className="flex flex-col items-center gap-1">
                        <FileText size={24} />
                        <span className="text-[10px] uppercase font-bold tracking-wider">CSV</span>
                    </div>
                    <div className="flex flex-col items-center gap-1">
                        <FileSpreadsheet size={24} />
                        <span className="text-[10px] uppercase font-bold tracking-wider">Excel</span>
                    </div>
                    <div className="flex flex-col items-center gap-1">
                        <FileJson size={24} />
                        <span className="text-[10px] uppercase font-bold tracking-wider">JSON</span>
                    </div>
                </div>
            </div>

            {/* Decorative Grid */}
            <div className="absolute inset-0 pointer-events-none opacity-[0.03] z-0"
                style={{ backgroundImage: 'radial-gradient(circle, #000 1px, transparent 1px)', backgroundSize: '20px 20px' }}
            />

            <input
                id="file-upload-input"
                type="file"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-30"
                onChange={onFileInput}
                accept=".csv,.xlsx,.xls,.json,.pdf"
                title="Upload file"
            />
        </div>
    );
}
