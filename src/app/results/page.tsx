'use client';

import React, { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import NavBar from '@/components/NavBar';
import Sidebar from '@/components/Sidebar';
import { useSidebarStore } from '@/lib/store';
import { useResultStore } from '@/store/resultStore';
import { clsx } from 'clsx';
import { EvidenceHighlightProvider } from '@/components/results/EvidenceHighlightContext';
import KpiCard from '@/components/results/KpiCard';
import LineChartCard from '@/components/results/LineChartCard';
import BarChartCard from '@/components/results/BarChartCard';
import DonutChartCard from '@/components/results/DonutChartCard';
import InsightsPanel from '@/components/results/InsightsPanel';
import DataPreviewTable from '@/components/results/DataPreviewTable';
import { Share2, Download, Gauge, RefreshCcw, AlertTriangle } from 'lucide-react';

export default function ResultsPage() {
    const isOpen = useSidebarStore((state) => state.isOpen);
    const searchParams = useSearchParams();
    const jobId = searchParams.get('jobId');

    const {
        loading,
        error,
        result,
        fetchResult,
        retry
    } = useResultStore();

    useEffect(() => {
        if (jobId) {
            fetchResult(jobId);
        }
    }, [jobId, fetchResult]);

    // Retry Handler
    const handleRetry = () => {
        retry(); // Clear error
        if (jobId) fetchResult(jobId);
    };

    // Derived States
    const kpis = result?.kpis || [];
    const qualityScore = result?.qualityScore ?? 0;

    // Sort logic handled in backend, but safe to default
    const analystInsights = result?.insightsAnalyst || [];
    const businessInsights = result?.insightsBusiness || [];

    // Chart Rendering
    const renderChart = (spec: any, idx: number) => {
        if (spec.type === 'line') {
            return (
                <LineChartCard
                    key={spec.id || idx}
                    data={spec.data}
                    xKey={spec.xKey || "date"}
                    yKey={spec.yKey || "value"}
                    title={spec.title}
                />
            );
        } else if (spec.type === 'bar') {
            return (
                <BarChartCard
                    key={spec.id || idx}
                    data={spec.data}
                    xKey={spec.xKey || "category"}
                    yKey={spec.yKey || "value"}
                    title={spec.title}
                />
            );
        } else if (spec.type === 'donut') {
            return (
                <DonutChartCard
                    key={spec.id || idx}
                    data={spec.data}
                    title={spec.title}
                    nameKey={spec.xKey || "category"}
                    dataKey={spec.yKey || "count"}
                />
            );
        }
        return null; // Unsupported chart type
    };

    return (
        <EvidenceHighlightProvider>
            <div className="min-h-screen bg-datapilot-page font-sans text-datapilot-text selection:bg-datapilot-primary/20 flex pt-16 relative">
                <NavBar />
                <Sidebar />

                <main className={clsx("flex-1 px-4 sm:px-6 md:px-8 xl:px-12 py-6 md:py-8 transition-all duration-300 max-w-[1600px] mx-auto w-full", isOpen ? "md:ml-20 lg:ml-72" : "ml-0")}>

                    {/* Loading State */}
                    {loading && (
                        <div className="flex flex-col items-center justify-center h-[60vh] space-y-4 animate-pulse">
                            <div className="w-16 h-16 border-4 border-datapilot-primary border-t-transparent rounded-full animate-spin"></div>
                            <h2 className="text-xl font-medium text-datapilot-text">Analyzing Dataset...</h2>
                            <p className="text-datapilot-muted">Generating AI insights, KPI metrics, and charts.</p>
                        </div>
                    )}

                    {/* Error State */}
                    {error && (
                        <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
                            <div className="bg-red-50 p-4 rounded-full border border-red-100">
                                <AlertTriangle className="w-8 h-8 text-red-500" />
                            </div>
                            <h2 className="text-xl font-bold text-datapilot-text">Analysis Failed</h2>
                            <p className="text-red-600 max-w-lg text-center">{error}</p>
                            <button
                                onClick={handleRetry}
                                className="mt-4 bg-datapilot-primary text-white px-6 py-2 rounded-lg hover:bg-blue-600 flex items-center gap-2"
                            >
                                <RefreshCcw className="w-4 h-4" /> Retry Analysis
                            </button>
                        </div>
                    )}

                    {/* Success State */}
                    {!loading && !error && result && (
                        <>
                            {/* Page Header */}
                            <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
                                <div>
                                    <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-datapilot-text mb-2 animate-in fade-in slide-in-from-bottom-2 duration-500">
                                        Analysis Results
                                    </h1>
                                    <p className="text-datapilot-muted text-lg animate-in fade-in slide-in-from-bottom-3 duration-500 delay-100">
                                        AI-generated insights and visualization for job {jobId?.substring(0, 8)}.
                                    </p>
                                </div>

                                <div className="flex items-center gap-4 animate-in fade-in slide-in-from-right-4 duration-500 delay-200">
                                    <div className="bg-white rounded-full border border-datapilot-border shadow-sm px-4 py-2 flex items-center gap-3">
                                        <div className="relative w-10 h-10 flex items-center justify-center">
                                            <Gauge className="w-6 h-6 text-datapilot-primary" />
                                            <svg className="absolute inset-0 w-full h-full -rotate-90">
                                                <circle cx="20" cy="20" r="18" stroke="#E6E9EE" strokeWidth="3" fill="none" />
                                                <circle
                                                    cx="20" cy="20" r="18"
                                                    stroke={qualityScore > 80 ? "#10B981" : "#F59E0B"}
                                                    strokeWidth="3" fill="none"
                                                    strokeDasharray="113"
                                                    strokeDashoffset={113 - (113 * qualityScore) / 100}
                                                    strokeLinecap="round"
                                                />
                                            </svg>
                                        </div>
                                        <div>
                                            <div className="text-[10px] uppercase font-bold text-datapilot-muted leading-tight">Data Quality</div>
                                            <div className="text-xl font-bold text-datapilot-text leading-tight">{qualityScore}<span className="text-sm font-normal text-datapilot-muted">/100</span></div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-12 gap-6 lg:gap-8">

                                {/* Left Column (8 cols) */}
                                <div className="col-span-12 lg:col-span-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">

                                    {/* KPI Row */}
                                    {kpis.length > 0 && (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
                                            {kpis.map((kpi, idx) => (
                                                <KpiCard
                                                    key={idx}
                                                    title={kpi.name}
                                                    value={String(kpi.value)}
                                                    delta={kpi.delta ? `${kpi.delta > 0 ? '+' : ''}${kpi.delta}%` : undefined}
                                                    deltaType={kpi.deltaType === 'negative' ? 'neg' : kpi.deltaType === 'positive' ? 'pos' : 'neutral'}
                                                    // Mock progress/sparkline for now as not in backend yet
                                                    progressValue={Math.random() * 100}
                                                />
                                            ))}
                                        </div>
                                    )}

                                    {/* Charts */}
                                    <div className="space-y-6">
                                        {/* Render Primary (Line) Charts specifically if any, or just map all? */}
                                        {/* Assuming first chart is primary for layout, others secondary */}
                                        {result.chartSpecs.slice(0, 1).map((spec, i) => renderChart(spec, i))}

                                        {result.chartSpecs.length > 1 && (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                {result.chartSpecs.slice(1).map((spec, i) => renderChart(spec, i + 1))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Data Preview */}
                                    <DataPreviewTable
                                        data={result.cleanedPreview}
                                        schema={result.schema}
                                    />

                                </div>

                                {/* Right Column (4 cols) - Sticky */}
                                <div className="col-span-12 lg:col-span-4 relative animate-in fade-in slide-in-from-right-4 duration-700 delay-300">
                                    <div className="sticky top-24 h-[calc(100vh-120px)] flex flex-col gap-4">

                                        <div className="flex-1 min-h-0">
                                            <InsightsPanel
                                                analystInsights={analystInsights}
                                                businessInsights={businessInsights}
                                            />
                                        </div>

                                        <div className="shrink-0 space-y-4">
                                            <div className="flex gap-3 pt-2 border-t border-datapilot-border/50">
                                                <button className="flex-1 flex items-center justify-center gap-2 bg-datapilot-primary text-white font-semibold py-2.5 rounded-lg hover:bg-blue-600 transition-shadow shadow-md hover:shadow-lg text-sm">
                                                    <Download className="w-4 h-4" /> Download Report
                                                </button>
                                                <button className="flex items-center justify-center gap-2 bg-white text-datapilot-text font-medium py-2.5 px-4 rounded-lg border border-datapilot-border hover:bg-slate-50 transition-colors shadow-sm hover:shadow-md text-sm">
                                                    <Share2 className="w-4 h-4" /> Share
                                                </button>
                                            </div>
                                        </div>

                                    </div>
                                </div>

                            </div>
                        </>
                    )}

                    {!loading && !error && !result && !jobId && (
                        <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
                            <h2 className="text-lg text-datapilot-muted">No Job ID provided.</h2>
                            <a href="/" className="text-datapilot-primary font-medium hover:underline">Start a new analysis</a>
                        </div>
                    )}
                </main>
            </div>
        </EvidenceHighlightProvider>
    );
}
