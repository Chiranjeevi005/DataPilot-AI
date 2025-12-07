"use client";

import React, { useEffect, useState } from 'react';
import LoadingState from '@/components/loading/LoadingState';
import { useAppStore, useSidebarStore } from '@/lib/store';
import { useRouter, useSearchParams } from 'next/navigation';
import axios from 'axios';
import NavBar from '@/components/NavBar';
import Sidebar from '@/components/Sidebar';
import { cn } from '@/lib/utils';

export default function LoadingPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { jobId: storeJobId, jobStatus, updateJobStatus, setResults, currentStep, reset } = useAppStore();
    const isOpen = useSidebarStore((state) => state.isOpen);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    // Get jobId from URL query param first, fallback to store
    const jobId = searchParams.get('jobId') || storeJobId;

    const handleCancel = () => {
        reset();
        router.push('/upload');
    };

    useEffect(() => {
        // If no jobId at all, redirect to upload
        if (!jobId) {
            console.error('No jobId found in URL or store, redirecting to upload');
            setErrorMessage('No job ID found. Redirecting to upload...');
            setTimeout(() => {
                router.push('/upload');
            }, 2000);
            return;
        }

        console.log('Loading page: Polling for job:', jobId);

        // Poll immediately on mount
        let isActive = true;

        const pollStatus = async () => {
            if (!isActive) return;

            try {
                console.log(`Polling job status for: ${jobId}`);
                const { data } = await axios.get(`/api/job-status?jobId=${jobId}`);

                console.log(`Job ${jobId} status:`, data.status);

                if (data.status === 'completed') {
                    updateJobStatus('completed', 5);
                    console.log('Job completed, redirecting to results');
                    router.push(`/results?jobId=${jobId}`);
                } else if (data.status === 'failed') {
                    updateJobStatus('error', 5);
                    console.log('Job failed, redirecting to results');
                    router.push(`/results?jobId=${jobId}`);
                } else if (data.status === 'processing') {
                    updateJobStatus('processing', 3);
                } else if (data.status === 'submitted' || data.status === 'pending') {
                    updateJobStatus('processing', 2);
                }
            } catch (err: any) {
                console.error("Poll error:", err);
                if (err.response?.status === 404) {
                    setErrorMessage('Job not found. It may have been deleted.');
                    setTimeout(() => {
                        router.push('/upload');
                    }, 3000);
                }
            }
        };

        // Poll immediately
        pollStatus();

        // Then poll every 2 seconds (faster for better UX)
        const interval = setInterval(pollStatus, 2000);

        // Simulate progress for the steps UI independent of polling for smoother demo
        const stepInterval = setInterval(() => {
            useAppStore.setState((state) => ({
                currentStep: state.currentStep < 4 ? state.currentStep + 1 : 4
            }));
        }, 2000);

        return () => {
            isActive = false;
            clearInterval(interval);
            clearInterval(stepInterval);
        };
    }, [jobId, router, updateJobStatus]);

    return (
        <div className="min-h-screen bg-background font-sans text-slate-900">
            <NavBar />
            <Sidebar />
            <main className={cn("min-h-screen pt-24 pb-10 flex items-center justify-center transition-all duration-300 ease-in-out", isOpen ? "md:ml-20 lg:ml-72" : "ml-0")}>
                {errorMessage ? (
                    <div className="text-center">
                        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
                            <div className="text-red-600 font-semibold mb-2">Error</div>
                            <div className="text-red-800">{errorMessage}</div>
                        </div>
                    </div>
                ) : (
                    <LoadingState currentStep={currentStep} onCancel={handleCancel} />
                )}
            </main>
        </div>
    );
}
