"use client";

import React, { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { CheckCircle2, Database, BarChart3, Sparkles, Brain, Zap, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

const steps = [
    { label: "Cleaning Data", icon: Database },
    { label: "Structuring Schema", icon: BarChart3 },
    { label: "Profiling Columns", icon: Sparkles },
    { label: "Analyzing Patterns", icon: Brain },
    { label: "Generating Insights", icon: Zap }
];

interface LoadingStateProps {
    currentStep: number;
    onCancel?: () => void;
}

export default function LoadingState({ currentStep, onCancel }: LoadingStateProps) {
    const [progress, setProgress] = useState(0);
    const targetProgress = Math.min((currentStep + 1) * 20, 99);

    // Smooth progress animation
    useEffect(() => {
        const interval = setInterval(() => {
            setProgress(prev => {
                if (prev < targetProgress) {
                    return Math.min(prev + 1, targetProgress);
                }
                return prev;
            });
        }, 30);
        return () => clearInterval(interval);
    }, [targetProgress]);

    return (
        <div className="w-full min-h-[500px] md:min-h-[600px] flex items-center justify-center p-4 md:p-8 pb-24 md:pb-8">
            <div className="w-full max-w-2xl mx-auto space-y-8 md:space-y-12">

                {/* Progress Circle */}
                <div className="flex flex-col items-center justify-center">
                    <div className="relative w-40 h-40 sm:w-48 sm:h-48 md:w-56 md:h-56">
                        {/* Background Circle */}
                        <svg className="w-full h-full -rotate-90" viewBox="0 0 200 200">
                            <circle
                                cx="100"
                                cy="100"
                                r="90"
                                fill="none"
                                stroke="#E2E8F0"
                                strokeWidth="8"
                                className="opacity-20"
                            />
                            <circle
                                cx="100"
                                cy="100"
                                r="90"
                                fill="none"
                                stroke="url(#progressGradient)"
                                strokeWidth="8"
                                strokeLinecap="round"
                                strokeDasharray={`${2 * Math.PI * 90}`}
                                strokeDashoffset={`${2 * Math.PI * 90 * (1 - progress / 100)}`}
                                className="transition-all duration-300 ease-out"
                            />
                            <defs>
                                <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stopColor="#2563EB" />
                                    <stop offset="100%" stopColor="#06B6D4" />
                                </linearGradient>
                            </defs>
                        </svg>

                        {/* Center Content */}
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            {/* Current Step Icon */}
                            <div className="mb-3 md:mb-4">
                                {steps[currentStep] && React.createElement(steps[currentStep].icon, {
                                    className: "w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 text-primary",
                                    strokeWidth: 1.5
                                })}
                            </div>

                            {/* Percentage */}
                            <div className="text-4xl sm:text-5xl md:text-6xl font-bold bg-gradient-to-br from-primary to-secondary bg-clip-text text-transparent">
                                {progress}%
                            </div>

                            {/* Status */}
                            <div className="text-xs sm:text-sm font-medium text-slate-500 mt-2 tracking-wide uppercase">
                                Processing
                            </div>
                        </div>
                    </div>

                    {/* Current Step Label */}
                    <div className="mt-6 md:mt-8 text-center">
                        <p className="text-base sm:text-lg md:text-xl font-semibold text-slate-700">
                            {steps[currentStep]?.label}
                        </p>
                    </div>
                </div>

                {/* Progress Steps */}
                <div className="w-full space-y-2 md:space-y-3">
                    {steps.map((step, index) => {
                        const isCompleted = index < currentStep;
                        const isCurrent = index === currentStep;
                        const Icon = step.icon;

                        return (
                            <div
                                key={index}
                                className={cn(
                                    "flex items-center gap-3 md:gap-4 p-3 md:p-4 rounded-xl md:rounded-2xl transition-all duration-500",
                                    isCurrent && "bg-white shadow-lg border-2 border-primary/20",
                                    isCompleted && "bg-emerald-50/50 border border-emerald-200",
                                    !isCurrent && !isCompleted && "bg-slate-50/50 border border-slate-100 opacity-60"
                                )}
                            >
                                {/* Step Number/Icon */}
                                <div className={cn(
                                    "flex-shrink-0 w-10 h-10 md:w-12 md:h-12 rounded-lg md:rounded-xl flex items-center justify-center transition-all duration-500",
                                    isCurrent && "bg-gradient-to-br from-primary to-secondary shadow-md",
                                    isCompleted && "bg-gradient-to-br from-emerald-500 to-emerald-600",
                                    !isCurrent && !isCompleted && "bg-slate-200"
                                )}>
                                    {isCompleted ? (
                                        <CheckCircle2 className="w-5 h-5 md:w-6 md:h-6 text-white" strokeWidth={2.5} />
                                    ) : (
                                        <Icon className={cn(
                                            "w-5 h-5 md:w-6 md:h-6",
                                            isCurrent ? "text-white" : "text-slate-400"
                                        )} strokeWidth={2} />
                                    )}
                                </div>

                                {/* Step Label */}
                                <div className="flex-1 min-w-0">
                                    <p className={cn(
                                        "text-sm md:text-base font-semibold truncate transition-colors duration-500",
                                        isCompleted && "text-emerald-700",
                                        isCurrent && "text-slate-800",
                                        !isCurrent && !isCompleted && "text-slate-500"
                                    )}>
                                        {step.label}
                                    </p>
                                </div>

                                {/* Status Indicator */}
                                <div className="flex-shrink-0">
                                    {isCurrent && (
                                        <div className="flex gap-1">
                                            {[...Array(3)].map((_, i) => (
                                                <div
                                                    key={i}
                                                    className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce"
                                                    style={{ animationDelay: `${i * 0.15}s` }}
                                                />
                                            ))}
                                        </div>
                                    )}
                                    {isCompleted && (
                                        <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Progress Bar & Cancel Action */}
                <div className="w-full space-y-8">
                    <div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-primary to-secondary rounded-full transition-all duration-500 ease-out"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                        <div className="flex justify-between items-center mt-2 text-xs text-slate-500">
                            <span>Step {currentStep + 1} of {steps.length}</span>
                            <span>{progress}% Complete</span>
                        </div>
                    </div>

                    {/* Cancel Button - Mobile Fixed Bottom, Desktop Inline */}
                    <div className="fixed bottom-0 left-0 right-0 p-4 bg-white/80 backdrop-blur-md border-t border-slate-200 z-50 md:static md:bg-transparent md:border-0 md:p-0">
                        <Button
                            variant="destructive"
                            className="w-full md:w-auto md:min-w-[200px] h-12 md:h-10 text-base md:text-sm font-medium shadow-lg md:shadow-none rounded-xl md:rounded-lg mx-auto block"
                            onClick={onCancel}
                        >
                            Cancel Job
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
