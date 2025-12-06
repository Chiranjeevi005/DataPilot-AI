"use client";

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { KPI } from '@/lib/store';

interface KpiCardProps {
    data: KPI;
}

export default function KpiCard({ data }: KpiCardProps) {
    const isUp = data.trend === 'up';
    const isDown = data.trend === 'down';

    return (
        <Card className="border-none shadow-soft hover:shadow-hover transition-shadow duration-300">
            <CardContent className="p-6">
                <div className="flex flex-col gap-1">
                    <span className="text-sm font-medium text-slate-500 uppercase tracking-wide">{data.title}</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-bold text-slate-900">{data.value}</span>
                        {data.change && (
                            <div className={cn(
                                "flex items-center text-xs font-bold px-2 py-0.5 rounded-full",
                                isUp ? "bg-emerald-100 text-emerald-700" :
                                    isDown ? "bg-rose-100 text-rose-700" :
                                        "bg-slate-100 text-slate-600"
                            )}>
                                {isUp && <ArrowUpRight size={12} className="mr-1" />}
                                {isDown && <ArrowDownRight size={12} className="mr-1" />}
                                {!isUp && !isDown && <Minus size={12} className="mr-1" />}
                                {data.change}
                            </div>
                        )}
                    </div>
                </div>
                {/* Mini sparkline or decorative bar could go here */}
                <div className="h-1 w-full bg-slate-100 mt-4 rounded-full overflow-hidden">
                    <div
                        className={cn("h-full rounded-full", isUp ? "bg-emerald-500" : isDown ? "bg-rose-500" : "bg-slate-400")}
                        style={{ width: '60%' }}
                    />
                </div>
            </CardContent>
        </Card>
    );
}
