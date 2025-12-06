export interface KpiItem {
    name: string;
    value: number | string;
    delta?: number;
    deltaType?: "positive" | "negative" | "neutral";
}

export interface InsightEvidence {
    type: "aggregate" | "row" | "pattern" | "metric";
    key?: string;
    value?: any;
    rowIndex?: number;
    description?: string;
}

export interface InsightItem {
    id: string;
    title: string;
    summary: string;
    severity: "info" | "warning" | "critical";
    evidence: InsightEvidence[];
    recommendation?: string;
}

export interface BusinessSummaryItem {
    text: string;
    evidenceKeys?: string[];
}

export interface ChartSpec {
    id: string;
    type: "line" | "bar" | "donut";
    title: string;
    data: any[];
    xKey?: string;
    yKey?: string; // Optional for Donut, usually valueKey
    metadata?: Record<string, any>;
}

export interface AnalysisResult {
    jobId: string;
    kpis: KpiItem[];
    schema: any[];
    cleanedPreview: any[];
    insightsAnalyst: InsightItem[];
    insightsBusiness: InsightItem[];
    businessSummary: BusinessSummaryItem[];
    chartSpecs: ChartSpec[]; // Explicitly typed
    qualityScore: number;
    issues: string[];
    processedAt: string;
    isFromCache?: boolean;
    version?: string;
    uiOptimized?: boolean;
}
