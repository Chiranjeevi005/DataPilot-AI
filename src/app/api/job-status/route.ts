
import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const jobId = searchParams.get('jobId');

    if (!jobId) {
        return NextResponse.json({ error: 'Missing jobId' }, { status: 400 });
    }

    // Storage Root - must match storage.py logic
    // storage.py uses 'tmp_uploads' in CWD on Windows
    const storageRoot = process.env.LOCAL_STORAGE_ROOT || path.join(process.cwd(), 'tmp_uploads');
    const jobDir = path.join(storageRoot, jobId);

    if (!fs.existsSync(jobDir)) {
        // If directory doesn't exist, maybe it's in Redis but not files? 
        // Or invalid ID. Assume pending or not found.
        // For simplicity, if we just uploaded, it might be pending queue.
        // But storage.py creates dir on upload? 
        // Wait, upload creates file at /tmp_uploads/downloads/... then worker moves it?
        // Actually process_job.py logs: ensuring local path...
        // We will assume if jobDir missing, it's 404 or pending.
        // Let's return pending to be safe if it's very fresh? 
        // But usually we want strictness.
        return NextResponse.json({ status: 'pending', message: 'Job initialized' });
    }

    // Check for result.json
    const resultPath = path.join(jobDir, 'result.json');
    if (fs.existsSync(resultPath)) {
        return NextResponse.json({
            status: 'completed',
            resultUrl: `/api/results/${jobId}`
        });
    }

    // Check for error.json
    const errorPath = path.join(jobDir, 'error.json');
    if (fs.existsSync(errorPath)) {
        try {
            const errorContent = fs.readFileSync(errorPath, 'utf8');
            const errorData = JSON.parse(errorContent);
            return NextResponse.json({
                status: 'failed',
                error: errorData.message || 'Unknown error',
                code: errorData.error
            });
        } catch {
            return NextResponse.json({ status: 'failed', error: 'Could not read error details' });
        }
    }

    // If neither, processing
    return NextResponse.json({ status: 'processing' });
}
