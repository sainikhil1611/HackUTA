# agentic_rag_sports.py
# pip install -U pip
# pip install pymupdf pypdf sentence-transformers faiss-cpu python-docx rank-bm25 rapidfuzz
# Optional OCR: pip install ocrmypdf

import os, re, json, math, uuid, subprocess, shutil
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

from sentence_transformers import SentenceTransformer
import faiss
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz

# ---------- CONFIG ----------
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K = 6
MMR_LAMBDA = 0.5

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("KB_DIR")) if os.getenv("KB_DIR") else (BASE_DIR / "kb")
INDEX_DIR = BASE_DIR / "index"
INDEX_DIR.mkdir(exist_ok=True, parents=True)

# ---------- UTIL ----------
@dataclass
class KBChunk:
    id: str
    text: str
    meta: Dict[str, Any]

def sliding_window_chunks(txt: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> List[str]:
    txt = re.sub(r"\s+", " ", txt).strip()
    chunks = []
    i = 0
    while i < len(txt):
        chunk = txt[i:i+chunk_size]
        chunks.append(chunk)
        i += (chunk_size - overlap)
        if i >= len(txt):
            break
    return chunks

# ---------- READERS ----------
def read_docx(path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    from docx import Document as DocxDocument
    doc = DocxDocument(str(path))
    items, buf, current_head = [], [], "Document"
    for p in doc.paragraphs:
        style = (p.style.name if p.style else "") or ""
        txt = p.text.strip()
        if not txt:
            continue
        if "Heading" in style:
            if buf:
                items.append(("\n".join(buf), {"section": current_head}))
                buf = []
            current_head = txt
        else:
            buf.append(txt)
    if buf:
        items.append(("\n".join(buf), {"section": current_head}))
    return items

def read_pdf(path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    """Prefer PyMuPDF; fallback to pypdf; skip empty pages and log issues."""
    items: List[Tuple[str, Dict[str, Any]]] = []
    used = None

    # 1) PyMuPDF
    if fitz is not None:
        try:
            doc = fitz.open(str(path))
            for i, page in enumerate(doc, start=1):
                text = page.get_text("text") or ""
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    items.append((text, {"page": i}))
            doc.close()
            used = "pymupdf"
        except Exception as e:
            print(f"[read_pdf] PyMuPDF failed on {path.name}: {e}")

    # 2) pypdf fallback
    if not items:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            for i, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text() or ""
                except Exception as e:
                    print(f"[read_pdf] pypdf page {i} error in {path.name}: {e}")
                    text = ""
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    items.append((text, {"page": i}))
            used = "pypdf"
        except Exception as e:
            print(f"[read_pdf] pypdf failed on {path.name}: {e}")

    if not items:
        print(f"[read_pdf] WARNING: {path.name} produced no text via {used or 'none'} (likely scanned).")

    return items

# ---------- INDEX BUILD / LOAD (with QUICK LOGS) ----------
def build_or_load_indexes(data_dir=DATA_DIR, index_dir=INDEX_DIR):
    # QUICK LOGS just before indexing:
    print("[config] DATA_DIR:", data_dir.resolve())
    print("[config] Exists:", data_dir.exists())
    print("[config] Contents:", [p.name for p in data_dir.glob("*")])

    emb = SentenceTransformer(EMBED_MODEL_NAME)

    meta_path = index_dir / "meta.json"
    faiss_path = index_dir / "faiss.index"
    bm25_path = index_dir / "bm25.json"

    if meta_path.exists() and faiss_path.exists() and bm25_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        if meta:
            index = faiss.read_index(str(faiss_path))
            with open(bm25_path, "r", encoding="utf-8") as f:
                bm25_data = json.load(f)
            bm25 = BM25Okapi([d["text"].split() for d in bm25_data]) if bm25_data else BM25Okapi([["dummy"]])
            print("[index] Loaded existing FAISS/BM25.")
            return emb, index, meta, bm25, bm25_data
        else:
            print("[index] Existing meta.json empty; rebuilding.")

    print(f"[index] Scanning data directory: {data_dir.resolve()}")
    found_paths = list(data_dir.glob("*"))
    print("[index] Found files:", [p.name for p in found_paths])

    chunks: List[KBChunk] = []
    for path in found_paths:
        ext = path.suffix.lower()
        if ext == ".pdf":
            docs = read_pdf(path)
            # Optional OCR if no text and ocrmypdf exists
            if not docs and shutil.which("ocrmypdf"):
                print(f"[index] Attempting OCR on {path.name} ...")
                ocr_out = path.with_name(path.stem + "_ocr.pdf")
                try:
                    subprocess.run(
                        ["ocrmypdf", "--skip-text", "--deskew", "--rotate-pages", str(path), str(ocr_out)],
                        check=True, capture_output=True
                    )
                    docs = read_pdf(ocr_out)
                    if docs:
                        print(f"[index] OCR succeeded for {path.name} → {ocr_out.name}")
                except subprocess.CalledProcessError as e:
                    print(f"[index] OCR failed for {path.name}: {e.stderr.decode(errors='ignore')[:300]}")

        elif ext in (".docx", ".doc"):
            docs = read_docx(path)
        else:
            print(f"[index] Skipping unsupported file type: {path.name}")
            docs = []

        if not docs:
            print(f"[index] No text extracted from {path.name}")
            continue

        for text, dmeta in docs:
            base_meta = {
                "filename": path.name,
                "sport": "basketball" if "basketball" in path.name.lower() else
                         "soccer"     if "soccer"     in path.name.lower() else
                         "tennis"     if "tennis"     in path.name.lower() else "sports",
            }
            base_meta.update(dmeta)
            for ch in sliding_window_chunks(text):
                if ch.strip():
                    chunks.append(KBChunk(id=str(uuid.uuid4()), text=ch, meta=base_meta))

    if not chunks:
        raise RuntimeError(
            "No chunks were created. Either kb path is wrong or PDFs have no extractable text. "
            "Fix path (see [config] logs) OR OCR/convert PDFs to DOCX/TXT."
        )

    texts = [c.text for c in chunks]
    print(f"[index] Prepared {len(texts)} text chunks from {len(found_paths)} files.")

    X = emb.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    if X.ndim != 2 or X.shape[0] == 0:
        raise RuntimeError(f"Embeddings shape {X.shape} — indicates empty inputs. Check extraction logs above.")

    d = X.shape[1]
    faiss.normalize_L2(X)
    index = faiss.IndexFlatIP(d)
    index.add(X)

    meta = [{"id": c.id, "text": c.text, "meta": c.meta} for c in chunks]
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    faiss.write_index(index, str(faiss_path))

    bm25_data = [{"id": c.id, "text": c.text, "meta": c.meta} for c in chunks]
    bm25 = BM25Okapi([d["text"].split() for d in bm25_data])
    with open(bm25_path, "w", encoding="utf-8") as f:
        json.dump(bm25_data, f, ensure_ascii=False, indent=2)

    print("[index] Built FAISS and BM25 indexes successfully.")
    return emb, index, meta, bm25, bm25_data

# ---------- RETRIEVER ----------
def search(query: str, emb: SentenceTransformer, index, meta, bm25, bm25_data, top_k=TOP_K):
    # vector
    qv = emb.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(qv)
    D, I = index.search(qv, top_k*5)
    vec_hits = [(float(D[0][i]), meta[I[0][i]]) for i in range(min(len(I[0]), top_k*5))]

    # lexical
    scores = bm25.get_scores(query.split())
    lex_hits = sorted(
        [(float(scores[i]), bm25_data[i]) for i in range(len(scores))],
        key=lambda x: x[0], reverse=True
    )[:top_k*5]

    # merge by id with best score
    merged = {}
    for s, m in vec_hits + lex_hits:
        key = m["id"]
        if key not in merged or s > merged[key]["score"]:
            merged[key] = {"score": s, "doc": m}

    # MMR diversify on text
    candidates = list(merged.values())
    selected, selected_texts = [], []
    while candidates and len(selected) < top_k:
        best, best_gain = None, -1e9
        for c in candidates:
            sim = 0.0
            if selected_texts:
                sim = max(fuzz.partial_ratio(c["doc"]["text"], st) for st in selected_texts) / 100.0
            gain = MMR_LAMBDA * c["score"] - (1 - MMR_LAMBDA) * sim
            if gain > best_gain:
                best, best_gain = c, gain
        selected.append(best["doc"])
        selected_texts.append(best["doc"]["text"])
        candidates.remove(best)
    return selected

# ---------- TOOLS ----------
def tool_calculator(expr: str) -> str:
    try:
        return str(eval(expr, {"__builtins__": {}}, {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan, "pi": math.pi}))
    except Exception as e:
        return f"CalcError: {e}"

def tool_retriever(q: str, ctx) -> List[Dict[str, Any]]:
    emb, index, meta, bm25, bm25_data = ctx
    return search(q, emb, index, meta, bm25, bm25_data)

# ---------- AGENT LOOP ----------
def plan(query: str) -> List[str]:
    q = query.lower()
    subs = []
    if "angle" in q or "arc" in q:
        subs.append(query)
        subs.append("release angle and entry angle guidance for shots and finishes")
    if "form" in q or "technique" in q:
        subs.append("form and technique cues")
    if not subs:
        subs.append(query)
    return list(dict.fromkeys(subs))  # dedupe keep order

def reflect(draft: str, evidences: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    issues = []
    combined = " ".join([e["text"] for e in evidences]).lower()
    if "angle" in draft.lower() and "angle" not in combined:
        issues.append("Angles mentioned but not grounded; retrieve angle-specific chunks.")
    if len(evidences) == 0:
        issues.append("No evidence retrieved.")
    return (len(issues) == 0), issues

def synthesize_answer(query: str, evidences: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append(f"**Answer (Agentic RAG):**")
    lines.append("")
    for ev in evidences[:4]:
        fn = ev["meta"].get("filename", "")
        sec = ev["meta"].get("section", "")
        pg  = ev["meta"].get("page", "")
        cite = f"({fn}" + (f" • {sec}" if sec else "") + (f" • p.{pg}" if pg else "") + ")"
        snippet = ev["text"].strip()
        snippet = re.sub(r"\s+", " ", snippet)
        lines.append(f"- {snippet}  \n  _Source:_ {cite}")
    lines.append("")
    lines.append("_Synthesis grounded in retrieved KB passages._")
    return "\n".join(lines)

def agentic_answer(query: str, ctx) -> str:
    subgoals = plan(query)
    collected: List[Dict[str, Any]] = []

    for sg in subgoals:
        hits = tool_retriever(sg, ctx)
        def bias(h):
            s = h["text"].lower()
            bonus = 0.0
            if any(k in s for k in ["angle","arc","entry","release"]): bonus += 1.0
            if any(k in s for k in ["form","technique","mechanics","finishing"]): bonus += 0.5
            return bonus
        hits = sorted(hits, key=lambda h: bias(h), reverse=True)[:3]
        collected.extend(hits)

    draft = synthesize_answer(query, collected)
    ok, issues = reflect(draft, collected)
    if not ok:
        refined = query + " " + " ".join(issues)
        collected.extend(tool_retriever(refined, ctx))
        draft = synthesize_answer(query, collected)

    return draft

# ---------- MAIN ----------
if __name__ == "__main__":
    try:
        emb, index, meta, bm25, bm25_data = build_or_load_indexes()
    except Exception as e:
        print("[fatal] Index build/load failed:", e)
        raise

    ctx = (emb, index, meta, bm25, bm25_data)

    # Demo questions
    questions = [
        "Give layup and floater release/entry angle guidance and the form cues to improve consistency.",
        "Summarize basketball jump-shot mechanics and optimal entry angles from the wing.",
        "For soccer, when should I chip versus place across goal, and what launch angles are typical?"
    ]
    for q in questions:
        print("=" * 80)
        print("Q:", q)
        print(agentic_answer(q, ctx))
