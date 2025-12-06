'use client';

import React, { useState } from 'react';
import { clsx } from 'clsx';
import { AlertCircle, AlertTriangle, Info, MoreHorizontal, ChevronDown, Check, Lightbulb } from 'lucide-react';
import { useEvidenceHighlight } from './EvidenceHighlightContext';
import { useToast } from '../ui/ToastContext';

type Severity = 'info' | 'warning' | 'critical';

interface Insight {
    id: string;
    type: 'Analyst' | 'Business';
    title: string;
    summary: string;
    severity: Severity;
    evidence: { label: string; value: string }[];
    rowIndices: number[];
    recommendation: string;
}

const INSIGHTS: Insight[] = [
    {
        id: '1',
        type: 'Analyst',
        title: 'Seasonal Spike Detected',
        summary: 'Sales show a 25% increase in June compared with the previous 3-month average.',
        severity: 'warning',
        evidence: [
            { label: 'Total_June', value: '$320k' },
            { label: 'avg_prior_3mo', value: '$256k' },
        ],
        rowIndices: [14, 45],
        recommendation: 'Verify promotional campaigns in June; flag top 3 SKUs for follow-up.'
    },
    {
        id: '2',
        type: 'Business',
        title: 'Large Transaction Outlier',
        summary: 'A single transaction of $999.5 on 2025-06-12 lacks unit count.',
        severity: 'info',
        evidence: [
            { label: 'max_total', value: '$999.5' },
        ],
        rowIndices: [2],
        recommendation: 'Contact Sales Ops to confirm or correct source invoice.'
    }
];

export default function InsightsPanel() {
    const [activeTab, setActiveTab] = useState<'Analyst' | 'Business'>('Analyst');
    const [expandedEvidence, setExpandedEvidence] = useState<string | null>(null);
    const { highlightRow, clearHighlight } = useEvidenceHighlight();
    const { showToast } = useToast();

    const activeInsights = INSIGHTS.filter(i => i.type === activeTab || i.rowIndices.length > 0) // Just showing mocked ones strictly? Prompt says "Analyst Mode / Business Mode (toggle)". I'll filter.
        .filter(i => i.type === activeTab || (activeTab === 'Business' && i.title === 'Large Transaction Outlier') || (activeTab === 'Analyst' && i.title === 'Seasonal Spike Detected'));
    // Actually, prompt provides SAMPLE texts. I will manually map them to tabs or just show all if not specified.
    // "Insight sample #1 (Analyst)... Insight sample #2 (Business)..."
    // So I strictly separate them.

    const renderInsightCard = (insight: Insight, isPrimary: boolean) => {
        const isExpanded = expandedEvidence === insight.id;

        return (
            <div key={insight.id} className={clsx(
                "bg-white rounded-[12px] p-4 border transition-all mb-4",
                isPrimary ? "shadow-md border-datapilot-primary/20 ring-1 ring-datapilot-primary/5" : "border-datapilot-border shadow-sm opacity-90 hover:opacity-100"
            )}>
                <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-datapilot-text text-sm">{insight.title}</h4>
                    </div>
                    <span className={clsx(
                        "text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border",
                        insight.severity === 'info' && "insight-severity-info",
                        insight.severity === 'warning' && "insight-severity-warning",
                        insight.severity === 'critical' && "insight-severity-critical"
                    )}>
                        {insight.severity}
                    </span>
                </div>

                <p className="text-sm text-datapilot-text mb-3 leading-relaxed">
                    {insight.summary}
                </p>

                {/* Actions Row */}
                <div className="flex items-center gap-2 mb-3">
                    <button
                        onClick={() => {
                            setExpandedEvidence(isExpanded ? null : insight.id);
                            if (!isExpanded) showToast("Evidence expanded", "info");
                        }}
                        className="text-xs font-medium text-datapilot-primary hover:text-blue-600 flex items-center bg-blue-50 px-2 py-1 rounded"
                    >
                        Show Evidence <ChevronDown className={clsx("w-3 h-3 ml-1 transition-transform", isExpanded && "rotate-180")} />
                    </button>
                    <button
                        onClick={() => showToast("AI Action Suggestion generated (Copied to action center)", "success")}
                        className="text-xs font-medium text-datapilot-text border border-datapilot-border px-2 py-1 rounded hover:bg-gray-50 flex items-center"
                    >
                        <Lightbulb className="w-3 h-3 mr-1 text-datapilot-orange" /> Suggest Action
                    </button>
                </div>

                {/* Expanded Evidence */}
                {isExpanded && (
                    <div className="bg-slate-50 rounded-lg p-3 mb-3 border border-slate-100 text-xs text-datapilot-muted animate-in slide-in-from-top-2 duration-200">
                        <ul className="mb-2 space-y-1">
                            {insight.evidence.map((ev, i) => (
                                <li key={i} className="flex justify-between border-b border-slate-200 pb-1 last:border-0">
                                    <span>{ev.label}</span>
                                    <span className="font-mono text-datapilot-text">{ev.value}</span>
                                </li>
                            ))}
                        </ul>
                        <div className="flex gap-2 mt-2">
                            {insight.rowIndices.map((idx) => (
                                <button
                                    key={idx}
                                    onClick={() => highlightRow(idx)}
                                    // onBlur={clearHighlight} // maybe Keep highlighted? Prompt: "Clicking again clears highlight"
                                    className="bg-yellow-100 text-yellow-800 text-[10px] font-bold px-2 py-1 rounded hover:bg-yellow-200 border border-yellow-200 transition-colors"
                                >
                                    Row {idx}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Recommendation */}
                <div className="bg-emerald-50/50 p-3 rounded-lg border border-emerald-100/50 flex gap-2">
                    <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <span className="text-xs text-emerald-900 font-medium">
                        {insight.recommendation}
                    </span>
                </div>
            </div>
        );
    };

    return (
        <div className="glass-panel rounded-[16px] p-1 flex flex-col h-full">
            {/* Height constraint handled by parent flex container */}

            <div className="px-4 py-3 border-b border-datapilot-border/50 flex justify-between items-center bg-white/40 rounded-t-[15px]">
                <h2 className="text-datapilot-text font-bold text-lg flex items-center gap-2">
                    AI Insights
                    <span className="w-2 h-2 rounded-full bg-datapilot-primary animate-pulse" />
                </h2>
            </div>

            <div className="px-4 py-2 bg-white/40 border-b border-datapilot-border/50">
                <div className="flex bg-slate-100/80 p-1 rounded-lg">
                    <button
                        onClick={() => setActiveTab('Analyst')}
                        className={clsx(
                            "flex-1 text-xs font-semibold py-1.5 rounded-md transition-all text-center",
                            activeTab === 'Analyst' ? "bg-white text-datapilot-primary shadow-sm" : "text-datapilot-muted hover:text-datapilot-text"
                        )}
                    >
                        Analyst Mode
                    </button>
                    <button
                        onClick={() => setActiveTab('Business')}
                        className={clsx(
                            "flex-1 text-xs font-semibold py-1.5 rounded-md transition-all text-center",
                            activeTab === 'Business' ? "bg-white text-datapilot-primary shadow-sm" : "text-datapilot-muted hover:text-datapilot-text"
                        )}
                    >
                        Business Mode
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
                {activeTab === 'Analyst' && renderInsightCard(INSIGHTS[0], true)}
                {activeTab === 'Business' && renderInsightCard(INSIGHTS[1], true)}

                {/* Accordion for more */}
                <div className="border border-datapilot-border rounded-lg bg-white/60">
                    <details className="group">
                        <summary className="flex justify-between items-center p-3 cursor-pointer text-sm font-medium text-datapilot-muted hover:text-datapilot-text">
                            More Insights (3)
                            <ChevronDown className="w-4 h-4 transition-transform group-open:rotate-180" />
                        </summary>
                        <div className="p-3 pt-0 border-t border-datapilot-border/50 text-xs text-datapilot-muted">
                            <p className="mb-2">Additional low-priority anomalies found in Q3 data...</p>
                            {/* Placeholder for folded insights */}
                            <div className="p-2 bg-white border border-slate-100 rounded mb-2 shadow-sm">
                                <span className="font-semibold text-slate-700">Minor dip in August</span>
                            </div>
                        </div>
                    </details>
                </div>
            </div>

        </div>
    );
}
