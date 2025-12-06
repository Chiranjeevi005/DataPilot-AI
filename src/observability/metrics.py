"""
Metrics collection and emission for DataPilot AI.
Emits counters and histograms to JSON snapshots for analysis.
"""

import os
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict

class MetricsCollector:
    """
    Collects and emits metrics to JSON snapshots.
    
    Supported metrics:
    - jobs_received_total (counter)
    - jobs_completed_total (counter)
    - jobs_failed_total (counter)
    - llm_failures_total (counter)
    - blob_failures_total (counter)
    - avg_processing_time_seconds (histogram)
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.counters: Dict[str, int] = defaultdict(int)
        self.histograms: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()
        self.last_flush = datetime.utcnow()
        
        # Configuration
        self.flush_interval = int(os.getenv('METRICS_FLUSH_INTERVAL', '10'))
        self.metrics_path = os.getenv('METRICS_SNAPSHOT_PATH', 'metrics/metrics_snapshot.json')
        
        # Auto-flush thread
        self.auto_flush_enabled = os.getenv('METRICS_AUTO_FLUSH', 'true').lower() == 'true'
        if self.auto_flush_enabled:
            self._start_auto_flush()
    
    def _start_auto_flush(self):
        """Start background thread for periodic metric flushing."""
        def auto_flush_worker():
            while self.auto_flush_enabled:
                time.sleep(self.flush_interval)
                try:
                    self.flush()
                except Exception as e:
                    print(f"[METRICS] Auto-flush error: {e}")
        
        thread = threading.Thread(target=auto_flush_worker, daemon=True)
        thread.start()
    
    def increment(self, metric_name: str, value: int = 1):
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the metric
            value: Amount to increment (default: 1)
        """
        with self.lock:
            self.counters[metric_name] += value
    
    def observe(self, metric_name: str, value: float):
        """
        Record an observation for a histogram metric.
        
        Args:
            metric_name: Name of the metric
            value: Observed value
        """
        with self.lock:
            self.histograms[metric_name].append(value)
    
    def get_snapshot(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.
        
        Returns:
            Dictionary containing all metrics
        """
        with self.lock:
            snapshot = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "counters": dict(self.counters),
                "histograms": {},
            }
            
            # Calculate histogram statistics
            for metric_name, values in self.histograms.items():
                if values:
                    snapshot["histograms"][metric_name] = {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "p50": self._percentile(values, 50),
                        "p95": self._percentile(values, 95),
                        "p99": self._percentile(values, 99),
                    }
                else:
                    snapshot["histograms"][metric_name] = {
                        "count": 0,
                        "sum": 0,
                        "avg": 0,
                        "min": 0,
                        "max": 0,
                        "p50": 0,
                        "p95": 0,
                        "p99": 0,
                    }
            
            return snapshot
    
    def _percentile(self, values: list, percentile: int) -> float:
        """
        Calculate percentile of values.
        
        Args:
            values: List of values
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile value
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100.0))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def flush(self) -> Optional[str]:
        """
        Flush metrics to blob storage or local file.
        
        Returns:
            Path where metrics were saved, or None on error
        """
        try:
            snapshot = self.get_snapshot()
            
            # Try to save to blob storage first
            blob_enabled = os.getenv('BLOB_ENABLED', 'false').lower() == 'true'
            
            if blob_enabled:
                try:
                    from lib import storage
                    import io
                    
                    # Create snapshot file
                    snapshot_json = json.dumps(snapshot, indent=2)
                    snapshot_stream = io.BytesIO(snapshot_json.encode('utf-8'))
                    
                    # Generate unique filename with timestamp
                    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                    filename = f"metrics_snapshot_{timestamp}.json"
                    
                    # Save to blob (using a special job_id for metrics)
                    blob_path = storage.save_file_to_blob(
                        snapshot_stream,
                        filename,
                        job_id="metrics"
                    )
                    
                    self.last_flush = datetime.utcnow()
                    print(f"[METRICS] Flushed to blob: {blob_path}")
                    return blob_path
                    
                except Exception as e:
                    print(f"[METRICS] Failed to flush to blob: {e}, falling back to local")
            
            # Fallback to local file
            local_path = self.metrics_path
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, 'w') as f:
                json.dump(snapshot, f, indent=2)
            
            self.last_flush = datetime.utcnow()
            print(f"[METRICS] Flushed to local: {local_path}")
            return local_path
            
        except Exception as e:
            print(f"[METRICS] Flush error: {e}")
            return None
    
    def reset(self):
        """Reset all metrics (useful for testing)."""
        with self.lock:
            self.counters.clear()
            self.histograms.clear()

# Global metrics collector instance
_metrics_collector = MetricsCollector()

def increment(metric_name: str, value: int = 1):
    """
    Increment a counter metric.
    
    Args:
        metric_name: Name of the metric
        value: Amount to increment (default: 1)
    """
    _metrics_collector.increment(metric_name, value)

def observe(metric_name: str, value: float):
    """
    Record an observation for a histogram metric.
    
    Args:
        metric_name: Name of the metric
        value: Observed value
    """
    _metrics_collector.observe(metric_name, value)

def flush_metrics() -> Optional[str]:
    """
    Flush metrics to storage.
    
    Returns:
        Path where metrics were saved, or None on error
    """
    return _metrics_collector.flush()

def get_metrics_snapshot() -> Dict[str, Any]:
    """
    Get current metrics snapshot.
    
    Returns:
        Dictionary containing all metrics
    """
    return _metrics_collector.get_snapshot()

def reset_metrics():
    """Reset all metrics (useful for testing)."""
    _metrics_collector.reset()
