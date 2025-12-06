/**
 * Test file to demonstrate Recent Uploads functionality
 * 
 * This file shows how the recent uploads feature integrates with the app
 */

import { useAppStore, RecentUpload } from '@/lib/store';

// Example: How uploads are automatically tracked
export function exampleUploadFlow() {
    const { setFile, startJob } = useAppStore.getState();

    // 1. User selects a file
    const file = new File(['test'], 'sales_data.csv', { type: 'text/csv' });
    setFile(file);

    // 2. User clicks "Run Analysis"
    // This automatically adds the upload to recent uploads
    const jobId = 'job_123456';
    startJob(jobId); // This creates a RecentUpload entry with status 'processing'
}

// Example: How to manually add a recent upload (if needed)
export function exampleManualAdd() {
    const { addRecentUpload } = useAppStore.getState();

    const upload: RecentUpload = {
        jobId: 'job_789',
        fileName: 'customer_data.xlsx',
        fileType: 'xlsx',
        fileSize: 1024000, // 1MB
        uploadedAt: new Date().toISOString(),
        status: 'processing'
    };

    addRecentUpload(upload);
}

// Example: How to update upload status
export function exampleStatusUpdate() {
    const { updateRecentUploadStatus } = useAppStore.getState();

    // When a job completes
    updateRecentUploadStatus('job_123456', 'completed');

    // Or if it fails
    updateRecentUploadStatus('job_789', 'error');
}

// Example: How to get all recent uploads
export function exampleGetUploads() {
    const { recentUploads } = useAppStore.getState();

    console.log('Recent uploads:', recentUploads);

    // Filter by status
    const completedUploads = recentUploads.filter(u => u.status === 'completed');
    const processingUploads = recentUploads.filter(u => u.status === 'processing');

    return { completedUploads, processingUploads };
}

// Example: How to clear all recent uploads
export function exampleClearUploads() {
    const { clearRecentUploads } = useAppStore.getState();

    if (confirm('Are you sure you want to clear all recent uploads?')) {
        clearRecentUploads();
    }
}

// Example: React component usage
// Note: For actual JSX, create a .tsx file
// For a production-ready component, see: src/components/RecentUploadsPanel.tsx
export function exampleReactUsage() {
    // In a React component (.tsx file), you would use:
    // const recentUploads = useAppStore((state) => state.recentUploads);
    // const addRecentUpload = useAppStore((state) => state.addRecentUpload);

    // Then render the uploads in your JSX - see RecentUploadsPanel.tsx for full example
    console.log('See src/components/RecentUploadsPanel.tsx for a complete React component example');
}
