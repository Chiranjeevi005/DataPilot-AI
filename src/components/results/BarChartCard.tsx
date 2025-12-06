'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface BarChartCardProps {
    data: any[];
    xKey: string;
    yKey: string;
}

export default function BarChartCard({ data, xKey, yKey }: BarChartCardProps) {
    return (
        <div className="bg-datapilot-card rounded-[12px] shadow-soft p-6 border border-datapilot-border flex flex-col h-[320px] transition-all hover:shadow-card-hover group">
            <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-datapilot-text font-semibold text-lg font-sans">Sales by Category</h3>
                </div>
                <div className="flex gap-2">
                    <span className="text-xs font-medium px-2 py-1 bg-datapilot-page text-datapilot-muted rounded-full border border-datapilot-border">Top Categories</span>
                </div>
            </div>

            <div className="flex-1 w-full min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E6E9EE" />
                        <XAxis
                            dataKey={xKey}
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#667085', fontSize: 11, fontWeight: 500 }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#667085', fontSize: 11, fontWeight: 500 }}
                        />
                        <Tooltip
                            cursor={{ fill: 'rgba(0,0,0,0.02)' }}
                            contentStyle={{
                                backgroundColor: '#FFFFFF',
                                border: '1px solid #E6E9EE',
                                borderRadius: '8px',
                                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
                            }}
                            labelStyle={{ color: '#667085' }}
                        />
                        <Bar dataKey={yKey} fill="#00C2D1" radius={[4, 4, 0, 0]} barSize={32} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
