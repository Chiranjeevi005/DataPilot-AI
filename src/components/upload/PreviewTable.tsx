"use client";

import React, { useState } from 'react';
import { useAppStore } from '@/lib/store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table as TableIcon, LayoutList, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function PreviewTable() {
    const { previewRows, previewColumns, totalRows } = useAppStore();
    const [isCardView, setIsCardView] = useState(false);
    const [expandedRows, setExpandedRows] = useState<number[]>([]);

    if (!previewRows || previewRows.length === 0) return null;

    const toggleRow = (index: number) => {
        setExpandedRows(prev =>
            prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
        );
    };

    const renderValue = (value: any) => {
        if (value === null || value === undefined) return <span className="text-slate-300 italic">null</span>;
        if (typeof value === 'object') return JSON.stringify(value);
        return String(value);
    };

    return (
        <Card className="mt-8 border-none shadow-none bg-transparent">
            <CardHeader className="px-0 pt-0 pb-4 flex flex-row items-center justify-between">
                <div>
                    <CardTitle className="text-lg md:text-xl font-semibold text-slate-800">
                        Data Preview
                        <span className="ml-3 text-sm font-normal text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                            {totalRows > 0 ? `${Math.min(previewRows.length, totalRows)} of ${totalRows} rows` : `${previewRows.length} rows`}
                        </span>
                    </CardTitle>
                </div>

                {/* View Toggle (hidden on mobile, visible on tablet+) */}
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsCardView(!isCardView)}
                    className="hidden md:flex gap-2 text-slate-600 border-slate-300"
                >
                    {isCardView ? <TableIcon size={16} /> : <LayoutList size={16} />}
                    {isCardView ? "Table View" : "Card View"}
                </Button>
            </CardHeader>

            <CardContent className="p-0">
                {/* Mobile & Card View Layout */}
                <div className={cn("space-y-4", isCardView ? "block" : "md:hidden")}>
                    {previewRows.map((row, rowIndex) => {
                        const isExpanded = expandedRows.includes(rowIndex);
                        // Show first 3 columns as summary
                        const summaryCols = previewColumns.slice(0, 3);
                        const detailCols = previewColumns.slice(3);

                        return (
                            <div key={rowIndex} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                                {/* Card Header / Summary */}
                                <div className="p-4 space-y-2">
                                    {summaryCols.map((col, i) => (
                                        <div key={i} className="flex justify-between items-center text-sm">
                                            <span className="font-medium text-slate-500">{col}</span>
                                            <span className="font-semibold text-slate-800 max-w-[60%] truncate">
                                                {renderValue(row[col])}
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                {/* Expanded Details */}
                                {isExpanded && detailCols.length > 0 && (
                                    <div className="px-4 pb-4 space-y-2 border-t border-slate-50 bg-slate-50/50 pt-3 animate-in slide-in-from-top-2">
                                        {detailCols.map((col, i) => (
                                            <div key={i} className="flex justify-between items-start text-sm">
                                                <span className="font-medium text-slate-500 mt-0.5">{col}</span>
                                                <span className="text-slate-700 max-w-[60%] break-all text-right">
                                                    {renderValue(row[col])}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Expand Action */}
                                {detailCols.length > 0 && (
                                    <button
                                        onClick={() => toggleRow(rowIndex)}
                                        className="w-full py-2 bg-slate-50 text-xs font-medium text-slate-500 hover:text-primary hover:bg-slate-100 transition-colors flex items-center justify-center gap-1 border-t border-slate-100"
                                    >
                                        {isExpanded ? (
                                            <>Show Less <ChevronUp size={14} /></>
                                        ) : (
                                            <>Show All Columns <ChevronDown size={14} /></>
                                        )}
                                    </button>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Desktop Table View */}
                <div className={cn(
                    "hidden overflow-hidden rounded-xl border border-slate-200 shadow-sm bg-white",
                    !isCardView && "md:block"
                )}>
                    <div className="overflow-x-auto max-h-[600px] overflow-y-auto custom-scrollbar">
                        <table className="w-full text-sm text-left border-collapse">
                            <thead className="bg-slate-50 border-b border-slate-200 sticky top-0 z-20 shadow-sm">
                                <tr>
                                    {previewColumns.map((col, i) => (
                                        <th key={i} className="px-6 py-4 font-semibold text-slate-600 uppercase text-xs tracking-wider whitespace-nowrap bg-slate-50">
                                            {col}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {previewRows.map((row, i) => (
                                    <tr key={i} className="hover:bg-slate-50/80 transition-colors group">
                                        {previewColumns.map((col, j) => (
                                            <td
                                                key={j}
                                                className="px-6 py-3 text-slate-600 whitespace-nowrap max-w-[200px] truncate group-hover:text-slate-900"
                                                title={String(row[col])}
                                            >
                                                {renderValue(row[col])}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div className="bg-slate-50 p-3 text-center text-xs text-slate-400 font-medium border-t border-slate-200">
                        Displaying {previewRows.length} sample rows
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
