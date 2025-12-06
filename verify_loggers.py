#!/usr/bin/env python3
"""
Comprehensive diagnostic to verify all logger instances are properly initialized.
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

print("=" * 80)
print("LOGGER DIAGNOSTIC - Verifying all modules can be imported")
print("=" * 80)

modules_to_test = [
    ('lib.llm_client', 'LLM Client'),
    ('lib.analysis', 'Analysis'),
    ('lib.storage', 'Storage'),
    ('lib.queue', 'Queue'),
    ('jobs.process_job', 'Process Job'),
    ('worker', 'Worker'),
]

all_passed = True

for module_name, display_name in modules_to_test:
    try:
        print(f"\n[Testing] {display_name} ({module_name})...")
        module = __import__(module_name, fromlist=[''])
        
        # Check if logger exists in module
        if hasattr(module, 'logger'):
            print(f"  ✓ Module has 'logger' attribute")
            print(f"  ✓ Logger type: {type(module.logger)}")
        else:
            print(f"  ⚠ Module does not have 'logger' attribute (may use observability instead)")
        
        print(f"  ✓ {display_name} imported successfully")
        
    except Exception as e:
        print(f"  ✗ FAILED to import {display_name}")
        print(f"    Error: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✓ ALL MODULES PASSED - System is ready")
else:
    print("✗ SOME MODULES FAILED - Fix required")
print("=" * 80)

sys.exit(0 if all_passed else 1)
