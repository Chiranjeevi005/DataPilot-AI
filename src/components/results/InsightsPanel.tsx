'use client';

import React, { useState } from 'react';
import { clsx } from 'clsx';
import { AlertCircle, AlertTriangle, Info, MoreHorizontal, ChevronDown, Check, Lightbulb } from 'lucide-react';
import { useEvidenceHighlight } from './EvidenceHighlightContext';
import { useToast } from '../ui/ToastContext';

import { InsightItem } from '@/types/analysis';

interface InsightsPanelProps {
    analystInsights?: InsightItem[];
    businessInsights?: InsightItem[];
}

// Mock data removed in favor of props

export default function InsightsPanel({ analystInsights = [], businessInsights = [] }: InsightsPanelProps) {
    const [activeTab, setActiveTab] = useState<'Analyst' | 'Business'>('Analyst');
    const [expandedEvidence, setExpandedEvidence] = useState<string | null>(null);
    const { highlightRow, clearHighlight } = useEvidenceHighlight();
    const { showToast } = useToast();

    const activeInsights = activeTab === 'Analyst' ? analystInsights : businessInsights;

    const renderInsightCard = (insight: InsightItem, isPrimary: boolean) => {
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
                    {insight.evidence && insight.evidence.length > 0 && (
                        <button
                            onClick={() => {
                                setExpandedEvidence(isExpanded ? null : insight.id);
                                if (!isExpanded) showToast("Evidence expanded", "info");
                            }}
                            className="text-xs font-medium text-datapilot-primary hover:text-blue-600 flex items-center bg-blue-50 px-2 py-1 rounded"
                        >
                            Show Evidence <ChevronDown className={clsx("w-3 h-3 ml-1 transition-transform", isExpanded && "rotate-180")} />
                        </button>
                    )}
                    {insight.recommendation && (
                        <button
                            onClick={() => showToast("Action copied", "success")}
                            className="text-xs font-medium text-datapilot-text border border-datapilot-border px-2 py-1 rounded hover:bg-gray-50 flex items-center"
                        >
                            <Lightbulb className="w-3 h-3 mr-1 text-datapilot-orange" /> Action
                        </button>
                    )}
                </div>

                {/* Expanded Evidence */}
                {
                    isExpanded && insight.evidence && (
                        <div className="bg-slate-50 rounded-lg p-3 mb-3 border border-slate-100 text-xs text-datapilot-muted animate-in slide-in-from-top-2 duration-200">
                            <ul className="mb-2 space-y-1">
                                {insight.evidence.map((ev, i) => (
                                    <li key={i} className="flex justify-between border-b border-slate-200 pb-1 last:border-0">
                                        <span>{ev.type === 'row' ? 'Row Ref' : ev.key || 'Metric'}</span>
                                        <span className="font-mono text-datapilot-text">{String(ev.value || '')}</span>
                                        {ev.description && <span className="text-slate-400 italic ml-2">- {ev.description}</span>}
                                    </li>
                                ))}
                            </ul>
                            <div className="flex gap-2 mt-2">
                                {/* Extract row indices from evidence if type is 'row' or 'rowIndex' is present */}
                                {insight.evidence.filter(e => e.rowIndex !== undefined).map((e, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => highlightRow(e.rowIndex!)}
                                        // onBlur={clearHighlight}
                                        className="bg-yellow-100 text-yellow-800 text-[10px] font-bold px-2 py-1 rounded hover:bg-yellow-200 border border-yellow-200 transition-colors"
                                    >
                                        Row {e.rowIndex}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )
                }

                {/* Recommendation */}
                {
                    insight.recommendation && (
                        <div className="bg-emerald-50/50 p-3 rounded-lg border border-emerald-100/50 flex gap-2">
                            <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                            <span className="text-xs text-emerald-900 font-medium">
                                {insight.recommendation}
                            </span>
                        </div>
                    )
                }
            </div >
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
                {activeInsights.length === 0 && (
                    <div className="text-center text-sm text-datapilot-muted mt-8">No insights found for this category.</div>
                )}
                {activeInsights.map((insight, idx) => renderInsightCard(insight, idx < 2))}

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
