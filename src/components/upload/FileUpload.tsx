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
                        // We don't know total rows without streaming, but for preview 10 is enough.
                        // For total rows, we might need a full parse or just estimate. 
                        // Let's set 0 for now or results.data.length if small.
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
                "relative group cursor-pointer flex flex-col items-center justify-center w-full h-80 rounded-3xl border-2 border-dashed transition-all duration-300 ease-out",
                isDragActive
                    ? "border-primary bg-primary/5 scale-[1.01] shadow-2xl shadow-primary/10"
                    : "border-slate-300 bg-slate-50/50 hover:bg-slate-50 hover:border-primary/50"
            )}
        >


            <div className="z-10 flex flex-col items-center space-y-4 text-center p-6">
                <div className={cn(
                    "w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300",
                    isDragActive ? "bg-white shadow-xl scale-110" : "bg-white shadow-soft"
                )}>
                    <Upload className={cn("w-10 h-10 transition-colors", isDragActive ? "text-primary" : "text-slate-400")} />
                </div>

                <div className="space-y-2">
                    <h3 className="text-2xl font-semibold text-slate-800">
                        {isDragActive ? "Drop to upload" : "Upload Data File"}
                    </h3>
                    <p className="text-slate-500 max-w-sm">
                        Drag & drop your CSV, Excel, or PDF here, or click to browse.
                    </p>
                </div>

                <div className="flex gap-4 mt-4 text-slate-400">
                    <FileText size={24} />
                    <FileSpreadsheet size={24} />
                    <FileJson size={24} />
                </div>
            </div>

            {/* Decorative Grid */}
            <div className="absolute inset-0 pointer-events-none opacity-[0.03]"
                style={{ backgroundImage: 'radial-gradient(circle, #000 1px, transparent 1px)', backgroundSize: '20px 20px' }}
            />

            <input
                type="file"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-50"
                onChange={onFileInput}
                accept=".csv,.xlsx,.json,.pdf"
            />
        </div>
    );
}
