
import { create } from 'zustand';
import { AnalysisResult } from '@/types/analysis';

interface ResultState {
    loading: boolean;
    error: string | null;
    result: AnalysisResult | null;
    highlightRowIndex: number | null;

    fetchResult: (jobId: string) => Promise<void>;
    retry: () => void;
    setHighlightRow: (index: number | null) => void;
    reset: () => void;
}

const MAX_RETRIES = 5;
const BASE_DELAY = 500; // ms

export const useResultStore = create<ResultState>((set, get) => ({
    loading: false,
    error: null,
    result: null,
    highlightRowIndex: null,

    fetchResult: async (jobId: string) => {
        let attempts = 0;

        const tryFetch = async () => {
            try {
                set({ loading: true, error: null });

                // 1. Get Job Status first
                const statusRes = await fetch(`/api/job-status/${jobId}`);
                if (!statusRes.ok) throw new Error("Failed to check job status");

                const statusData = await statusRes.json();

                if (statusData.status === 'failed') {
                    throw new Error(statusData.error || "Job processing failed");
                }

                if (statusData.status === 'processing' || statusData.status === 'pending') {
                    // Not ready, verify timeout or retry
                    if (attempts < MAX_RETRIES) {
                        const delay = BASE_DELAY * Math.pow(2, attempts);
                        attempts++;
                        setTimeout(tryFetch, delay);
                        return;
                    } else {
                        // Polling should be handled by the component or a dedicated poller?
                        // Prompt says: "Auto-retry with exponential backoff (0.5 → 1 → 2 → 4 sec)"
                        // This usually implies polling while status is not completed.
                        // But if I use this strictly for "fetchResult", maybe I should just wait?
                        // If status is still processing, we usually keep polling.
                        // "MAX_RETRIES" usually applies to errors. For polling, we might want until timeout?
                        // Let's implement robust polling until complete or failed.

                        // If still processing, keep polling but slow down
                        const delay = 4000;
                        setTimeout(tryFetch, delay);
                        return;
                    }
                }

                if (statusData.status === 'completed') {
                    // 2. Fetch Actual Result
                    // If resultUrl starts with /api/results, use it.
                    const resultUrl = statusData.resultUrl || `/api/results/${jobId}`;
                    const res = await fetch(resultUrl);
                    if (!res.ok) throw new Error("Failed to fetch analysis result");

                    const data: AnalysisResult = await res.json();

                    // Runtime validation safeguard (optional but good)
                    if (!data.insightsAnalyst) data.insightsAnalyst = [];
                    if (!data.chartSpecs) data.chartSpecs = [];

                    set({ result: data, loading: false });
                    return;
                }

            } catch (err: any) {
                console.error("Fetch error:", err);
                set({ error: err.message || "Unknown error", loading: false });
            }
        };

        tryFetch();
    },

    retry: () => {
        const { result } = get();
        // If we have a result, maybe just re-fetch?
        // Actually retry usually implies error state recovery.
        // For now, no-op or clear error.
        set({ error: null, loading: false });
    },

    setHighlightRow: (index) => set({ highlightRowIndex: index }),

    reset: () => set({ result: null, error: null, loading: false, highlightRowIndex: null })
}));
