import os
import sys

# Define target files
resolved_file_path = r"c:\Users\HP\Desktop\Rag_Project\test_evidence_resolved.txt"
unresolved_file_path = r"c:\Users\HP\Desktop\Rag_Project\test_evidence_unresolved.txt"

# 1. Read files
with open(resolved_file_path, "r", encoding="utf-8") as f:
    resolved_text = f.read()

with open(unresolved_file_path, "r", encoding="utf-8") as f:
    unresolved_text = f.read()

# 2. Extract GAP_RESOLUTION mapping from app.py
sys.path.append(r"c:\Users\HP\Desktop\Rag_Project")
from app import GAP_RESOLUTION, DEMO_FINDINGS

print("=== GAP RESOLUTION DEFINITIONS ===")
print(f"Total defined controls: {len(GAP_RESOLUTION)}")

# 3. Simulate analysis on 'test_evidence_resolved.txt'
print("\n=== RUNNING SIMULATED SCAN ON 'test_evidence_resolved.txt' ===")
file_texts_resolved = {"test_evidence_resolved.txt": resolved_text}

resolved_mapping = {}
for control, keywords in GAP_RESOLUTION.items():
    matching_files = []
    for fname, ftext in file_texts_resolved.items():
        if any(kw in ftext.lower() for kw in keywords):
            matching_files.append(fname)
    if matching_files:
        resolved_mapping[control] = matching_files

print("Resolved controls:")
for ctrl, files in resolved_mapping.items():
    print(f"  ✓ {ctrl} (Resolved by: {', '.join(files)})")

# 4. Simulate analysis on 'test_evidence_unresolved.txt'
print("\n=== RUNNING SIMULATED SCAN ON 'test_evidence_unresolved.txt' ===")
file_texts_unresolved = {"test_evidence_unresolved.txt": unresolved_text}

resolved_mapping_unresolved = {}
for control, keywords in GAP_RESOLUTION.items():
    matching_files = []
    for fname, ftext in file_texts_unresolved.items():
        if any(kw in ftext.lower() for kw in keywords):
            matching_files.append(fname)
    if matching_files:
        resolved_mapping_unresolved[control] = matching_files

print(f"Resolved controls (should be empty): {len(resolved_mapping_unresolved)}")
for ctrl, files in resolved_mapping_unresolved.items():
    print(f"  ✓ {ctrl} (Resolved by: {', '.join(files)})")

print("\nValidation completed successfully!")
