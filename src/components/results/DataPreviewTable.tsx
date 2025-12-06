'use client';

import React, { useRef, useEffect, useState } from 'react';
import { clsx } from 'clsx';
import { Search, StretchHorizontal, Maximize2, AlertCircle } from 'lucide-react';
import { useEvidenceHighlight } from './EvidenceHighlightContext';
import { useToast } from '../ui/ToastContext';

interface DataPreviewTableProps {
    data?: any[];
}

// Mock 10 rows if no data provided, or allow realistic data
const MOCK_DATA = Array.from({ length: 15 }).map((_, i) => ({
    id: i,
    date: '2025-06-12',
    category: i % 2 === 0 ? 'Electronics' : 'Home',
    region: ['North', 'South', 'East', 'West'][i % 4],
    sales: (Math.random() * 1000).toFixed(2),
    units: Math.floor(Math.random() * 50),
    status: i === 2 ? 'Pending' : 'Completed' // referencing mock insight row 2
}));

export default function DataPreviewTable({ data = MOCK_DATA }: DataPreviewTableProps) {
    const { highlightedRowIndex, clearHighlight } = useEvidenceHighlight();
    const { showToast } = useToast();
    const tableRef = useRef<HTMLDivElement>(null);
    const [viewMode, setViewMode] = useState<'table' | 'card'>('table');
    const columns = ['Date', 'Category', 'Region', 'Sales', 'Units', 'Status'];
    const [qualityState, setQualityState] = useState(columns.map((_, i) => (i === 4 ? 'warning' : 'good')));

    // Auto-scroll to highlight
    useEffect(() => {
        if (highlightedRowIndex !== null && tableRef.current && viewMode === 'table') {
            const row = tableRef.current.querySelector(`[data-row-index="${highlightedRowIndex}"]`);
            if (row) {
                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }, [highlightedRowIndex, viewMode]);

    const handleFix = () => {
        showToast("Auto-fixing data quality issues...", "info");
        setTimeout(() => {
            setQualityState(prev => prev.map(() => 'good'));
            showToast("Issues resolved! 2 columns cleaned.", "success");
        }, 1000);
    };

    const handleIgnore = () => {
        showToast("Quality warnings ignored.", "info");
    };

    return (
        <div className="bg-datapilot-card rounded-[12px] shadow-soft border border-datapilot-border flex flex-col transition-all hover:shadow-card-hover overflow-hidden">

            {/* Header Toolbar */}
            <div className="p-4 border-b border-datapilot-border flex justify-between items-center bg-slate-50/50">
                <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-datapilot-text">Data Preview</h3>
                    <span className="text-xs text-datapilot-muted font-mono bg-white px-2 py-0.5 rounded border border-datapilot-border">{data.length} rows</span>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setViewMode(viewMode === 'table' ? 'card' : 'table')}
                        className={clsx("flex items-center text-xs font-medium px-3 py-1.5 border rounded-lg shadow-sm transition-colors",
                            viewMode === 'card' ? "bg-datapilot-primary text-white border-transparent" : "bg-white text-datapilot-muted hover:text-datapilot-primary border-datapilot-border"
                        )}
                    >
                        <StretchHorizontal className="w-3 h-3 mr-1.5" /> {viewMode === 'table' ? 'Card View' : 'Table View'}
                    </button>
                    <button
                        onClick={() => showToast("Full Screen Table not implemented in demo.", "info")}
                        className="flex items-center text-xs font-medium text-white bg-datapilot-primary hover:bg-blue-600 px-3 py-1.5 rounded-lg shadow-sm transition-colors"
                    >
                        <Maximize2 className="w-3 h-3 mr-1.5" /> Full Table
                    </button>
                </div>
            </div>

            {/* Content Container */}
            <div className="relative overflow-auto max-h-[400px] custom-scrollbar min-h-[300px]" ref={tableRef}>
                {viewMode === 'table' ? (
                    <table className="w-full text-left text-sm whitespace-nowrap">
                        <thead className="bg-slate-50 sticky top-0 z-10 shadow-sm">
                            <tr>
                                <th className="w-10 px-4 py-3 border-b border-datapilot-border"></th>
                                <th className="px-4 py-3 font-semibold text-datapilot-muted text-xs uppercase tracking-wider border-b border-datapilot-border">Row #</th>
                                {columns.map(col => (
                                    <th key={col} className="px-4 py-3 font-semibold text-datapilot-muted text-xs uppercase tracking-wider border-b border-datapilot-border">
                                        {col}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-datapilot-border">
                            {data.map((row, idx) => {
                                const isHighlighted = highlightedRowIndex === idx;
                                return (
                                    <tr
                                        key={idx}
                                        data-row-index={idx}
                                        className={clsx(
                                            "transition-colors hover:bg-slate-50/80 group cursor-pointer",
                                            isHighlighted && "highlight-row"
                                        )}
                                        onClick={() => {
                                            isHighlighted && clearHighlight();
                                            showToast(`Row ${idx} selected`, 'info');
                                        }}
                                    >
                                        <td className="px-4 py-3 text-center">
                                            {isHighlighted && <div className="w-2 h-2 rounded-full bg-datapilot-orange mx-auto animate-pulse" />}
                                            {!isHighlighted && <Search className="w-3 h-3 text-slate-300 opacity-0 group-hover:opacity-100 mx-auto cursor-pointer" />}
                                        </td>
                                        <td className="px-4 py-3 text-datapilot-muted font-mono text-xs">{idx}</td>
                                        <td className="px-4 py-3 text-datapilot-text">{row.date}</td>
                                        <td className="px-4 py-3 text-datapilot-text">{row.category}</td>
                                        <td className="px-4 py-3 text-datapilot-text">{row.region}</td>
                                        <td className="px-4 py-3 font-semibold text-datapilot-text">${row.sales}</td>
                                        <td className="px-4 py-3 text-datapilot-text text-center">{row.units}</td>
                                        <td className="px-4 py-3">
                                            <span className={clsx(
                                                "px-2 py-0.5 rounded-full text-[10px] font-bold uppercase",
                                                row.status === 'Completed' ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                                            )}>
                                                {row.status}
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                ) : (
                    <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {data.map((row, idx) => (
                            <div key={idx} className={clsx("bg-white p-4 rounded-lg border shadow-sm hover:shadow-md transition-all", highlightedRowIndex === idx && "ring-2 ring-datapilot-orange")}>
                                <div className="flex justify-between mb-2">
                                    <span className="text-xs font-mono text-datapilot-muted">Row {idx}</span>
                                    <span className={clsx("text-[10px] px-2 rounded-full", row.status === 'Completed' ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800")}>{row.status}</span>
                                </div>
                                <div className="space-y-1">
                                    <div className="flex justify-between text-sm"><span className="text-slate-500">Date:</span> <span>{row.date}</span></div>
                                    <div className="flex justify-between text-sm"><span className="text-slate-500">Category:</span> <span>{row.category}</span></div>
                                    <div className="flex justify-between text-sm"><span className="text-slate-500">Sales:</span> <span className="font-semibold">${row.sales}</span></div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Data Quality Strip */}
            <div className="bg-slate-50 border-t border-datapilot-border p-2 px-4 flex gap-6 overflow-x-auto custom-scrollbar">
                <div className="flex items-center gap-2 text-xs font-medium text-datapilot-text shrink-0">
                    <span className="text-datapilot-muted uppercase text-[10px]">Data Quality:</span>
                </div>
                {columns.map((col, i) => {
                    const hasIssue = qualityState[i] === 'warning';
                    return (
                        <div key={col} className="flex items-center gap-1.5 shrink-0 group cursor-pointer hover:bg-white px-2 py-1 rounded transition-colors" onClick={() => hasIssue && showToast(`Issue in ${col}: Missing values`, 'error')}>
                            <div className={clsx("w-2 h-2 rounded-full", hasIssue ? "bg-datapilot-orange" : "bg-datapilot-success")} />
                            <span className="text-xs text-datapilot-muted group-hover:text-datapilot-text">{col}</span>
                            {hasIssue && <AlertCircle className="w-3 h-3 text-datapilot-orange" />}
                        </div>
                    );
                })}
                <div className="ml-auto flex gap-2">
                    <button onClick={handleFix} className="text-[10px] bg-white border border-datapilot-border px-2 py-1 rounded text-datapilot-muted hover:text-datapilot-primary transition-colors">Fix</button>
                    <button onClick={handleIgnore} className="text-[10px] bg-white border border-datapilot-border px-2 py-1 rounded text-datapilot-muted hover:text-datapilot-text transition-colors">Ignore</button>
                </div>
            </div>
        </div>
    );
}
