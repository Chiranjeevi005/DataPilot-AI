'use client';

import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface DonutChartCardProps {
    data: { name: string; value: number }[];
}

const COLORS = ['#8A6BFF', '#00C2D1', '#FFB86B', '#00A3FF'];

export default function DonutChartCard({ data }: DonutChartCardProps) {
    const total = data.reduce((acc, curr) => acc + curr.value, 0);

    return (
        <div className="bg-datapilot-card rounded-[12px] shadow-soft p-6 border border-datapilot-border flex flex-col h-[320px] transition-all hover:shadow-card-hover group relative">
            <div className="mb-2">
                <h3 className="text-datapilot-text font-semibold text-lg font-sans">Regional Distribution</h3>
            </div>

            <div className="flex-1 w-full min-h-0 relative">
                <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                    <span className="text-datapilot-muted text-xs font-medium">Total Revenue</span>
                    <span className="text-datapilot-text text-xl font-bold">${(total / 1000).toFixed(1)}k</span>
                </div>

                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="none" />
                            ))}
                        </Pie>
                        <Tooltip
                            formatter={(value: number) => `$${value.toLocaleString()}`}
                            contentStyle={{ borderRadius: '8px', border: '1px solid #E6E9EE' }}
                        />
                        <Legend
                            verticalAlign="bottom"
                            height={36}
                            iconType="circle"
                            iconSize={8}
                            formatter={(value, entry: any) => (
                                <span className="text-datapilot-muted text-xs font-medium ml-1">{value}</span>
                            )}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
