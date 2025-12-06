"""
Test worker metrics collection and emission.
Simulates jobs and verifies metrics are correctly tracked.
"""

import os
import sys
import json
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from observability import increment, observe, get_metrics_snapshot, reset_metrics

def test_counter_metrics():
    """Test counter metrics."""
    print("=" * 60)
    print("Testing Counter Metrics...")
    print("=" * 60)
    
    # Reset metrics
    reset_metrics()
    
    # Simulate job processing
    print("\nSimulating 3 jobs:")
    print("  - 1 success")
    print("  - 1 failure")
    print("  - 1 LLM fallback")
    
    # Job 1: Success
    increment("jobs_received_total")
    time.sleep(0.1)
    increment("jobs_completed_total")
    print("✓ Job 1: Completed successfully")
    
    # Job 2: Failure
    increment("jobs_received_total")
    time.sleep(0.1)
    increment("jobs_failed_total")
    print("✓ Job 2: Failed")
    
    # Job 3: LLM Fallback
    increment("jobs_received_total")
    increment("llm_failures_total")
    time.sleep(0.1)
    increment("jobs_completed_total")
    print("✓ Job 3: Completed with LLM fallback")
    
    # Get snapshot
    snapshot = get_metrics_snapshot()
    
    print("\n" + "-" * 60)
    print("Metrics Snapshot:")
    print("-" * 60)
    print(json.dumps(snapshot, indent=2))
    
    # Verify counters
    counters = snapshot.get('counters', {})
    
    print("\n" + "-" * 60)
    print("Verification:")
    print("-" * 60)
    
    expected = {
        "jobs_received_total": 3,
        "jobs_completed_total": 2,
        "jobs_failed_total": 1,
        "llm_failures_total": 1
    }
    
    all_passed = True
    for metric, expected_value in expected.items():
        actual_value = counters.get(metric, 0)
        if actual_value == expected_value:
            print(f"✓ {metric}: {actual_value} (expected: {expected_value})")
        else:
            print(f"✗ {metric}: {actual_value} (expected: {expected_value})")
            all_passed = False
    
    return all_passed

def test_histogram_metrics():
    """Test histogram metrics."""
    print("\n" + "=" * 60)
    print("Testing Histogram Metrics...")
    print("=" * 60)
    
    # Reset metrics
    reset_metrics()
    
    # Simulate processing times
    processing_times = [1.5, 2.3, 3.1, 1.8, 2.7, 4.2, 1.2, 2.9, 3.5, 2.1]
    
    print(f"\nSimulating {len(processing_times)} job processing times:")
    for i, duration in enumerate(processing_times, 1):
        observe("avg_processing_time_seconds", duration)
        print(f"  Job {i}: {duration}s")
    
    # Get snapshot
    snapshot = get_metrics_snapshot()
    
    print("\n" + "-" * 60)
    print("Histogram Statistics:")
    print("-" * 60)
    
    histograms = snapshot.get('histograms', {})
    processing_stats = histograms.get('avg_processing_time_seconds', {})
    
    print(json.dumps(processing_stats, indent=2))
    
    # Verify statistics
    print("\n" + "-" * 60)
    print("Verification:")
    print("-" * 60)
    
    expected_count = len(processing_times)
    expected_sum = sum(processing_times)
    expected_avg = expected_sum / expected_count
    expected_min = min(processing_times)
    expected_max = max(processing_times)
    
    actual_count = processing_stats.get('count', 0)
    actual_sum = processing_stats.get('sum', 0)
    actual_avg = processing_stats.get('avg', 0)
    actual_min = processing_stats.get('min', 0)
    actual_max = processing_stats.get('max', 0)
    
    all_passed = True
    
    if actual_count == expected_count:
        print(f"✓ Count: {actual_count}")
    else:
        print(f"✗ Count: {actual_count} (expected: {expected_count})")
        all_passed = False
    
    if abs(actual_sum - expected_sum) < 0.01:
        print(f"✓ Sum: {actual_sum:.2f}s")
    else:
        print(f"✗ Sum: {actual_sum:.2f}s (expected: {expected_sum:.2f}s)")
        all_passed = False
    
    if abs(actual_avg - expected_avg) < 0.01:
        print(f"✓ Average: {actual_avg:.2f}s")
    else:
        print(f"✗ Average: {actual_avg:.2f}s (expected: {expected_avg:.2f}s)")
        all_passed = False
    
    if abs(actual_min - expected_min) < 0.01:
        print(f"✓ Min: {actual_min:.2f}s")
    else:
        print(f"✗ Min: {actual_min:.2f}s (expected: {expected_min:.2f}s)")
        all_passed = False
    
    if abs(actual_max - expected_max) < 0.01:
        print(f"✓ Max: {actual_max:.2f}s")
    else:
        print(f"✗ Max: {actual_max:.2f}s (expected: {expected_max:.2f}s)")
        all_passed = False
    
    # Check percentiles exist
    if 'p50' in processing_stats and 'p95' in processing_stats and 'p99' in processing_stats:
        print(f"✓ Percentiles calculated (p50: {processing_stats['p50']:.2f}s, "
              f"p95: {processing_stats['p95']:.2f}s, p99: {processing_stats['p99']:.2f}s)")
    else:
        print("✗ Percentiles not calculated")
        all_passed = False
    
    return all_passed

def test_metrics_persistence():
    """Test metrics snapshot persistence."""
    print("\n" + "=" * 60)
    print("Testing Metrics Persistence...")
    print("=" * 60)
    
    # Reset and add some metrics
    reset_metrics()
    increment("jobs_received_total", 5)
    observe("avg_processing_time_seconds", 2.5)
    
    # Try to flush metrics
    try:
        from observability import flush_metrics
        
        print("\nFlushing metrics to storage...")
        result = flush_metrics()
        
        if result:
            print(f"✓ Metrics flushed successfully to: {result}")
            
            # Try to read the file if it's local
            if os.path.exists(result):
                with open(result, 'r') as f:
                    data = json.load(f)
                print("\n" + "-" * 60)
                print("Persisted Metrics:")
                print("-" * 60)
                print(json.dumps(data, indent=2))
                return True
            else:
                print("✓ Metrics flushed to blob storage")
                return True
        else:
            print("✗ Metrics flush failed")
            return False
            
    except Exception as e:
        print(f"✗ Error flushing metrics: {e}")
        return False

def main():
    """Run all metrics tests."""
    print("\n" + "=" * 60)
    print("DataPilot AI - Worker Metrics Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test counters
    results.append(("Counter Metrics", test_counter_metrics()))
    
    # Test histograms
    results.append(("Histogram Metrics", test_histogram_metrics()))
    
    # Test persistence
    results.append(("Metrics Persistence", test_metrics_persistence()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
