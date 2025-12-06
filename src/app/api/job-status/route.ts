import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const jobId = searchParams.get('jobId');

    // Validate jobId presence
    if (!jobId) {
        return NextResponse.json({ error: 'Missing jobId' }, { status: 400 });
    }

    // Mock checking status - randomly complete or processing
    // But for the sake of demo flow, let's make it finish quickly or based on polling count if I could track it, 
    // but stateless: just return completed for now to unblock, or "processing" then "completed" randomly.
    // Prompt says: "When status = “completed”, redirect to /results."

    const statuses = ['processing', 'processing', 'completed'];
    const status = statuses[Math.floor(Math.random() * statuses.length)];

    // Force completed for smoother demo if needed, but let's leave it random-ish for "realism" 
    // or just return 'completed' if we want to ensure it works on first/second try. 
    // Let's actually always return 'completed' after a short delay simulation in client, 
    // OR since the client polls every 3s, let's just Random it.

    return NextResponse.json({
        status: 'completed', // Forcing completed for now to ensure flow works easily
        resultUrl: "/api/mock-result"
    });
}
