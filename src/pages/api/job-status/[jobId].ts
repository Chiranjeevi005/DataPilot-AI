import type { NextApiRequest, NextApiResponse } from 'next';
import Redis from 'ioredis';

function getRedisClient() {
    let redisUrl = process.env.REDIS_URL || 'redis://localhost:6379/0';
    if (redisUrl.includes('upstash.io') && redisUrl.startsWith('redis://')) {
        redisUrl = redisUrl.replace('redis://', 'rediss://');
    }
    return new Redis(redisUrl);
}

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const { jobId } = req.query;

        console.log('[JOB-STATUS] Checking status for:', jobId);

        if (!jobId || typeof jobId !== 'string') {
            return res.status(400).json({ error: 'Missing job ID' });
        }

        const redis = getRedisClient();
        const jobKey = `job:${jobId}`;
        const dataStr = await redis.get(jobKey);

        if (!dataStr) {
            console.error('[JOB-STATUS] Job not found:', jobKey);
            await redis.quit();
            return res.status(404).json({ error: 'Job not found' });
        }

        const data = JSON.parse(dataStr);
        console.log('[JOB-STATUS] Job data:', data);

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

        console.log('[JOB-STATUS] Returning response:', response);

        return res.status(200).json(response);

    } catch (error: any) {
        console.error('[JOB-STATUS] Error:', error);
        return res.status(500).json({
            error: 'Internal Server Error',
            message: error.message,
            stack: error.stack
        });
    }
}
