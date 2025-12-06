
import sys
import os
import traceback

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

print("--- Starting Diagnostic ---")

print("1. Importing observability...")
try:
    import observability
    print("[OK] observability imported")
except Exception as e:
    print(f"[FAIL] observability import: {e}")
    traceback.print_exc()

print("\n2. Importing lib.analysis.transform_to_ui...")
try:
    from lib.analysis.transform_to_ui import transform_to_ui
    print("[OK] transform_to_ui imported")
except Exception as e:
    print(f"[FAIL] transform_to_ui import: {e}")
    traceback.print_exc()

print("\n3. Importing jobs.process_job...")
try:
    from jobs import process_job
    print("[OK] process_job imported")
except Exception as e:
    print(f"[FAIL] process_job import: {e}")
    traceback.print_exc()

print("\n4. Importing worker...")
try:
    import worker
    print("[OK] worker imported")
except Exception as e:
    print(f"[FAIL] worker import: {e}")
    traceback.print_exc()

print("--- Diagnostic Complete ---")
