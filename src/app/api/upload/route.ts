import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
    // Mock upload delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    return NextResponse.json({
        jobId: "demo-job-" + Math.floor(Math.random() * 1000),
        status: "submitted"
    });
}
