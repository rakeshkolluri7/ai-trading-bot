from src.scanner import scan_market
import sys

# Force output to see what's happening
print("--- RUNNING DIAGNOSTIC SCAN ---")
try:
    best, report = scan_market("All") 
    print(f"\nFound {len(report)} candidates.")
    if best:
        print(f"Top Pick: {best}")
    else:
        print("No candidates met the threshold.")
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
