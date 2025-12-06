'use client';

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot } from 'recharts';
import { Download } from 'lucide-react';
import { useToast } from '../ui/ToastContext';

interface Annotation {
    x: string;
    y: number;
    label: string;
}

interface LineChartCardProps {
    data: any[];
    xKey: string;
    yKey: string;
    annotations?: Annotation[];
    title?: string;
}

export default function LineChartCard({ data, xKey, yKey, annotations, title = "Trend Analysis" }: LineChartCardProps) {
    const { showToast } = useToast();

    return (
        <div className="bg-datapilot-card rounded-[12px] shadow-soft p-6 border border-datapilot-border flex flex-col h-[320px] transition-all hover:shadow-card-hover group relative">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-datapilot-text font-semibold text-lg font-sans">{title}</h3>
                <button
                    onClick={() => showToast("Downloading chart as PNG...", "info")}
                    className="text-datapilot-muted hover:text-datapilot-primary transition-colors p-1 rounded-md hover:bg-slate-50"
                >
                    <Download className="w-5 h-5" />
                </button>
            </div>

            <div className="flex-1 w-full min-h-0 min-w-0">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#00A3FF" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#00A3FF" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E6E9EE" />
                        <XAxis
                            dataKey={xKey}
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#667085', fontSize: 12, fontWeight: 500 }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#667085', fontSize: 12, fontWeight: 500 }}
                            tickFormatter={(val) => `$${val / 1000}k`}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#FFFFFF',
                                border: '1px solid #E6E9EE',
                                borderRadius: '8px',
                                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
                            }}
                            labelStyle={{ color: '#667085', marginBottom: '4px' }}
                            itemStyle={{ color: '#0F172A', fontWeight: '600' }}
                        />
                        <Line
                            type="monotone"
                            dataKey={yKey}
                            stroke="#00A3FF"
                            strokeWidth={3}
                            dot={false}
                            activeDot={{ r: 6, fill: '#00A3FF', stroke: '#fff', strokeWidth: 2 }}
                            fill="url(#colorSales)"
                        />
                        {annotations?.map((ant, idx) => (
                            <ReferenceDot
                                key={idx}
                                x={ant.x}
                                y={ant.y}
                                r={5}
                                fill="#FFB86B"
                                stroke="white"
                                strokeWidth={2}
                                label={{
                                    position: 'top',
                                    value: ant.label,
                                    fill: '#0F172A',
                                    fontSize: 11,
                                    fontWeight: 600,
                                    offset: 10
                                }}
                            />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
