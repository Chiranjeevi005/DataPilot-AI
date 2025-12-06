"use client";

import React, { useEffect } from 'react';
import { useAppStore, useSidebarStore } from '@/lib/store';
import NavBar from '@/components/NavBar';
import Sidebar from '@/components/Sidebar';
import KpiCard from '@/components/results/KpiCard';
import ChartCard from '@/components/results/ChartCard';
import InsightPanel from '@/components/results/InsightPanel';
import { useRouter } from 'next/navigation';
import ResponsiveContainer from '@/components/ResponsiveContainer';
import { cn } from '@/lib/utils';

export default function ResultsPage() {
    const { results } = useAppStore();
    const isOpen = useSidebarStore((state) => state.isOpen);
    const router = useRouter();

    useEffect(() => {
        // If no results, redirect to upload
        if (!results) {
            // router.push('/upload'); // Commented out for dev ease to allow direct access if needed, OR mock init
            // For strict flow:
            // router.replace('/upload');
        }
    }, [results, router]);

    if (!results) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <p>No results found. Please start a new analysis.</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50/50 font-sans text-slate-900">
            <NavBar />
            <Sidebar />

            <main className={cn("pt-24 pb-12 transition-all duration-300 ease-in-out", isOpen ? "md:ml-20 lg:ml-72" : "ml-0")}>
                <ResponsiveContainer maxWidth="2xl">
                    <div className="space-y-8">

                        {/* Header */}
                        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight text-slate-900">Analysis Results</h1>
                                <p className="text-slate-500 mt-1">AI-generated insights and visualization for your dataset.</p>
                            </div>
                            <div className="flex items-center justify-between md:block md:text-right bg-white md:bg-transparent p-4 md:p-0 rounded-xl md:rounded-none shadow-sm md:shadow-none border md:border-none border-slate-200">
                                <div className="text-sm font-medium text-slate-500">Data Quality Score</div>
                                <div className="text-3xl font-bold text-emerald-600">{results.qualityScore}/100</div>
                            </div>
                        </div>

                        {/* KPIs */}
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
                            {results.kpis && results.kpis.map((kpi, i) => (
                                <KpiCard key={i} data={kpi} />
                            ))}
                        </div>

                        {/* Main Content Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Charts Section - Spans 2 cols */}
                            <div className="lg:col-span-2 space-y-8">
                                {results.chartSpecs && results.chartSpecs.map((spec) => (
                                    <ChartCard key={spec.id} spec={spec} />
                                ))}
                            </div>

                            {/* Insights Panel - Spans 1 col */}
                            <div className="lg:col-span-1">
                                <InsightPanel insights={results.insights || []} />
                            </div>
                        </div>

                    </div>
                </ResponsiveContainer>
            </main>
        </div>
    );
}
