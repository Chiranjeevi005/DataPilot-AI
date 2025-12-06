
import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { AnalysisResult } from '@/types/analysis';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ jobId: string }> } // Params are promises in Next.js 15+? Or standard objects?
    // Next 15: props.params is a Promise. Next.js 13/14: it's an object. 
    // Package.json says "next": "16.0.7". So it is Promise.
) {
    const { jobId } = await params;

    if (!jobId) {
        return NextResponse.json({ error: 'Missing jobId' }, { status: 400 });
    }

    const storageRoot = process.env.LOCAL_STORAGE_ROOT || path.join(process.cwd(), 'tmp_uploads');
    const resultPath = path.join(storageRoot, jobId, 'result.json');

    if (!fs.existsSync(resultPath)) {
        return NextResponse.json({ error: 'Result not found', code: 'RESULT_NOT_READY' }, { status: 404 });
    }

    try {
        const fileContent = fs.readFileSync(resultPath, 'utf8');
        const data = JSON.parse(fileContent);

        // Optional: Run runtime type validation here if strictness required?
        // But we trust the Worker. 
        // We inject the extra fields requested in Prompt Part 4

        const responseData: AnalysisResult = {
            ...data,
            isFromCache: true, // It's from file, so sorta cache
            version: "1.0",
            uiOptimized: true
        };

        return NextResponse.json(responseData);
    } catch (e) {
        console.error("Error serving result:", e);
        return NextResponse.json({ error: 'Invalid result file', code: 'LLM_PARSE_FAILURE' }, { status: 500 });
    }
}
