import { NextResponse } from "next/server";

export async function GET() {
    const mockData = {
        schema: {
            fields: [
                { name: "Date", type: "date" },
                { name: "Category", type: "string" },
                { name: "Sales", type: "number" },
                { name: "Region", type: "string" }
            ]
        },
        qualityScore: 85,
        kpis: [
            { title: "Total Rows", value: "12,450", change: "+12%", trend: "up" },
            { title: "Missing Values", value: "45", change: "-5%", trend: "down" },
            { title: "Unique Categories", value: "8", change: "0%", trend: "neutral" },
            { title: "Total Revenue", value: "$1.2M", change: "+8%", trend: "up" }
        ],
        chartSpecs: [
            {
                id: "trend-1",
                type: "line",
                title: "Sales Trend",
                dataKey: "value",
                categoryKey: "date",
                data: [
                    { date: "Jan", value: 400 },
                    { date: "Feb", value: 300 },
                    { date: "Mar", value: 550 },
                    { date: "Apr", value: 450 },
                    { date: "May", value: 600 },
                    { date: "Jun", value: 750 }
                ]
            },
            {
                id: "cat-1",
                type: "bar",
                title: "Sales by Category",
                dataKey: "amount",
                categoryKey: "name",
                data: [
                    { name: "Electronics", amount: 1200 },
                    { name: "Clothing", amount: 900 },
                    { name: "Home", amount: 1500 },
                    { name: "Books", amount: 400 }
                ]
            },
            {
                id: "comp-1",
                type: "donut",
                title: "Regional Distribution",
                dataKey: "value",
                categoryKey: "name",
                data: [
                    { name: "North", value: 30 },
                    { name: "South", value: 20 },
                    { name: "East", value: 25 },
                    { name: "West", value: 25 }
                ]
            }
        ],
        insights: [
            {
                id: "ins-1",
                title: "Seasonal Spike Detected",
                explanation: "Sales show a significant 25% increase in June compared to previous months.",
                type: "analyst",
                evidence: "Trend analysis of 'Sales' column over 'Date'."
            },
            {
                id: "ins-2",
                title: "Underperforming Category",
                explanation: "Books category is lagging behind others by 40% in total revenue.",
                type: "business",
                evidence: "Aggregation of Sales by Category."
            }
        ],
        cleanedPreview: Array.from({ length: 10 }).map((_, i) => ({
            id: i,
            Date: `2023-0${(i % 6) + 1}-15`,
            Category: ['Electronics', 'Clothing', 'Home', 'Books'][i % 4],
            Sales: Math.floor(Math.random() * 1000) + 100,
            Region: ['North', 'South', 'East', 'West'][i % 4]
        }))
    };

    return NextResponse.json(mockData);
}
