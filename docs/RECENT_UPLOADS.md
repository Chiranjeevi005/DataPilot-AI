# Recent Uploads Feature

## Overview
The Recent Uploads feature tracks and displays the last 10 file uploads in the sidebar, allowing users to quickly access their previous analyses.

## Implementation Details

### Storage
- **State Management**: Uses Zustand store with localStorage persistence
- **Persistence Key**: `datapilot-storage`
- **Max Items**: 10 most recent uploads
- **Persisted Data**: Only `recentUploads` array is persisted to localStorage

### Data Structure
Each recent upload contains:
```typescript
{
  jobId: string;           // Unique job identifier
  fileName: string;        // Original file name
  fileType: FileType;      // 'csv' | 'json' | 'pdf' | 'xlsx'
  fileSize: number;        // File size in bytes
  uploadedAt: string;      // ISO timestamp
  status: 'processing' | 'completed' | 'error';
}
```

### Features
1. **Automatic Tracking**: Uploads are automatically added when a job starts
2. **Status Updates**: Status is updated as jobs progress (processing → completed/error)
3. **Click Navigation**: 
   - Completed jobs → Navigate to results page
   - Processing jobs → Navigate to loading page
   - Error jobs → Navigate to upload page
4. **Visual Indicators**:
   - File type badges (color-coded)
   - Status icons (spinner, checkmark, alert)
   - Relative timestamps (e.g., "2h ago", "just now")
5. **Responsive Design**: Adapts to mobile, tablet, and desktop views

### Usage

#### Accessing Recent Uploads
The sidebar automatically displays recent uploads. Users can:
- View the list in the sidebar
- Click on any upload to navigate to its results/status
- See real-time status updates

#### Programmatic Access
```typescript
import { useAppStore } from '@/lib/store';

// Get recent uploads
const recentUploads = useAppStore((state) => state.recentUploads);

// Add a new upload (done automatically on job start)
const addRecentUpload = useAppStore((state) => state.addRecentUpload);

// Update status
const updateStatus = useAppStore((state) => state.updateRecentUploadStatus);

// Clear all recent uploads
const clearRecentUploads = useAppStore((state) => state.clearRecentUploads);
```

### Persistence
- Recent uploads persist across browser sessions via localStorage
- Only the `recentUploads` array is persisted (not the entire app state)
- Clearing browser data will reset the recent uploads list

### Future Enhancements
- Add ability to delete individual uploads from history
- Add search/filter functionality for recent uploads
- Add ability to export recent uploads list
- Add analytics on upload patterns
