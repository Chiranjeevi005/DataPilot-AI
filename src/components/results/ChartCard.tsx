"use client";

import React from 'react';
import { ResponsiveContainer, LineChart, Line, BarChart, Bar, PieChart, Pie, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, AreaChart, Area } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartSpec } from '@/lib/store';
import { useMediaQuery } from '@/hooks/use-media-query';

interface ChartCardProps {
    spec: ChartSpec;
}

const COLORS = ['#2563EB', '#06B6D4', '#7F5BFF', '#F59E0B', '#10B981'];

export default function ChartCard({ spec }: ChartCardProps) {
    const isMobile = useMediaQuery('(max-width: 640px)');

    const axisStyle = {
        fontSize: isMobile ? 10 : 12,
        stroke: "#94A3B8"
    };

    const renderChart = () => {
        switch (spec.type) {
            case 'line':
                return (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={spec.data} margin={{ top: 10, right: 10, left: isMobile ? -20 : 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id={`grad-${spec.id}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" opacity={isMobile ? 0.5 : 1} />
                            <XAxis
                                dataKey={spec.categoryKey}
                                {...axisStyle}
                                tickLine={false}
                                axisLine={false}
                                tick={{ fontSize: axisStyle.fontSize }}
                                interval={isMobile ? 'preserveStartEnd' : 0}
                            />
                            <YAxis
                                {...axisStyle}
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={(value) => `${value}`}
                                width={isMobile ? 30 : 40}
                                tick={{ fontSize: axisStyle.fontSize }}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #E2E8F0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', fontSize: isMobile ? '12px' : '14px' }}
                                itemStyle={{ color: '#1E293B' }}
                            />
                            <Area type="monotone" dataKey={spec.dataKey} stroke="#2563EB" strokeWidth={isMobile ? 2 : 3} fillOpacity={1} fill={`url(#grad-${spec.id})`} />
                        </AreaChart>
                    </ResponsiveContainer>
                );
            case 'bar':
                return (
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={spec.data} margin={{ top: 10, right: 10, left: isMobile ? -20 : 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" opacity={isMobile ? 0.5 : 1} />
                            <XAxis
                                dataKey={spec.categoryKey}
                                {...axisStyle}
                                tickLine={false}
                                axisLine={false}
                                tick={{ fontSize: axisStyle.fontSize }}
                            />
                            <YAxis
                                {...axisStyle}
                                tickLine={false}
                                axisLine={false}
                                width={isMobile ? 30 : 40}
                                tick={{ fontSize: axisStyle.fontSize }}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #E2E8F0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', fontSize: isMobile ? '12px' : '14px' }}
                                cursor={{ fill: '#F1F5F9' }}
                            />
                            <Bar dataKey={spec.dataKey} fill="#06B6D4" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                );
            case 'donut':
                return (
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={spec.data}
                                innerRadius={isMobile ? 45 : 60}
                                outerRadius={isMobile ? 65 : 80}
                                paddingAngle={5}
                                dataKey={spec.dataKey}
                            >
                                {spec.data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #E2E8F0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', fontSize: isMobile ? '12px' : '14px' }}
                            />
                            <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: isMobile ? '10px' : '12px' }} />
                        </PieChart>
                    </ResponsiveContainer>
                );
            default:
                return <div>Unsupported chart type</div>;
        }
    };

    return (
        <Card className="h-[400px] border-none shadow-soft hover:shadow-hover transition-shadow duration-300 flex flex-col">
            <CardHeader>
                <CardTitle className="text-lg font-bold text-slate-800">{spec.title}</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 min-h-0">
                {renderChart()}
            </CardContent>
        </Card>
    );
}
