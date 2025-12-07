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

await redis.quit();

return NextResponse.json({
    jobId,
    status: 'submitted'
});

    } catch (error: any) {
    console.error('Upload error:', error);
    return NextResponse.json({
        error: 'Internal Server Error',
        message: error.message
    }, { status: 500 });
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
