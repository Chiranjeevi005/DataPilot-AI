"use client";

import React from 'react';
import Link from 'next/link';
import { UploadCloud, ArrowRight, Activity, CheckCircle2, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Hero() {
    return (
        <div className="relative w-full">
            {/* Background Decor */}
            <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-blue-400/10 rounded-full blur-3xl -z-10 translate-x-1/3 -translate-y-1/4" />
            <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-cyan-400/10 rounded-full blur-3xl -z-10 -translate-x-1/3 translate-y-1/4" />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center pt-8 pb-16">

                {/* Left Content - Typography & Actions */}
                <div className="lg:col-span-7 flex flex-col gap-8">
                    <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 w-fit rounded-full border border-blue-100 mb-2">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-500 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-600"></span>
                        </span>
                        <span className="text-xs font-semibold text-blue-700 tracking-wide uppercase">AI is in Action</span>
                    </div>

                    <h1 className="text-5xl lg:text-7xl font-bold tracking-tight text-slate-900 leading-[1.1]">
                        Unlock the <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-500">hidden value</span> in your data.
                    </h1>

                    <p className="text-lg text-slate-500 max-w-xl leading-relaxed">
                        DataPilot AI transforms complex files into clear, actionable dashboards instantly.
                        No coding required—just drag, drop, and discover.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 mt-2">
                        <Link href="/upload" className="h-14 px-8 rounded-full bg-slate-900 text-white font-medium hover:bg-slate-800 transition-all flex items-center justify-center gap-2 shadow-xl shadow-slate-200 hover:-translate-y-1 text-lg group">
                            <UploadCloud size={22} className="text-blue-400" />
                            <span>Start Analyzing Free</span>
                            <ArrowRight size={18} className="opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                        </Link>
                    </div>

                    <div className="flex items-center gap-8 mt-6 text-sm font-medium text-slate-500">
                        <div className="flex items-center gap-2">
                            <CheckCircle2 size={16} className="text-emerald-500" />
                            <span>AI Insights</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <CheckCircle2 size={16} className="text-emerald-500" />
                            <span>99.9% Uptime</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <CheckCircle2 size={16} className="text-emerald-500" />
                            <span>Auto-Scaling</span>
                        </div>
                    </div>
                </div>

                {/* Right Content - Visuals */}
                <div className="lg:col-span-5 relative">
                    <div className="relative z-10 w-full aspect-square lg:aspect-[4/5] rounded-[2.5rem] overflow-hidden border-8 border-white shadow-2xl shadow-blue-900/10 bg-slate-100">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <div className="relative w-full h-full group">
                            <div className="absolute inset-0 bg-blue-500/10 mix-blend-overlay z-10 pointer-events-none group-hover:bg-transparent transition-all duration-500" />
                            <img
                                src="/assets/hero-illustration.png"
                                alt="AI Data Intelligence Core"
                                className="w-full h-full object-cover transition-transform duration-700 hover:scale-105"
                            />
                        </div>

                        {/* Floating Glass Card 1 */}
                        <div className="absolute top-8 right-8 bg-white/10 backdrop-blur-md border border-white/20 p-4 rounded-2xl shadow-lg animate-bounce duration-[3000ms]">
                            <Activity className="text-cyan-400" size={32} />
                            <div className="mt-2 text-white font-semibold text-sm">Insights that Matters</div>
                        </div>

                        {/* Floating Glass Card 2 */}
                        <div className="absolute bottom-8 left-8 bg-slate-900/90 backdrop-blur-md border border-white/10 p-4 rounded-xl shadow-xl max-w-[200px]">
                            <div className="text-xs text-slate-400 mb-1">Growth Potential</div>
                            <div className="flex items-end gap-2">
                                <span className="text-2xl font-bold text-white">Limitless</span>
                                <span className="text-xs text-emerald-400 mb-1">▲ 100%</span>
                            </div>
                            <div className="w-full h-1 bg-slate-700 mt-2 rounded-full overflow-hidden">
                                <div className="w-full h-full bg-gradient-to-r from-blue-500 to-cyan-500"></div>
                            </div>
                        </div>
                    </div>

                    {/* Decorative Pattern Grid */}
                    <div className="absolute -z-10 -bottom-12 -right-12 text-slate-200">
                        <svg width="200" height="200" fill="currentColor">
                            <pattern id="dots" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
                                <circle cx="2" cy="2" r="2" />
                            </pattern>
                            <rect width="200" height="200" fill="url(#dots)" />
                        </svg>
                    </div>
                </div>

            </div>
        </div>
    );
}
