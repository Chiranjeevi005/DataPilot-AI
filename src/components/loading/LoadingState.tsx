"use client";

import React, { useEffect } from 'react';
import { cn } from '@/lib/utils';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

const steps = [
    "Cleaning Data",
    "Structuring Schema",
    "Profiling Columns",
    "Analyzing Patterns",
    "Generating Insights"
];

interface LoadingStateProps {
    currentStep: number;
}

export default function LoadingState({ currentStep }: LoadingStateProps) {
    // Determine active step index based on some logic or just passed prop.
    // The store has currentStep.

    return (
        <div className="flex flex-col items-center justify-center space-y-12">
            {/* Central Animated Ring */}
            <div className="relative">
                <div className="w-64 h-64 rounded-full border-4 border-slate-100 flex items-center justify-center relative">
                    {/* Spinning Rings */}
                    <div className="absolute inset-0 rounded-full border-4 border-t-primary border-r-transparent border-b-transparent border-l-transparent animate-spin duration-[3s]" />
                    <div className="absolute inset-4 rounded-full border-4 border-b-secondary border-t-transparent border-l-transparent border-r-transparent animate-spin duration-[4s] direction-reverse" />

                    {/* Center Pulse */}
                    <div className="w-40 h-40 bg-white rounded-full shadow-[0_0_40px_rgba(37,99,235,0.15)] flex items-center justify-center flex-col z-10">
                        <div className="w-3 h-3 bg-primary rounded-full animate-ping mb-4" />
                        <span className="text-slate-400 text-xs font-semibold tracking-widest uppercase">Processing</span>
                        <span className="text-2xl font-bold text-slate-800 mt-1">
                            {Math.min((currentStep + 1) * 20, 99)}%
                        </span>
                    </div>
                </div>

                {/* Background Glow */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/10 rounded-full blur-3xl -z-10 animate-pulse" />
            </div>

            {/* Steps List */}
            <div className="w-full max-w-md space-y-4">
                {steps.map((step, index) => {
                    const isCompleted = index < currentStep;
                    const isCurrent = index === currentStep;

                    return (
                        <div key={index} className={cn(
                            "flex items-center gap-4 p-3 rounded-xl transition-all duration-500",
                            isCurrent ? "bg-white shadow-soft scale-105 border border-slate-100" : "opacity-50"
                        )}>
                            <div className="relative flex items-center justify-center">
                                {isCompleted ? (
                                    <CheckCircle2 className="text-emerald-500 w-6 h-6" />
                                ) : isCurrent ? (
                                    <Loader2 className="text-primary w-6 h-6 animate-spin" />
                                ) : (
                                    <Circle className="text-slate-200 w-6 h-6" />
                                )}
                                {index !== steps.length - 1 && (
                                    <div className={cn(
                                        "absolute top-8 left-1/2 -translate-x-1/2 w-0.5 h-6",
                                        isCompleted ? "bg-emerald-500" : "bg-slate-200"
                                    )} />
                                )}
                            </div>
                            <span className={cn(
                                "font-medium",
                                isCompleted ? "text-emerald-700" : isCurrent ? "text-slate-800" : "text-slate-400"
                            )}>
                                {step}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
