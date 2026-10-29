import pandas as pd

def format_value(val):
    if pd.isna(val):
        return ""
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val).strip()

def compare_material_excels(file1: str, file2: str) -> str:
    try:
        # Load both Excel files without headers, define column names
        df1 = pd.read_excel(file1, header=None, names=["name", "quantity", "reference"])
        df2 = pd.read_excel(file2, header=None, names=["name", "quantity", "reference"])

        # Drop empty names
        df1.dropna(subset=["name"], inplace=True)
        df2.dropna(subset=["name"], inplace=True)

        df1.set_index("name", inplace=True)
        df2.set_index("name", inplace=True)

        changes = []
        all_names = set(df1.index) | set(df2.index)

        for name in sorted(all_names):
            row1 = df1.loc[name] if name in df1.index else None
            row2 = df2.loc[name] if name in df2.index else None

            if row1 is None:
                qty2 = format_value(row2["quantity"])
                ref2 = format_value(row2["reference"])
                changes.append(f"➕ Added: {name} → Qty: {qty2}, Ref: {ref2}")
            elif row2 is None:
                qty1 = format_value(row1["quantity"])
                ref1 = format_value(row1["reference"])
                changes.append(f"➖ Removed: {name} → Qty: {qty1}, Ref: {ref1}")
            else:
                # Handle possible duplicates
                if isinstance(row1, pd.DataFrame):
                    row1 = row1.iloc[0]
                if isinstance(row2, pd.DataFrame):
                    row2 = row2.iloc[0]

                qty1 = format_value(row1["quantity"])
                qty2 = format_value(row2["quantity"])
                ref1 = format_value(row1["reference"])
                ref2 = format_value(row2["reference"])

                if qty1 != qty2 or ref1 != ref2:
                    changes.append(
                        f"✏️ Modified: {name}\n"
                        f"    Old → {name}: Qty: {qty1}, Ref: {ref1}\n"
                        f"    New → {name}: Qty: {qty2}, Ref: {ref2}"
                    )

        return "\n".join(changes) if changes else "✅ No differences found between material sheets."

    except Exception as e:
        return f"❌ Error: {str(e)}"
