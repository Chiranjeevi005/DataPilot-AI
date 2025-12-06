'use client';

import React from 'react';
import NavBar from '@/components/NavBar';
import Sidebar from '@/components/Sidebar';
import { useSidebarStore } from '@/lib/store';
import { clsx } from 'clsx';
import { EvidenceHighlightProvider } from '@/components/results/EvidenceHighlightContext';
import KpiCard from '@/components/results/KpiCard';
import LineChartCard from '@/components/results/LineChartCard';
import BarChartCard from '@/components/results/BarChartCard';
import DonutChartCard from '@/components/results/DonutChartCard';
import InsightsPanel from '@/components/results/InsightsPanel';
import DataPreviewTable from '@/components/results/DataPreviewTable';
import { Share2, Download, Gauge } from 'lucide-react';

// Mock Data
const MOCK_KPIS = [
    {
        title: 'Total Revenue',
        value: '$124.5k',
        delta: '+12%',
        deltaType: 'pos' as const,
        progressValue: 78,
        sparklineData: Array.from({ length: 10 }).map((_, i) => ({ value: 100 + Math.random() * 50 }))
    },
    {
        title: 'Total Orders',
        value: '1,204',
        delta: '-5%',
        deltaType: 'neg' as const,
        progressValue: 65,
        sparklineData: Array.from({ length: 10 }).map((_, i) => ({ value: 50 + Math.random() * 20 }))
    },
    {
        title: 'Avg Order Value',
        value: '$103.4',
        delta: '+2.4%',
        deltaType: 'pos' as const,
        progressValue: 45,
        sparklineData: Array.from({ length: 10 }).map((_, i) => ({ value: 90 + Math.random() * 10 }))
    },
    {
        title: 'Active Regions',
        value: '12',
        delta: '0%',
        deltaType: 'neutral' as const,
        progressValue: 100,
        sparklineData: Array.from({ length: 10 }).map((_, i) => ({ value: 12 }))
    }
];

const LINE_CHART_DATA = [
    { month: 'Jan', value: 4000 },
    { month: 'Feb', value: 3000 },
    { month: 'Mar', value: 2000 },
    { month: 'Apr', value: 2780 },
    { month: 'May', value: 1890 },
    { month: 'Jun', value: 9500 }, // Spike
    { month: 'Jul', value: 3490 },
    { month: 'Aug', value: 2000 },
    { month: 'Sep', value: 5000 },
    { month: 'Oct', value: 6000 },
    { month: 'Nov', value: 7000 },
    { month: 'Dec', value: 8000 },
];

const ANNOTATIONS = [
    { x: 'Jun', y: 9500, label: 'Spike' },
    { x: 'May', y: 1890, label: 'Dip' }
];

const BAR_DATA = [
    { name: 'Electronics', value: 45000 },
    { name: 'Home', value: 32000 },
    { name: 'Fashion', value: 28000 },
    { name: 'Sports', value: 15000 },
    { name: 'Books', value: 8000 },
];

const DONUT_DATA = [
    { name: 'North', value: 35 },
    { name: 'South', value: 25 },
    { name: 'East', value: 20 },
    { name: 'West', value: 20 },
];

export default function ResultsPage() {
    const isOpen = useSidebarStore((state) => state.isOpen);

    return (
        <EvidenceHighlightProvider>
            <div className="min-h-screen bg-datapilot-page font-sans text-datapilot-text selection:bg-datapilot-primary/20 flex pt-16 relative">
                <NavBar />
                <Sidebar />

                <main className={clsx("flex-1 px-4 sm:px-6 md:px-8 xl:px-12 py-6 md:py-8 transition-all duration-300 max-w-[1600px] mx-auto w-full", isOpen ? "md:ml-20 lg:ml-72" : "ml-0")}>

                    {/* Page Header */}
                    <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
                        <div>
                            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-datapilot-text mb-2 animate-in fade-in slide-in-from-bottom-2 duration-500">
                                Analysis Results
                            </h1>
                            <p className="text-datapilot-muted text-lg animate-in fade-in slide-in-from-bottom-3 duration-500 delay-100">
                                AI-generated insights and visualization for your dataset.
                            </p>
                        </div>

                        <div className="flex items-center gap-4 animate-in fade-in slide-in-from-right-4 duration-500 delay-200">
                            {/* Data Quality Score Pill */}
                            <div className="bg-white rounded-full border border-datapilot-border shadow-sm px-4 py-2 flex items-center gap-3">
                                <div className="relative w-10 h-10 flex items-center justify-center">
                                    <Gauge className="w-6 h-6 text-datapilot-primary" />
                                    {/* Radial micro chart simulated by generic Gauge icon for now or SVG circle */}
                                    <svg className="absolute inset-0 w-full h-full -rotate-90">
                                        <circle cx="20" cy="20" r="18" stroke="#E6E9EE" strokeWidth="3" fill="none" />
                                        <circle cx="20" cy="20" r="18" stroke="#00A3FF" strokeWidth="3" fill="none" strokeDasharray="113" strokeDashoffset="20" strokeLinecap="round" />
                                    </svg>
                                </div>
                                <div>
                                    <div className="text-[10px] uppercase font-bold text-datapilot-muted leading-tight">Data Quality</div>
                                    <div className="text-xl font-bold text-datapilot-text leading-tight">92<span className="text-sm font-normal text-datapilot-muted">/100</span></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-12 gap-6 lg:gap-8">

                        {/* Left Column (8 cols) */}
                        <div className="col-span-12 lg:col-span-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">

                            {/* KPI Row */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
                                {MOCK_KPIS.map((kpi, idx) => (
                                    <KpiCard key={idx} {...kpi} />
                                ))}
                            </div>

                            {/* Primary Chart: Sales Trend */}
                            <LineChartCard
                                data={LINE_CHART_DATA}
                                xKey="month"
                                yKey="value"
                                annotations={ANNOTATIONS}
                            />

                            {/* Secondary Charts row */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <BarChartCard data={BAR_DATA} xKey="name" yKey="value" />
                                <DonutChartCard data={DONUT_DATA} />
                            </div>

                            {/* Data Preview */}
                            <DataPreviewTable />

                        </div>

                        {/* Right Column (4 cols) - Sticky */}
                        <div className="col-span-12 lg:col-span-4 relative animate-in fade-in slide-in-from-right-4 duration-700 delay-300">
                            {/* Sticky Container - Fixed height to viewport minus header/padding */}
                            <div className="sticky top-24 h-[calc(100vh-120px)] flex flex-col gap-4">

                                {/* AI Insights - Takes remaining space and scrolls internally */}
                                <div className="flex-1 min-h-0">
                                    <InsightsPanel />
                                </div>

                                {/* Fixed items at bottom */}
                                <div className="shrink-0 space-y-4">
                                    <div className="flex gap-3 pt-2 border-t border-datapilot-border/50">
                                        <button className="flex-1 flex items-center justify-center gap-2 bg-datapilot-primary text-white font-semibold py-2.5 rounded-lg hover:bg-blue-600 transition-shadow shadow-md hover:shadow-lg text-sm">
                                            <Download className="w-4 h-4" /> Download PDF
                                        </button>
                                        <button className="flex items-center justify-center gap-2 bg-white text-datapilot-text font-medium py-2.5 px-4 rounded-lg border border-datapilot-border hover:bg-slate-50 transition-colors shadow-sm hover:shadow-md text-sm">
                                            <Share2 className="w-4 h-4" /> Share
                                        </button>
                                    </div>
                                </div>

                            </div>
                        </div>

                    </div>

                </main>
            </div>
        </EvidenceHighlightProvider>
    );
}
