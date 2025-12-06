import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SidebarStore {
    isOpen: boolean;
    toggle: () => void;
    close: () => void;
    open: () => void;
}

export const useSidebarStore = create<SidebarStore>((set) => ({
    isOpen: false,
    toggle: () => set((state) => ({ isOpen: !state.isOpen })),
    close: () => set({ isOpen: false }),
    open: () => set({ isOpen: true }),
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

export interface RecentUpload {
    jobId: string;
    fileName: string;
    fileType: FileType;
    fileSize: number;
    uploadedAt: string; // ISO timestamp
    status: 'processing' | 'completed' | 'error';
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

    // Recent Uploads
    recentUploads: RecentUpload[];

    // Actions
    setFile: (file: File) => void;
    setPreviewData: (rows: any[], columns: string[], totalRows: number) => void;
    startJob: (jobId: string) => void;
    updateJobStatus: (status: AppState['jobStatus'], step?: number) => void;
    setResults: (results: ResultsData) => void;
    addRecentUpload: (upload: RecentUpload) => void;
    updateRecentUploadStatus: (jobId: string, status: RecentUpload['status']) => void;
    getRecentUploads: () => RecentUpload[];
    clearRecentUploads: () => void;
    reset: () => void;
}

export const useAppStore = create<AppState>()(persist(
    (set, get) => ({
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
        recentUploads: [],

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

        startJob: (jobId) => {
            const state = get();

            // Add to recent uploads when job starts
            if (state.fileName && state.fileType && state.fileSize) {
                const newUpload: RecentUpload = {
                    jobId,
                    fileName: state.fileName,
                    fileType: state.fileType,
                    fileSize: state.fileSize,
                    uploadedAt: new Date().toISOString(),
                    status: 'processing'
                };

                get().addRecentUpload(newUpload);
            }

            set({ jobId, jobStatus: 'processing', currentStep: 1 });
        },

        updateJobStatus: (status, step) => {
            const state = get();

            // Update recent upload status when job status changes
            if (state.jobId && (status === 'completed' || status === 'error')) {
                get().updateRecentUploadStatus(state.jobId, status);
            }

            set({
                jobStatus: status,
                currentStep: step !== undefined ? step : state.currentStep
            });
        },

        setResults: (results) => {
            const state = get();

            // Mark as completed in recent uploads
            if (state.jobId) {
                get().updateRecentUploadStatus(state.jobId, 'completed');
            }

            set({ results, jobStatus: 'completed' });
        },

        addRecentUpload: (upload) => set((state) => {
            // Remove duplicate if exists (same jobId)
            const filtered = state.recentUploads.filter(u => u.jobId !== upload.jobId);

            // Add new upload at the beginning and keep only last 10
            const updated = [upload, ...filtered].slice(0, 10);

            return { recentUploads: updated };
        }),

        updateRecentUploadStatus: (jobId, status) => set((state) => ({
            recentUploads: state.recentUploads.map(upload =>
                upload.jobId === jobId ? { ...upload, status } : upload
            )
        })),

        getRecentUploads: () => get().recentUploads,

        clearRecentUploads: () => set({ recentUploads: [] }),

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
            // Note: recentUploads is NOT reset here to preserve history
        })
    }),
    {
        name: 'datapilot-storage', // localStorage key
        partialize: (state) => ({ recentUploads: state.recentUploads }), // Only persist recentUploads
    }
));
