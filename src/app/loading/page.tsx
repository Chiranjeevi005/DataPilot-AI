"use client";

import React, { useEffect } from 'react';
import LoadingState from '@/components/loading/LoadingState';
import { useAppStore, useSidebarStore } from '@/lib/store';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import NavBar from '@/components/NavBar';
import Sidebar from '@/components/Sidebar';
import { cn } from '@/lib/utils';

export default function LoadingPage() {
    const router = useRouter();
    const { jobId, jobStatus, updateJobStatus, setResults, currentStep, reset } = useAppStore();
    const isOpen = useSidebarStore((state) => state.isOpen);

    const handleCancel = () => {
        reset();
        router.push('/upload');
    };

    useEffect(() => {
        if (!jobId) {
            // router.push('/upload');
            return;
        }

        const pollStatus = async () => {
            try {
                // Correct API call using query param
                const { data } = await axios.get(`/api/job-status?jobId=${jobId}`);

                if (data.status === 'completed') {
                    updateJobStatus('completed', 5);
                    setTimeout(() => {
                        router.push(`/results?jobId=${jobId}`);
                    }, 500);
                } else if (data.status === 'failed') {
                    updateJobStatus('error', 5);
                    router.push(`/results?jobId=${jobId}`);
                }
            } catch (err) {
                console.error("Poll error:", err);
            }
        };

        const interval = setInterval(pollStatus, 3000);

        // Simulate progress for the steps UI independent of polling for smoother demo
        const stepInterval = setInterval(() => {
            useAppStore.setState((state) => ({
                currentStep: state.currentStep < 4 ? state.currentStep + 1 : 4
            }));
        }, 2000);

        return () => {
            clearInterval(interval);
            clearInterval(stepInterval);
        };
    }, [jobId, router, updateJobStatus]);

    return (
        <div className="min-h-screen bg-background font-sans text-slate-900">
            <NavBar />
            <Sidebar />
            <main className={cn("min-h-screen pt-24 pb-10 flex items-center justify-center transition-all duration-300 ease-in-out", isOpen ? "md:ml-20 lg:ml-72" : "ml-0")}>
                <LoadingState currentStep={currentStep} onCancel={handleCancel} />
            </main>
        </div>
    );
}
