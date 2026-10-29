import pandas as pd
from collections import defaultdict, deque
from typing import Optional, Tuple, List, Dict, Set, Union
import os
import fitz  # PyMuPDF
from collections import defaultdict, deque
from typing import List, Tuple, Dict, Set


import re

def clean_address(addr: str) -> str:
    if not isinstance(addr, str):
        return addr
    addr = addr.strip()

    addr = re.sub(r'^(=*\+\s*\w+\s*-\s*)', '', addr, flags=re.IGNORECASE)

    if addr.count(':') == 2:
        first, middle, _ = addr.split(':', 2)
        addr = f"{first}/{middle}"
        return addr

    if '.' in addr and ':' in addr:
        addr = addr.replace(':', '/')
        return addr

    if re.match(r'^[^/:]+/[^/:]+:[^/:]+$', addr):
        parts = addr.split('/')
        if len(parts) == 2 and ':' in parts[1]:
            mid, right = parts[1].split(':', 1)
            addr = f"{parts[0]}.{mid}/{right}"
            return addr

    if addr.count('/') == 2:
        parts = addr.split('/')
        if len(parts) == 3 and parts[1].isdigit():
            addr = f"{parts[0]}.{parts[1]}/{parts[2]}"
            return addr
    if ':' in addr:
        addr = addr.replace(':', '/')
    return addr.strip()






def parse_address(address_str: Optional[str]) -> Optional[Tuple[str, str]]:
    if pd.isna(address_str) or not str(address_str).strip():
        return None
    address_str = str(address_str).strip()
    for delimiter in (":", ".", "/"):
        if delimiter in address_str:
            parts = address_str.split(delimiter)
            device = delimiter.join(parts[:-1]).strip()
            pin = parts[-1].strip()
            if delimiter == ":":
                device = parts[0].strip()
                pin = ":".join(parts[1:]).strip()
            return device, pin
    return address_str, ""


def detect_file_format(df: pd.DataFrame) -> str:
    columns = [str(col).strip().lower() for col in df.columns]

    format_4_col = [
        {"von art/zählnr.", "von anschlusspunkt", "nach art/zählnr.", "nach anschlusspunkt"},
        {"from device name", "from pin", "to device name", "to pin"},
        {"from device", "from pin", "to device", "to pin"}
    ]
    format_2_col = [
        {"von", "nach"},
        {"von betriebsmittelk", "nach betriebsmittelk"},
        {"start", "end"},
        {"from", "to"}
    ]

    for fmt in format_4_col:
        if fmt.issubset(set(columns)):
            return "custom_4"

    for fmt in format_2_col:
        if fmt.issubset(set(columns)):
            return "custom_2"

    if "aderdruck 2" in columns:
        return "model_2"

    if df.shape[1] == 2:
        sample_row = df.dropna(how='all').iloc[0]
        if all("/" in str(cell) for cell in sample_row):
            return "model_1"

    if not df.empty:
        sample_row = df.dropna(how='all').iloc[0]
        for cell in sample_row:
            if pd.notna(cell):
                cell_str = str(cell)
                if ":" in cell_str:
                    return "start_end"
                if "." in cell_str:
                    return "from_to"

    if df.shape[1] == 4:
        simplified_headers = []
        for col in df.columns:
            col_str = str(col).lower().strip()
            if '.' in col_str:
                col_str = col_str.split('.')[0]
            simplified_headers.append(col_str)

        # ✅ Detect model_3
        if simplified_headers.count("pin") == 2 and sum("bmk" in h or "name" in h for h in simplified_headers) >= 2:
            return "model_3"

        # ✅ Detect model_5
        col_set = set(columns)
        if {"produkt-aspekt", "anschluss", "produkt-aspekt1", "anschluss1"}.issubset(col_set):
            return "model_5"

    return "original"








def build_connections_from_manual(df: pd.DataFrame, manual_columns: List[str]) -> List[Tuple[str, str]]:
    df.columns = [col.strip().lower() for col in df.columns]
    for col in manual_columns:
        if col.strip().lower() not in df.columns:
            raise ValueError(f"Manual column '{col}' not found in Excel file.")
    connections = []
    if len(manual_columns) == 4:
        col_map = {
            manual_columns[0].lower(): 'from_device',
            manual_columns[1].lower(): 'from_pin',
            manual_columns[2].lower(): 'to_device',
            manual_columns[3].lower(): 'to_pin'
        }
        df = df.rename(columns=col_map)
        for _, row in df.iterrows():
            from_dev = clean_address(str(row.get('from_device', '')).strip().lstrip('-'))
            from_pin = str(row.get('from_pin', '')).strip()
            to_dev = clean_address(str(row.get('to_device', '')).strip().lstrip('-'))
            to_pin = str(row.get('to_pin', '')).strip()
            if from_dev and to_dev:
                from_full = clean_address(f"{from_dev}/{from_pin}" if from_pin else from_dev)
                to_full = clean_address(f"{to_dev}/{to_pin}" if to_pin else to_dev)
                connections.append((from_full, to_full))
    elif len(manual_columns) == 2:
        col1, col2 = manual_columns
        for _, row in df.iterrows():
            start = parse_address(row.get(col1))
            end = parse_address(row.get(col2))
            if start and end:
                s_dev, s_pin = start
                e_dev, e_pin = end
                from_full = clean_address(f"{s_dev}/{s_pin}" if s_pin else s_dev)
                to_full = clean_address(f"{e_dev}/{e_pin}" if e_pin else e_dev)
                connections.append((from_full, to_full))
    else:
        raise ValueError("Invalid number of manual columns. Must be 2 or 4.")
    if not connections:
        raise ValueError("No valid connections found in manual columns.")
    return connections


def build_connections_auto(df: pd.DataFrame) -> List[Tuple[str, str]]:
    file_format = detect_file_format(df)
    df.columns = [col.strip().lower() for col in df.columns]
    connections = []

    if file_format == "custom_4":
        df = df.rename(columns={
            'von art/zählnr.': 'from_device',
            'von anschlusspunkt': 'from_pin',
            'nach art/zählnr.': 'to_device',
            'nach anschlusspunkt': 'to_pin',
            'from device name': 'from_device',
            'from pin': 'from_pin',
            'to device name': 'to_device',
            'to pin': 'to_pin',
            'from device': 'from_device',
            'to device': 'to_device'
        })
        for _, row in df.iterrows():
            from_dev = clean_address(str(row.get('from_device', '')).strip().lstrip('-'))
            from_pin = str(row.get('from_pin', '')).strip().replace(":", "")
            to_dev = clean_address(str(row.get('to_device', '')).strip().lstrip('-'))
            to_pin = str(row.get('to_pin', '')).strip().replace(":", "")
            if from_dev and to_dev:
                from_full = clean_address(f"{from_dev}/{from_pin}" if from_pin else from_dev)
                to_full = clean_address(f"{to_dev}/{to_pin}" if to_pin else to_dev)
                connections.append((from_full, to_full))

    elif file_format == "custom_2":
        col_map = {
            'von': 'start',
            'nach': 'end',
            'von betriebsmittelk': 'start',
            'nach betriebsmittelk': 'end',
            'start': 'start',
            'end': 'end',
            'from': 'start',
            'to': 'end'
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        for _, row in df.iterrows():
            start = parse_address(row.get('start'))
            end = parse_address(row.get('end'))
            if start and end:
                s_dev, s_pin = start
                e_dev, e_pin = end
                from_full = clean_address(f"{s_dev}/{s_pin.replace(':', '')}" if s_pin else s_dev)
                to_full = clean_address(f"{e_dev}/{e_pin.replace(':', '')}" if e_pin else e_dev)
                connections.append((from_full, to_full))

    elif file_format == "model_1":
        for _, row in df.iterrows():
            a, b = str(row[0]).strip(), str(row[1]).strip()
            a_parts = a.split('/')
            b_parts = b.split('/')
            if len(a_parts) >= 2:
                from_dev = a_parts[0] + '.' + a_parts[1]
                from_pin = a_parts[2].replace(":", "") if len(a_parts) > 2 else ''
                from_full = f"{from_dev}/{from_pin}" if from_pin else from_dev
            else:
                continue
            if len(b_parts) >= 2:
                to_dev = b_parts[0] + '.' + b_parts[1]
                to_pin = b_parts[2].replace(":", "") if len(b_parts) > 2 else ''
                to_full = f"{to_dev}/{to_pin}" if to_pin else to_dev
            else:
                continue
            connections.append((clean_address(from_full), clean_address(to_full)))

    elif file_format == "model_2":
        for _, row in df.iterrows():
            if "aderdruck 2" in df.columns:
                cell = str(row["aderdruck 2"]).strip()
            else:
                cell = str(row[0]).strip()
            if "/" in cell:
                parts = cell.split('/')
                left = parts[0].strip()
                right = parts[1].strip()

                if ':' in left:
                    dev, pin = left.split(':', 1)
                    from_full = f"{dev.strip()}/{pin.strip().replace(':', '')}"
                else:
                    from_full = clean_address(left)

                if ':' in right:
                    dev, pin = right.split(':', 1)
                    to_full = f"{dev.strip()}/{pin.strip().replace(':', '')}"
                else:
                    to_full = clean_address(right)

                connections.append((from_full, to_full))

    elif file_format == "model_3":
        for _, row in df.iterrows():
            name1 = str(row[0]).strip().lstrip('-')
            pin1 = str(row[1]).strip().replace(":", "")
            name2 = str(row[2]).strip().lstrip('-')
            pin2 = str(row[3]).strip().replace(":", "")

            from_full = clean_address(f"{name1}/{pin1}" if pin1 else name1)
            to_full = clean_address(f"{name2}/{pin2}" if pin2 else name2)

            if from_full and to_full:
                connections.append((from_full, to_full))

    elif file_format == "model_4":
        for _, row in df.iterrows():
            try:
                from_dev = str(row["Produkt-aspekt"]).strip().lstrip("-")
                from_pin = str(row["Anschluss"]).strip().replace(":", "")
                to_dev = str(row["Produkt-aspekt.1"]).strip().lstrip("-")
                to_pin = str(row["Anschluss.1"]).strip().replace(":", "")

                if from_dev and to_dev:
                    from_full = f"{from_dev}/{from_pin}" if from_pin else from_dev
                    to_full = f"{to_dev}/{to_pin}" if to_pin else to_dev
                    connections.append((clean_address(from_full), clean_address(to_full)))
            except Exception as e:
                print("⚠️ Model 4 row skipped:", e)
                continue

    elif file_format == "model_5":
        for _, row in df.iterrows():
            try:
                from_dev = str(row["Produkt-aspekt"]).strip().lstrip("-")
                from_pin = str(row["Anschluss"]).strip().replace(":", "")
                to_dev = str(row["Produkt-aspekt1"]).strip().lstrip("-")
                to_pin = str(row["Anschluss1"]).strip().replace(":", "")

                if from_dev and to_dev:
                    from_full = f"{from_dev}/{from_pin}" if from_pin else from_dev
                    to_full = f"{to_dev}/{to_pin}" if to_pin else to_dev
                    connections.append((clean_address(from_full), clean_address(to_full)))
            except Exception as e:
                print("⚠️ Model 5 row skipped:", e)
                continue

    if not connections:
        raise ValueError("No valid connections found in auto-detected format.")
    return connections




import re


def is_sp_like(name: str) -> bool:
    # Normalize and check basic known SP prefixes
    name = name.upper()
    if any(name.startswith(prefix) for prefix in ("SP", "VP", "SPL", "XS", "QV")):
        return True
    # Match XSx:SB pattern like XS8:SB, XS12:SB, etc.
    if re.match(r'^XS\d+:SB$', name, re.IGNORECASE):
        return True
    return False



from collections import defaultdict, deque
from typing import List, Tuple, Dict, Set
import re

def find_sp_clusters(connections: List[Tuple[str, str]]) -> Tuple[List[List[str]], Dict[str, Set[str]], List[Tuple[str, str]]]:
    sp_graph = defaultdict(set)
    sp_to_other = defaultdict(set)
    normal_connections = []

    for from_full, to_full in connections:
        from_dev = from_full.split('/')[0]
        to_dev = to_full.split('/')[0]

        is_sp_from = is_sp_like(from_dev)
        is_sp_to = is_sp_like(to_dev)

        if is_sp_from and is_sp_to:
            sp_graph[from_dev].add(to_dev)
            sp_graph[to_dev].add(from_dev)
        elif is_sp_from:
            sp_graph[from_dev]  # ensure key exists
            sp_to_other[from_dev].add(clean_address(to_full))
        elif is_sp_to:
            sp_graph[to_dev]  # ensure key exists
            sp_to_other[to_dev].add(clean_address(from_full))
        else:
            normal_connections.append((clean_address(from_full), clean_address(to_full)))

    # Group SPs into clusters
    visited = set()
    sp_clusters = []

    for sp in sp_graph:
        if sp not in visited:
            queue = deque([sp])
            cluster = []
            while queue:
                node = queue.popleft()
                if node not in visited:
                    visited.add(node)
                    cluster.append(node)
                    queue.extend(sp_graph[node] - visited)
            if cluster:
                sp_clusters.append(sorted(cluster))

    return sp_clusters, sp_to_other, normal_connections





def generate_complete_ivs_script(file_path: str, output_path: str, manual_columns: Optional[List[str]] = None) -> Union[str, None]:
    def find_resistances(connections: List[Tuple[str, str]]) -> Set[str]:
        resistances = set()
        for from_full, to_full in connections:
            for addr in (from_full, to_full):
                dev = addr.split('/')[0]  # take only the device part (before "/")
                if dev.startswith("R") and dev[1:].isdigit():  # e.g. R726, R104
                    resistances.add(dev)
        return resistances

    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
            df.columns = [str(col).strip().lower() for col in df.columns]
            connections = build_connections_from_manual(df, manual_columns) if manual_columns else build_connections_auto(df)
        else:
            return f"❌ Unsupported file format: {ext}"

        ivs_lines = ["// Auto-generated by Python"]
        sp_clusters, sp_to_other, normal_connections = find_sp_clusters(connections)

        for cluster in sp_clusters:
            label = '-'.join(cluster)
            addresses = set()
            for sp in cluster:
                addresses.update(sp_to_other[sp])
            quoted = ', '.join(f'"{clean_address(addr)}"' for addr in sorted(addresses) if addr)
            sp_name = label.split('/')[0]  # remove the pin from the SP label
            ivs_lines.append(f"TestNetwork( '{sp_name}', Topology= STAR, {quoted} );")

        unique_connections = set()
        for from_full, to_full in normal_connections:
            if (to_full, from_full) not in unique_connections:
                unique_connections.add((clean_address(from_full), clean_address(to_full)))

        for a, b in sorted(unique_connections):
            ivs_lines.append(f'TestConnection( "{a}", "{b}" );')

        # 👉 Add resistance verification comment if needed
        resistances = find_resistances(connections)
        if resistances:
            ivs_lines.append(f"//===> Vérifier si ( {', '.join(sorted(resistances))} ) sont des resistances")

        # Updated footer
        ivs_lines.extend([
            "",
            "DoIsolationTest();",
            "UIMessageStop('DEBRANCHER LE CABLAGE');",
            "",
            "DoUnplugTest();",
            "",
            "_Str2 = UIMessageSetVariable('FA', Size= NORMAL, AllowAbort= ON, HideCharacters= ON,  Tout=0s, TextColor= '#FFA500', BackColor='White');",
            "",
            "_Str1 = UIMessageSetVariable('OP-ID', Size= NORMAL, AllowAbort= ON, HideCharacters= ON, Tout=0s, TextColor= '#FFA500', BackColor='White');",
            "",
            "end."
        ])

        with open(output_path, "w") as file:
            file.write('\n'.join(ivs_lines))

        return f"✅ IVISion script generated successfully:\n{output_path}"

    except Exception as e:
        return f"❌ Error: {str(e)}"


