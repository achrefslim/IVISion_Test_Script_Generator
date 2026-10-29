import re
from pathlib import Path
import pdfplumber
from collections import defaultdict

def is_sp_table_pdf(pdf_path: str) -> bool:
    """Return True when the PDF lists splice points as -SP labels (table style wiring diagram)."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                if re.search(r'-SP\d+', page.extract_text() or ""):
                    return True
    except Exception:
        return False
    return False

def generate_ivs_from_new_pdf(pdf_path: str, output_path: str) -> str:
    """Parse a wiring diagram PDF and generate an IVISion script."""
    return generate_generic_pdf_ivs(pdf_path, output_path)

def generate_generic_pdf_ivs(pdf_path: str, output_path: str) -> str:
    """Generic parser for similar wiring diagram PDFs"""
    # Extract all text from PDF with proper layout preservation
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text(layout=True, keep_blank_chars=True) + "\n"

    # 1. Parse SP connections
    sp_connections = defaultdict(list)
    sp_pattern = re.compile(r'-SP(\d+)\s*[^\n]*?((?:-X\d+:\d+|GND\d*:|XX\d+:\d+|X\d+/\d+)[^\n]*)')
    
    for match in sp_pattern.finditer(full_text):
        sp_name = f"SP{match.group(1)}"
        connections_part = match.group(2)
        
        connections = re.findall(r'(-X\d+:[\w/]+|GND\d*:[\w/]*|XX\d+:[\w/]+|X\d+/[\w/]+)', connections_part)
        
        cleaned_connections = []
        for conn in connections:
            if conn.startswith('-X') and ':' in conn:
                parts = conn[1:].split(':')
                cleaned = f"{parts[0]}/{parts[1]}"
                cleaned_connections.append(cleaned)
            elif ':' in conn and not conn.startswith('GND'):
                parts = conn.split(':')
                cleaned = f"{parts[0]}/{parts[1]}"
                cleaned_connections.append(cleaned)
            else:
                cleaned_connections.append(conn.replace(':', '/'))
        
        sp_connections[sp_name].extend(cleaned_connections)

    # 2. Group SPs with shared connections
    connection_groups = defaultdict(list)
    connection_sets = {}
    
    for sp, connections in sp_connections.items():
        conn_set = set()
        for conn in connections:
            if conn.startswith('GND'):
                conn_set.add('GND2')
            else:
                conn_set.add(conn)
        
        key = frozenset(conn_set)
        connection_groups[key].append(sp)
        connection_sets[key] = conn_set

    # Generate TestNetwork statements
    test_networks = []
    for key, sps in connection_groups.items():
        if not connection_sets[key]:
            continue
            
        sorted_sps = sorted(sps, key=lambda x: int(x[2:]))
        sp_group = '-'.join(sorted_sps)
        
        sorted_conns = sorted(
            connection_sets[key],
            key=lambda x: (
                0 if x.startswith('GND') else 1,
                int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0,
                x.split('/')[1] if '/' in x else '0'
            )
        )
        
        tn_line = f'TestNetwork( \'{sp_group}\', Topology= STAR, ' + ', '.join([f'"{c}"' for c in sorted_conns]) + ' );'
        test_networks.append(tn_line)

    # 3. Find direct connections
    direct_connections = set()
    
    table_conn_pattern = re.compile(r'([XG]\w+[/:]\w+)\s*[-\\]\s*([XG]\w+[/:]\w+)')
    for match in table_conn_pattern.finditer(full_text):
        a, b = match.groups()
        a = a.replace(':', '/')
        b = b.replace(':', '/')
        if a != b:
            direct_connections.add((a, b))
    
    colon_conn_pattern = re.compile(r'(?:from\s+)?(-X\d+:\d+)\s+(?:to\s+)?(-X\d+:\d+)', re.IGNORECASE)
    for match in colon_conn_pattern.finditer(full_text):
        a, b = [x[1:].replace(':', '/') for x in match.groups()]
        if a != b:
            direct_connections.add((a, b))
    
    test_connections = []
    for a, b in sorted(direct_connections, key=lambda x: (x[0], x[1])):
        test_connections.append(f'TestConnection( "{a}", "{b}" );')

    # 4. Fixed commands
    fixed_commands = [
        "",
        "UIMessageStop( 'MONTER CP DE X016' );",
        "",
        "DoIsolationTest();",
        "UIMessageStop( ' DEBRANCHER LE CABLAGE ' );",
        "DoUnplugTest();",
        "_Str2 = UIMessageSetVariable ('FA',Size= NORMAL , AllowAbort= ON,HideCharacters= ON, Tout=0s , TextColor= '#FFA500', BackColor='White');",
        "_Str1 = UIMessageSetVariable ('OP-ID',Size= NORMAL , AllowAbort= ON,HideCharacters= ON, Tout=0s , TextColor= '#FFA500', BackColor='White');",
        "",
        "end."
    ]

    # Combine all parts
    full_script = "\n".join(test_networks + [""] + test_connections + fixed_commands)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_script)

    return f"✅ IVISion script generated from generic PDF and saved to: {output_path}"