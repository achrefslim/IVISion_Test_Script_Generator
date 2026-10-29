import os
from pathlib import Path
from typing import Optional, List
import re

import pandas as pd

from ivs_generator import (
    parse_address,
    build_connections_auto,
    build_connections_from_manual,
    find_sp_clusters,
)
from new_pdf_parser import generate_ivs_from_new_pdf, is_sp_table_pdf
from pdf_generator import generate_ivs_from_pdf


def convert_legacy_to_ivs3(legacy_script: str) -> str:
    """
    Convert legacy IVISion script (TestNetwork, TestConnection) into IVISion 3 format (CONNECTION).
    """
    lines = legacy_script.strip().splitlines()
    ivs3_lines = ["DefSec( Section1 );"]

    for line in lines:
        line = line.strip()

        if line.startswith("TestNetwork"):
            try:
                # Extract inside the parentheses
                inner = re.search(r'\((.*?)\)', line)
                if not inner:
                    continue
                content = inner.group(1)

                # Split by 'Topology= STAR,' while being tolerant to extra space
                group_part, conn_part = re.split(r'Topology\s*=\s*STAR\s*,', content, maxsplit=1)

                # Clean the SP/VP group name (remove quotes, commas, and whitespace)
                sp_group = re.sub(r"[',\";]", "", group_part).strip()

                # Extract and clean all connections
                conns = [c.strip().strip('"') for c in conn_part.split(",") if c.strip()]

                ivs3_lines.append(f"CONNECTION ( {sp_group}; {', '.join(conns)} );")
            except Exception:
                continue

        elif line.startswith("TestConnection"):
            try:
                a, b = re.search(r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', line).groups()
                ivs3_lines.append(f"CONNECTION ( {a}, {b} );")
            except Exception:
                continue

    return "\n".join(ivs3_lines)


def generate_ivs3_from_excel_or_pdf(file_path: str, output_path: str, manual_columns: Optional[List[str]] = None) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
            df.columns = [str(col).strip().lower() for col in df.columns]
            connections = (
                build_connections_from_manual(df, manual_columns)
                if manual_columns else
                build_connections_auto(df)
            )
            if not connections:
                return "❌ No valid connections found in Excel file."

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            ivs_lines = ["DefSec( Section1 );"]
            sp_clusters, sp_to_other, normal_connections = find_sp_clusters(connections)

            # Handle SP/VP clusters
            for cluster in sp_clusters:
                label = '-'.join(cluster).replace("'", "").replace(",", "").strip()
                all_nodes = set()
                for sp in cluster:
                    all_nodes.update(sp_to_other.get(sp, []))
                if all_nodes:
                    addr_line = ", ".join(sorted(all_nodes))
                    ivs_lines.append(f"CONNECTION ( {label}; {addr_line} );")

            # Handle direct connections
            unique_connections = set()
            for a, b in normal_connections:
                if (b, a) not in unique_connections:
                    unique_connections.add((a, b))

            for a, b in sorted(unique_connections):
                ivs_lines.append(f"CONNECTION ( {a}, {b} );")

            ivs_lines.append("")  # Final newline for clean end
            with open(output_path, "w", encoding="utf-8") as f:
                f.write('\n'.join(ivs_lines))

            return f"✅ IVISion 3 script generated from Excel:\n{output_path}"

        elif ext == '.pdf':
            filename = Path(file_path).name
            temp_script_path = output_path.replace(".ivs", "_legacy.ivs")

            # Use appropriate parser
            if is_sp_table_pdf(file_path):
                result = generate_ivs_from_new_pdf(file_path, temp_script_path)
            else:
                result = generate_ivs_from_pdf(file_path, temp_script_path)

            if not Path(temp_script_path).exists():
                return "❌ Failed to generate intermediate legacy script."

            legacy_script = Path(temp_script_path).read_text(encoding="utf-8")
            ivs3_script = convert_legacy_to_ivs3(legacy_script)

            Path(output_path).write_text(ivs3_script, encoding="utf-8")
            Path(temp_script_path).unlink(missing_ok=True)

            return f"✅ IVISion 3 script generated from PDF:\n{output_path}"

        else:
            return f"❌ Unsupported file format: {ext}"

    except Exception as e:
        return f"❌ Error while generating IVISion 3 script: {str(e)}"
