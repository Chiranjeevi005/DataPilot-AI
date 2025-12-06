'use client';

import React from 'react';
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { clsx } from 'clsx';

interface KpiCardProps {
    title: string;
    value: string;
    delta: string;
    deltaType: 'pos' | 'neg' | 'neutral';
    sparklineData: { value: number }[];
    progressValue?: number; // 0-100
}

export default function KpiCard({ title, value, delta, deltaType, sparklineData, progressValue }: KpiCardProps) {
    const isPos = deltaType === 'pos';
    const isNeg = deltaType === 'neg';

    return (
        <div className="bg-datapilot-card rounded-[12px] shadow-soft p-5 border border-datapilot-border flex flex-col justify-between h-[140px] transition-all hover:-translate-y-1 hover:shadow-card-hover group relative overflow-hidden">
            {/* Glow on hover */}
            <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-datapilot-primary to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            <div className="flex justify-between items-start">
                <div>
                    <h3 className="text-datapilot-muted text-sm font-medium mb-1 font-sans">{title}</h3>
                    <div className="text-2xl font-bold text-datapilot-text tracking-tight font-sans">{value}</div>
                </div>
                <div className={clsx(
                    "flex items-center text-xs font-semibold px-2 py-1 rounded-full",
                    isPos && "bg-green-100 text-datapilot-success",
                    isNeg && "bg-red-100 text-datapilot-danger",
                    !isPos && !isNeg && "bg-gray-100 text-datapilot-muted"
                )}>
                    {isPos && <ArrowUpRight className="w-3 h-3 mr-1" />}
                    {isNeg && <ArrowDownRight className="w-3 h-3 mr-1" />}
                    {!isPos && !isNeg && <Minus className="w-3 h-3 mr-1" />}
                    {delta}
                </div>
            </div>

            <div className="flex items-end justify-between mt-2">
                {/* Progress Bar or Sparkline footer */}
                <div className="w-full flex items-center justify-between gap-4">
                    {/* Progress Bar (Subtle) */}
                    {progressValue !== undefined && (
                        <div className="w-16 h-1 bg-datapilot-border rounded-full overflow-hidden">
                            <div
                                className="h-full bg-datapilot-primary rounded-full"
                                style={{ width: `${progressValue}%` }}
                            />
                        </div>
                    )}

                    {/* Sparkline */}
                    <div className="h-8 w-24">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={sparklineData}>
                                <defs>
                                    <linearGradient id={`colorSpark-${title}`} x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={isNeg ? '#FF6B6B' : '#00A3FF'} stopOpacity={0.3} />
                                        <stop offset="95%" stopColor={isNeg ? '#FF6B6B' : '#00A3FF'} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <YAxis hide domain={['dataMin', 'dataMax']} />
                                <Area
                                    type="monotone"
                                    dataKey="value"
                                    stroke={isNeg ? '#FF6B6B' : '#00A3FF'}
                                    fillOpacity={1}
                                    fill={`url(#colorSpark-${title})`}
                                    strokeWidth={2}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}
