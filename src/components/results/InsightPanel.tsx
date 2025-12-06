"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

import { Lightbulb, Briefcase, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Insight } from '@/lib/store';
import { Button } from '@/components/ui/button';

// Inline Simple Tabs for now to avoid complexity of creating accessible Tabs components from scratch if not present.
// Actually I'll use state for tabs.

interface InsightPanelProps {
    insights: Insight[];
}

export default function InsightPanel({ insights }: InsightPanelProps) {
    const [activeTab, setActiveTab] = useState<'analyst' | 'business'>('analyst');
    const filteredInsights = insights.filter(i => i.type === activeTab);

    return (
        <Card className="h-full border-none shadow-lg shadow-blue-900/5 bg-white/80 backdrop-blur-sm sticky top-24">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-xl text-slate-800">
                        <Lightbulb className="text-yellow-500 fill-yellow-500" size={24} />
                        AI Insights
                    </CardTitle>
                </div>

                <div className="flex p-1 bg-slate-100/80 rounded-lg mt-4 w-full">
                    <button
                        onClick={() => setActiveTab('analyst')}
                        className={cn(
                            "flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium rounded-md transition-all",
                            activeTab === 'analyst' ? "bg-white text-primary shadow-sm" : "text-slate-500 hover:text-slate-700"
                        )}
                    >
                        Analyst Mode
                    </button>
                    <button
                        onClick={() => setActiveTab('business')}
                        className={cn(
                            "flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium rounded-md transition-all",
                            activeTab === 'business' ? "bg-white text-secondary shadow-sm" : "text-slate-500 hover:text-slate-700"
                        )}
                    >
                        Business Mode
                    </button>
                </div>
            </CardHeader>

            <CardContent className="space-y-4 mt-2 overflow-y-auto max-h-[calc(100vh-300px)] custom-scrollbar pr-2">
                {filteredInsights.length === 0 && (
                    <div className="text-center text-slate-400 py-10">
                        No insights generated for this view.
                    </div>
                )}

                {filteredInsights.map((insight) => (
                    <InsightItem key={insight.id} insight={insight} />
                ))}
            </CardContent>
        </Card>
    );
}

function InsightItem({ insight }: { insight: Insight }) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="border border-slate-100 rounded-xl p-4 bg-white shadow-sm hover:shadow-md transition-all">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <h4 className="font-semibold text-slate-800">{insight.title}</h4>
                    <p className="text-sm text-slate-600 mt-1 leading-relaxed">{insight.explanation}</p>
                </div>
            </div>

            {insight.evidence && (
                <div className="mt-3 pt-3 border-t border-slate-50">
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="flex items-center gap-1 text-xs font-semibold text-primary/80 hover:text-primary transition-colors"
                    >
                        {expanded ? "Hide Evidence" : "Show Evidence"}
                        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>

                    {expanded && (
                        <div className="mt-2 p-3 bg-slate-50 rounded-lg text-xs text-slate-600 font-mono">
                            {insight.evidence}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
