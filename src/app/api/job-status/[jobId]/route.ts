import { NextRequest, NextResponse } from 'next/server';
import Redis from 'ioredis';

function getRedisClient() {
    let redisUrl = process.env.REDIS_URL || 'redis://localhost:6379/0';
    if (redisUrl.includes('upstash.io') && redisUrl.startsWith('redis://')) {
        redisUrl = redisUrl.replace('redis://', 'rediss://');
    }
    return new Redis(redisUrl);
}

export async function GET(
    request: NextRequest,
    { params }: { params: { jobId: string } }
) {
    try {
        const { jobId } = params;

        if (!jobId) {
            return NextResponse.json({ error: 'Missing job ID' }, { status: 400 });
        }

        const redis = getRedisClient();
        const jobKey = `job:${jobId}`;
        const dataStr = await redis.get(jobKey);

        if (!dataStr) {
            await redis.quit();
            return NextResponse.json({ error: 'Job not found' }, { status: 404 });
        }

        const data = JSON.parse(dataStr);

        // Check for timeout
        if (data.status === 'processing' && data.timeoutAt) {
            const timeoutAt = new Date(data.timeoutAt);
            const now = new Date();

            if (now > timeoutAt) {
                data.status = 'failed';
                data.error = 'timeout';
                data.errorMessage = 'Job exceeded maximum processing time';
                data.updatedAt = new Date().toISOString();
                await redis.set(jobKey, JSON.stringify(data));
            }
        }

        await redis.quit();

        const response: any = {
            jobId,
            status: data.status,
        };

        if (data.progress) response.progress = data.progress;
        if (data.resultUrl) response.resultUrl = data.resultUrl;
        if (data.error) response.error = data.error;
        if (data.errorMessage) response.errorMessage = data.errorMessage;
        if (data.createdAt) response.createdAt = data.createdAt;
        if (data.updatedAt) response.updatedAt = data.updatedAt;
        if (data.cancelledAt) response.cancelledAt = data.cancelledAt;

        return NextResponse.json(response);

    } catch (error: any) {
        console.error('Job status error:', error);
        return NextResponse.json({
            error: 'Internal Server Error',
            message: error.message
        }, { status: 500 });
    }
}
