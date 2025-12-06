"use client";

import React from 'react';
import { useAppStore } from '@/lib/store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function PreviewTable() {
    const { previewRows, previewColumns } = useAppStore();

    if (!previewRows || previewRows.length === 0) return null;

    return (
        <Card className="mt-8 border-none shadow-none bg-transparent">
            <CardHeader className="px-0 pt-0 pb-4">
                <CardTitle className="text-lg font-semibold text-slate-700">Data Preview</CardTitle>
            </CardHeader>
            <CardContent className="p-0 overflow-hidden rounded-xl border border-slate-200 shadow-sm bg-white">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-slate-50 border-b border-slate-200">
                            <tr>
                                {previewColumns.map((col, i) => (
                                    <th key={i} className="px-6 py-4 font-semibold text-slate-600 uppercase text-xs tracking-wider whitespace-nowrap">
                                        {col}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {previewRows.map((row, i) => (
                                <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                                    {previewColumns.map((col, j) => (
                                        <td key={j} className="px-6 py-3 text-slate-600 whitespace-nowrap max-w-[200px] truncate">
                                            {row[col]}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="bg-slate-50 p-3 text-center text-xs text-slate-400 font-medium">
                    Showing first {previewRows.length} rows for review
                </div>
            </CardContent>
        </Card>
    );
}
