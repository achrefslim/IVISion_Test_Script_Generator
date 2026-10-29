import pandas as pd
from typing import Set, Tuple, List
from ivs_generator import build_connections_auto

def normalize_connection(a: str, b: str) -> Tuple[str, str]:
    """Return a sorted tuple of two nodes (ignores order)."""
    return tuple(sorted([a.strip(), b.strip()]))

def extract_connections_from_file(file_path: str) -> Set[Tuple[str, str]]:
    """Extract normalized connections from Excel file using build_connections_auto."""
    df = pd.read_excel(file_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    connections = build_connections_auto(df)
    normalized = set(normalize_connection(a, b) for a, b in connections)
    return normalized

def compare_connection_sets(set1: Set[Tuple[str, str]], set2: Set[Tuple[str, str]]) -> dict:
    """Compare two connection sets. Returns dict with keys: added, removed, unchanged"""
    return {
        "added": sorted(set2 - set1),
        "removed": sorted(set1 - set2),
        "unchanged": sorted(set1 & set2),
    }

def compare_excels(file1: str, file2: str) -> str:
    """Compare connections in two Excel files and return a readable report."""
    try:
        set1 = extract_connections_from_file(file1)
        set2 = extract_connections_from_file(file2)
    except Exception as e:
        return f"❌ Error reading Excel files: {e}"

    result = compare_connection_sets(set1, set2)
    report_lines = ["🔍 Excel Connection Comparison Result:", ""]

    if result["added"]:
        report_lines.append("🟢 Added Connections:")
        for a, b in result["added"]:
            report_lines.append(f"  - {a} ↔ {b}")

    if result["removed"]:
        report_lines.append("\n🔴 Removed Connections:")
        for a, b in result["removed"]:
            report_lines.append(f"  - {a} ↔ {b}")

    if not result["added"] and not result["removed"]:
        report_lines.append("✅ No changes detected between files.")

    return "\n".join(report_lines)
