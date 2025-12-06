import { create } from 'zustand';

interface SidebarStore {
    isOpen: boolean;
    toggle: () => void;
    close: () => void;
}

export const useSidebarStore = create<SidebarStore>((set) => ({
    isOpen: false,
    toggle: () => set((state) => ({ isOpen: !state.isOpen })),
    close: () => set({ isOpen: false }),
}));



export type FileType = 'csv' | 'json' | 'pdf' | 'xlsx' | 'unknown';

export interface KPI {
    title: string;
    value: string | number;
    change?: string;
    trend?: 'up' | 'down' | 'neutral';
    icon?: string;
}

export interface ChartSpec {
    id: string;
    type: 'line' | 'bar' | 'donut';
    title: string;
    data: any[];
    dataKey: string;
    categoryKey?: string;
}

export interface Insight {
    id: string;
    title: string;
    explanation: string;
    evidence?: string;
    type: 'analyst' | 'business';
}

export interface ResultsData {
    kpis: KPI[];
    chartSpecs: ChartSpec[];
    cleanedPreview: any[];
    insights: Insight[];
    qualityScore: number;
}

interface AppState {
    // Upload & Preview State
    file: File | null;
    fileName: string | null;
    fileType: FileType;
    fileSize: number;
    previewRows: any[];
    previewColumns: string[];
    totalRows: number;

    // Job State
    jobId: string | null;
    jobStatus: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
    currentStep: number; // For loading screen stepper

    // Results State
    results: ResultsData | null;

    // Actions
    setFile: (file: File) => void;
    setPreviewData: (rows: any[], columns: string[], totalRows: number) => void;
    startJob: (jobId: string) => void;
    updateJobStatus: (status: AppState['jobStatus'], step?: number) => void;
    setResults: (results: ResultsData) => void;
    reset: () => void;
}

export const useAppStore = create<AppState>((set) => ({
    file: null,
    fileName: null,
    fileType: 'unknown',
    fileSize: 0,
    previewRows: [],
    previewColumns: [],
    totalRows: 0,

    jobId: null,
    jobStatus: 'idle',
    currentStep: 0,

    results: null,

    setFile: (file) => {
        let type: FileType = 'unknown';
        if (file.name.endsWith('.csv')) type = 'csv';
        else if (file.name.endsWith('.json')) type = 'json';
        else if (file.name.endsWith('.pdf')) type = 'pdf';
        else if (file.name.endsWith('.xlsx')) type = 'xlsx';

        set({
            file,
            fileName: file.name,
            fileSize: file.size,
            fileType: type
        });
    },

    setPreviewData: (rows, columns, totalRows) => set({ previewRows: rows, previewColumns: columns, totalRows }),

    startJob: (jobId) => set({ jobId, jobStatus: 'processing', currentStep: 1 }),

    updateJobStatus: (status, step) => set((state) => ({
        jobStatus: status,
        currentStep: step !== undefined ? step : state.currentStep
    })),

    setResults: (results) => set({ results, jobStatus: 'completed' }),

    reset: () => set({
        file: null,
        fileName: null,
        fileType: 'unknown',
        fileSize: 0,
        previewRows: [],
        previewColumns: [],
        totalRows: 0,
        jobId: null,
        jobStatus: 'idle',
        currentStep: 0,
        results: null
    })
}));
