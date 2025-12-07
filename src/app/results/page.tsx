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


function ResultsPageContent() {
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

    // Download Report Handler - Enhanced Version
    const handleDownloadReport = async () => {
        if (!result) return;

        try {
            // Show loading indicator
            const button = document.querySelector('button[onclick*="handleDownloadReport"]') as HTMLButtonElement;
            const originalText = button?.innerHTML;
            if (button) {
                button.disabled = true;
                button.innerHTML = '<svg class="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Generating...';
            }

            // Dynamic imports
            const jsPDF = (await import('jspdf')).default;
            const html2canvas = (await import('html2canvas')).default;

            const doc = new jsPDF('p', 'mm', 'a4');
            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();
            const margin = 20;
            const contentWidth = pageWidth - (2 * margin);
            let yPos = margin;

            // Helper to add page break
            const addPageIfNeeded = (space: number) => {
                if (yPos + space > pageHeight - margin) {
                    doc.addPage();
                    yPos = margin;
                    return true;
                }
                return false;
            };

            // ===== COVER PAGE =====
            // Background gradient effect
            doc.setFillColor(37, 99, 235);
            doc.rect(0, 0, pageWidth, 80, 'F');

            // Title
            doc.setTextColor(255, 255, 255);
            doc.setFontSize(32);
            doc.setFont('helvetica', 'bold');
            doc.text('DataPilot AI', pageWidth / 2, 35, { align: 'center' });

            doc.setFontSize(18);
            doc.setFont('helvetica', 'normal');
            doc.text('Analysis Report', pageWidth / 2, 50, { align: 'center' });

            // Metadata box
            yPos = 100;
            doc.setFillColor(248, 250, 252);
            doc.roundedRect(margin, yPos, contentWidth, 40, 3, 3, 'F');

            doc.setTextColor(71, 85, 105);
            doc.setFontSize(10);
            doc.text('Report Details', margin + 5, yPos + 8);

            doc.setFontSize(9);
            doc.setTextColor(100, 116, 139);
            doc.text(`Generated: ${new Date().toLocaleString()}`, margin + 5, yPos + 16);
            doc.text(`Job ID: ${jobId || 'N/A'}`, margin + 5, yPos + 24);
            doc.text(`Quality Score: ${qualityScore}/100`, margin + 5, yPos + 32);

            // Quality Score Badge
            const scoreX = pageWidth - margin - 50;
            const scoreColor = qualityScore > 80 ? [16, 185, 129] : qualityScore > 60 ? [251, 191, 36] : [239, 68, 68];
            doc.setFillColor(scoreColor[0], scoreColor[1], scoreColor[2]);
            doc.circle(scoreX + 20, yPos + 20, 18, 'F');

            doc.setTextColor(255, 255, 255);
            doc.setFontSize(20);
            doc.setFont('helvetica', 'bold');
            doc.text(String(qualityScore), scoreX + 20, yPos + 24, { align: 'center' });
            doc.setFontSize(8);
            doc.text('/100', scoreX + 20, yPos + 30, { align: 'center' });

            yPos = 160;

            // ===== KEY METRICS SECTION =====
            addPageIfNeeded(60);
            doc.setFillColor(37, 99, 235);
            doc.rect(margin, yPos, contentWidth, 8, 'F');
            doc.setTextColor(255, 255, 255);
            doc.setFontSize(14);
            doc.setFont('helvetica', 'bold');
            doc.text('Key Performance Indicators', margin + 3, yPos + 6);
            yPos += 15;

            // Manual KPI Table (instead of autoTable)
            const tableStartY = yPos;
            const colWidth = contentWidth / 2;
            const rowHeight = 8;

            // Table header
            doc.setFillColor(71, 85, 105);
            doc.rect(margin, yPos, contentWidth, rowHeight, 'F');
            doc.setTextColor(255, 255, 255);
            doc.setFontSize(10);
            doc.setFont('helvetica', 'bold');
            doc.text('Metric', margin + 3, yPos + 5.5);
            doc.text('Value', margin + colWidth + 3, yPos + 5.5);
            yPos += rowHeight;

            // Table rows
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(9);
            kpis.slice(0, 6).forEach((kpi, idx) => {
                // Alternating row colors
                if (idx % 2 === 1) {
                    doc.setFillColor(248, 250, 252);
                    doc.rect(margin, yPos, contentWidth, rowHeight, 'F');
                }

                // Border
                doc.setDrawColor(200, 200, 200);
                doc.rect(margin, yPos, contentWidth, rowHeight, 'S');
                doc.line(margin + colWidth, yPos, margin + colWidth, yPos + rowHeight);

                // Text
                doc.setTextColor(60, 60, 60);
                doc.text(kpi.name, margin + 3, yPos + 5.5);
                doc.text(String(kpi.value), margin + colWidth + 3, yPos + 5.5);
                yPos += rowHeight;
            });

            yPos += 10;

            // ===== ANALYST INSIGHTS =====
            if (analystInsights.length > 0) {
                addPageIfNeeded(60);
                doc.setFillColor(37, 99, 235);
                doc.rect(margin, yPos, contentWidth, 8, 'F');
                doc.setTextColor(255, 255, 255);
                doc.setFontSize(14);
                doc.setFont('helvetica', 'bold');
                doc.text('Analyst Insights', margin + 3, yPos + 6);
                yPos += 15;

                analystInsights.slice(0, 5).forEach((insight, idx) => {
                    addPageIfNeeded(35);

                    // Insight box
                    doc.setFillColor(248, 250, 252);
                    const boxHeight = 25;
                    doc.roundedRect(margin, yPos, contentWidth, boxHeight, 2, 2, 'F');

                    // Severity badge
                    const severityColors: any = {
                        'critical': [239, 68, 68],
                        'warning': [251, 191, 36],
                        'info': [59, 130, 246]
                    };
                    const badgeColor = severityColors[insight.severity] || [100, 116, 139];
                    doc.setFillColor(badgeColor[0], badgeColor[1], badgeColor[2]);
                    doc.circle(margin + 5, yPos + 5, 2, 'F');

                    // Title
                    doc.setTextColor(15, 23, 42);
                    doc.setFontSize(11);
                    doc.setFont('helvetica', 'bold');
                    doc.text(`${idx + 1}. ${insight.title || 'Untitled'}`, margin + 10, yPos + 6);

                    // Summary
                    doc.setFontSize(9);
                    doc.setFont('helvetica', 'normal');
                    doc.setTextColor(71, 85, 105);
                    const summaryLines = doc.splitTextToSize(insight.summary || '', contentWidth - 15);
                    doc.text(summaryLines.slice(0, 2), margin + 10, yPos + 12);

                    yPos += boxHeight + 5;
                });
            }

            // ===== BUSINESS INSIGHTS =====
            if (businessInsights.length > 0) {
                addPageIfNeeded(60);
                doc.setFillColor(37, 99, 235);
                doc.rect(margin, yPos, contentWidth, 8, 'F');
                doc.setTextColor(255, 255, 255);
                doc.setFontSize(14);
                doc.setFont('helvetica', 'bold');
                doc.text('Business Insights & Recommendations', margin + 3, yPos + 6);
                yPos += 15;

                businessInsights.slice(0, 5).forEach((insight, idx) => {
                    addPageIfNeeded(40);

                    // Insight box with gradient
                    doc.setFillColor(236, 254, 255);
                    const boxHeight = insight.recommendation ? 32 : 25;
                    doc.roundedRect(margin, yPos, contentWidth, boxHeight, 2, 2, 'F');

                    // Icon
                    doc.setFillColor(6, 182, 212);
                    doc.circle(margin + 5, yPos + 5, 2, 'F');

                    // Title
                    doc.setTextColor(15, 23, 42);
                    doc.setFontSize(11);
                    doc.setFont('helvetica', 'bold');
                    doc.text(`${idx + 1}. ${insight.title || 'Untitled'}`, margin + 10, yPos + 6);

                    // Summary
                    doc.setFontSize(9);
                    doc.setFont('helvetica', 'normal');
                    doc.setTextColor(71, 85, 105);
                    const summaryLines = doc.splitTextToSize(insight.summary || '', contentWidth - 15);
                    doc.text(summaryLines.slice(0, 2), margin + 10, yPos + 12);

                    // Recommendation
                    if (insight.recommendation) {
                        doc.setTextColor(16, 185, 129);
                        doc.setFont('helvetica', 'italic');
                        doc.setFontSize(8);
                        const recLines = doc.splitTextToSize(`→ ${insight.recommendation || ''}`, contentWidth - 15);
                        doc.text(recLines.slice(0, 2), margin + 10, yPos + 22);
                    }

                    yPos += boxHeight + 5;
                });
            }

            // ===== FOOTER ON EVERY PAGE =====
            const totalPages = (doc as any).internal.pages.length - 1;
            for (let i = 1; i <= totalPages; i++) {
                doc.setPage(i);
                doc.setFontSize(8);
                doc.setTextColor(148, 163, 184);
                doc.text(
                    `DataPilot AI - Intelligent Data Analysis Platform | Page ${i} of ${totalPages}`,
                    pageWidth / 2,
                    pageHeight - 10,
                    { align: 'center' }
                );
            }

            // Save PDF
            const fileName = `DataPilot_Analysis_${new Date().toISOString().split('T')[0]}_${jobId?.substring(0, 8)}.pdf`;
            doc.save(fileName);

            // Reset button
            if (button && originalText) {
                button.disabled = false;
                button.innerHTML = originalText;
            }

        } catch (error) {
            console.error('Error generating PDF:', error);
            alert('Failed to generate report. Please try again.');

            // Reset button on error
            const button = document.querySelector('button[onclick*="handleDownloadReport"]') as HTMLButtonElement;
            if (button) {
                button.disabled = false;
                button.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg> Download Report';
            }
        }
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
                                                <button
                                                    onClick={handleDownloadReport}
                                                    className="flex-1 flex items-center justify-center gap-2 bg-datapilot-primary text-white font-semibold py-2.5 rounded-lg hover:bg-blue-600 transition-shadow shadow-md hover:shadow-lg text-sm"
                                                >
                                                    <Download className="w-4 h-4" /> Download Report
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

export default function ResultsPage() {
    return (
        <React.Suspense fallback={<div className="min-h-screen bg-datapilot-page flex items-center justify-center">Loading results...</div>}>
            <ResultsPageContent />
        </React.Suspense>
    );
}

