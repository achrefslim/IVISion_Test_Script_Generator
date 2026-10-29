# pdf_generator.py

import re
from pathlib import Path
from typing import List
import networkx as nx
import pdfplumber
from jinja2 import Template
from pdf2image import convert_from_path
import pytesseract

# ─────────────── REGEX + TEMPLATES ───────────────
PAIR_RE = re.compile(r'([\w.-]+(?:[:/][\w.-]+)?)\\([\w.-]+(?:[:/][\w.-]+)?)', re.IGNORECASE)
EXCLUDE_WORDS = {'HINWEIS', 'NOTE', 'WARNING', 'ANMERKUNG', 'COMMENT'}

T_P2P = Template('TestConnection( {{a}}, {{b}} );')
T_RESISTOR = Template('TestResistor( {{name}}, {{pin1}}, {{pin2}}, R= {{resistance}} Ohm, Tol+= {{tolerance}} %, Tol-= {{tolerance}} %, Twait=0ms, Tmeas= 10 ms );')
T_MESSAGE = Template('UIMessageStop( {{message}} );')

FOOTER = """
DoIsolationTest();
UIMessageStop( ' DEBRANCHER LE CABLAGE ' );
DoUnplugTest();
_Str2 = UIMessageSetVariable ('FA',Size= NORMAL , AllowAbort= ON,HideCharacters= ON, Tout=0s , TextColor= '#FFA500', BackColor='White');
_Str1 = UIMessageSetVariable ('OP-ID',Size= NORMAL , AllowAbort= ON,HideCharacters= ON, Tout=0s , TextColor= '#FFA500', BackColor='White');
end.
""".lstrip()

# ─────────────── OCR + TEXT ───────────────
def ocr_page(pdf_path: Path, page_no: int) -> str:
    img = convert_from_path(str(pdf_path), first_page=page_no, last_page=page_no, dpi=300)[0]
    return pytesseract.image_to_string(img.convert("L"), config="--psm 11 --oem 1")

def extract_text(pdf_path: Path) -> str:
    chunks = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx, page in enumerate(pdf.pages, 1):
            txt = page.extract_text() or ""
            chunks.append(txt if txt.strip() else ocr_page(pdf_path, idx))
    return "\n".join(chunks)

# ─────────────── GRAPH UTILS ───────────────
def norm(raw: str) -> str:
    s = raw.replace(":", "/").strip().upper()
    return s[:-1] if s.endswith("/") else s

def is_junk(node: str) -> bool:
    return (
        not node or len(node) < 3 or any(w in node for w in EXCLUDE_WORDS) or "\\" in node
    )

def build_graph(text: str) -> nx.Graph:
    g = nx.Graph()
    for m in PAIR_RE.finditer(text):
        a, b = map(norm, m.groups())
        if is_junk(a) or is_junk(b):
            continue
        g.add_edge(a, b)
    return g

# ─────────────── CONNECTION EMISSION ───────────────
def emit_component(nodes: List[str]) -> List[str]:
    lines = []
    sp_nodes = [n for n in nodes if re.fullmatch(r"SP\d+", n.upper())]
    
    if len(sp_nodes) == 1 and len(nodes) > 1:
        # STAR topology case
        sp = sp_nodes[0]
        other_nodes = [f'"{n}"' for n in nodes if n != sp]
        lines.append(f"TestNetwork( '{sp}', Topology= STAR, {', '.join(other_nodes)} );")
    else:
        # Default pairwise TestConnection logic
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a, b = nodes[i], nodes[j]
                if any(n.startswith("K") for n in [a, b]):
                    k_pin = a if a.startswith("K") else b
                    other_pin = b if a.startswith("K") else a
                    if "/85" in k_pin and "/86" in k_pin.replace("/85", "/86"):
                        k_name = k_pin.split("/")[0]
                        lines.append(T_RESISTOR.render(name=f"'{k_name}'", pin1=f'"{k_pin}"',
                                                       pin2=f'"{other_pin}"', resistance=85, tolerance=35))
                        lines.append(T_MESSAGE.render(message=f"'monter {k_name}'"))
                lines.append(T_P2P.render(a=f'"{a}"', b=f'"{b}"'))
    
    return lines


def graph_to_code(g: nx.Graph) -> str:
    code_lines = []
    for comp in sorted(nx.connected_components(g), key=lambda c: (-len(c), sorted(c))):
        code_lines.extend(emit_component(sorted(comp)))
    code_lines.append(FOOTER)
    return "\n".join(code_lines)

# ─────────────── MAIN FUNCTION TO USE IN GUI ───────────────
def generate_ivs_from_pdf(pdf_path: str, output_path: str) -> str:
    text = extract_text(Path(pdf_path))
    g = build_graph(text)
    if g.number_of_edges() == 0:
        return "❌ Error: No valid labeled connections found in PDF file."
    code = graph_to_code(g)
    Path(output_path).write_text(code, encoding="utf-8")
    return f"✅ Generated IVISion script with {g.number_of_edges()} connections."