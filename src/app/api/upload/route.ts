import { NextRequest, NextResponse } from 'next/server';
import Redis from 'ioredis';

// Get Redis client with SSL support for Upstash
function getRedisClient() {
    let redisUrl = process.env.REDIS_URL || 'redis://localhost:6379/0';

    // Convert to rediss:// for Upstash SSL
    if (redisUrl.includes('upstash.io') && redisUrl.startsWith('redis://')) {
        redisUrl = redisUrl.replace('redis://', 'rediss://');
    }

    return new Redis(redisUrl);
}

export async function POST(request: NextRequest) {
    // Add CORS headers
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    };

    try {
        console.log('[UPLOAD] Starting file upload');

        const formData = await request.formData();
        const file = formData.get('file') as File;

        if (!file) {
            console.error('[UPLOAD] No file provided');
            return NextResponse.json(
                { error: 'No file provided' },
                { status: 400, headers }
            );
        }

        console.log('[UPLOAD] File received:', file.name, file.size, 'bytes');

        // Validate file extension
        const allowedExtensions = ['.csv', '.xlsx', '.xls', '.json', '.pdf'];
        const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

        if (!allowedExtensions.includes(ext)) {
            console.error('[UPLOAD] Invalid extension:', ext);
            return NextResponse.json({
                error: 'Invalid file extension. Allowed: csv, xlsx, xls, json, pdf'
            }, { status: 400, headers });
        }

        // Check file size
        const maxSize = parseInt(process.env.MAX_UPLOAD_SIZE_BYTES || '20971520');
        if (file.size > maxSize) {
            console.error('[UPLOAD] File too large:', file.size, '>', maxSize);
            return NextResponse.json({
                error: 'File too large',
                maxBytes: maxSize
            }, { status: 413, headers });
        }

        // Generate job ID
        const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace('T', '_').substring(0, 15);
        const randomSuffix = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
        const jobId = `job_${timestamp}_${randomSuffix}`;

        console.log('[UPLOAD] Generated jobId:', jobId);

        // Read file data
        const arrayBuffer = await file.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);

        // Save to /tmp
        const fs = await import('fs/promises');
        const path = await import('path');
        const uploadDir = `/tmp/uploads/${jobId}`;
        await fs.mkdir(uploadDir, { recursive: true });
        const filePath = path.join(uploadDir, file.name);
        await fs.writeFile(filePath, buffer);

        console.log('[UPLOAD] File saved to:', filePath);

        // Create job in Redis
        const redis = getRedisClient();
        const now = new Date().toISOString();
        const timeoutSeconds = parseInt(process.env.JOB_TIMEOUT_SECONDS || '600');
        const timeoutAt = new Date(Date.now() + timeoutSeconds * 1000).toISOString();

        const jobData = {
            jobId,
            status: 'submitted',
            fileUrl: filePath,
            fileName: file.name,
            createdAt: now,
            timeoutAt
        };

        const jobKey = `job:${jobId}`;
        await redis.set(jobKey, JSON.stringify(jobData));

        console.log('[UPLOAD] Job created in Redis:', jobKey);

        // Set TTL
        const ttlHours = parseInt(process.env.JOB_TTL_HOURS || '24');
        await redis.expire(jobKey, ttlHours * 3600);

        // Enqueue job
        const queuePayload = {
            jobId,
            fileUrl: filePath,
            fileName: file.name
        };
        await redis.rpush('data_jobs', JSON.stringify(queuePayload));

        console.log('[UPLOAD] Job enqueued');

        await redis.quit();

        return NextResponse.json({
            jobId,
            status: 'submitted'
        }, { headers });

    } catch (error: any) {
        console.error('[UPLOAD] Error:', error);
        return NextResponse.json({
            error: 'Internal Server Error',
            message: error.message,
            stack: error.stack
        }, { status: 500, headers });
    }
}

export async function OPTIONS() {
    return new NextResponse(null, {
        status: 200,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        },
    });
}
