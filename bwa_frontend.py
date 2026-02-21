from __future__ import annotations

import json
import os
import re
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional, List, Iterator, Tuple

import pandas as pd
import streamlit as st

from bwa_backend import app

# ─────────────────────────────────────────────
# Page config — must be FIRST streamlit call
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BlogForge AI",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Global CSS — dark editorial theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── Root variables ── */
:root {
    --bg:          #0d0f14;
    --bg-card:     #13161e;
    --bg-hover:    #1a1e2a;
    --border:      #252836;
    --border-bright: #353a50;
    --gold:        #f5a623;
    --gold-dim:    #b8741a;
    --teal:        #2dd4c4;
    --red:         #ff5e5e;
    --text-primary: #eef0f6;
    --text-secondary: #8a90a8;
    --text-muted:   #555a72;
    --radius:       10px;
    --shadow:       0 4px 24px rgba(0,0,0,.45);
}

/* ── Base ── */
html, body, [data-testid="stApp"] {
    background: var(--bg) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { font-family: 'DM Sans', sans-serif !important; }

/* ── Typography ── */
h1, h2, h3 { font-family: 'DM Serif Display', serif !important; }

/* ── Inputs ── */
textarea, input[type="text"], [data-baseweb="textarea"] {
    background: var(--bg) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    transition: border-color .2s;
}
textarea:focus, input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px rgba(245,166,35,.12) !important;
}

/* ── Primary button ── */
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dim) 100%) !important;
    color: #0d0f14 !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: .3px !important;
    padding: 0.55rem 1.4rem !important;
    transition: opacity .2s, transform .15s !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    opacity: .9 !important;
    transform: translateY(-1px) !important;
}

/* ── Secondary button ── */
[data-testid="stButton"] > button:not([kind="primary"]) {
    background: transparent !important;
    border: 1px solid var(--border-bright) !important;
    color: var(--text-secondary) !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    transition: border-color .2s, color .2s !important;
}
[data-testid="stButton"] > button:not([kind="primary"]):hover {
    border-color: var(--gold) !important;
    color: var(--gold) !important;
}

/* ── Download buttons ── */
[data-testid="stDownloadButton"] > button {
    background: transparent !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: var(--radius) !important;
    color: var(--teal) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: .4px !important;
    transition: all .2s !important;
}
[data-testid="stDownloadButton"] > button:hover {
    border-color: var(--teal) !important;
    background: rgba(45,212,196,.08) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid var(--border) !important;
    gap: 4px !important;
}
[data-testid="stTabs"] [role="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    background: transparent !important;
    border: none !important;
    border-radius: 6px 6px 0 0 !important;
    padding: .45rem .9rem !important;
    transition: color .2s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--gold) !important;
    border-bottom: 2px solid var(--gold) !important;
    background: rgba(245,166,35,.06) !important;
}
[data-testid="stTabs"] [role="tab"]:hover { color: var(--text-primary) !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden;
}
[data-testid="stDataFrame"] th {
    background: var(--bg-hover) !important;
    color: var(--gold) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: .5px !important;
    text-transform: uppercase !important;
}
[data-testid="stDataFrame"] td {
    font-size: 12.5px !important;
    color: var(--text-secondary) !important;
}

/* ── JSON viewer ── */
[data-testid="stJson"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
}

/* ── Status / spinner ── */
[data-testid="stStatus"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stStatusWidget"] { color: var(--teal) !important; }

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    font-size: 13.5px !important;
}

/* ── Radio buttons (past blogs) ── */
[data-testid="stRadio"] label {
    font-size: 12.5px !important;
    color: var(--text-secondary) !important;
    padding: 4px 0 !important;
    transition: color .15s !important;
}
[data-testid="stRadio"] label:hover { color: var(--text-primary) !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary {
    font-size: 13px !important;
    color: var(--text-secondary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Logs textarea ── */
[data-testid="stTextArea"] textarea {
    font-family: 'DM Mono', monospace !important;
    font-size: 11.5px !important;
    background: #080a0f !important;
    color: #6bffb8 !important;
    line-height: 1.6 !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Scrollbar ── */
* { scrollbar-width: thin; scrollbar-color: var(--border-bright) transparent; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 99px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Custom HTML components
# ─────────────────────────────────────────────
def hero_header():
    st.markdown("""
    <div style="
        padding: 2.5rem 0 1.8rem 0;
        border-bottom: 1px solid #252836;
        margin-bottom: 1.8rem;
    ">
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:.5rem;">
            <div style="
                width:42px; height:42px; border-radius:10px;
                background: linear-gradient(135deg,#f5a623,#b8741a);
                display:flex; align-items:center; justify-content:center;
                font-size:20px; flex-shrink:0;
            ">✍️</div>
            <div>
                <div style="
                    font-family:'DM Serif Display',serif;
                    font-size:1.9rem; font-weight:400; color:#eef0f6;
                    line-height:1.1;
                ">BlogForge <span style="color:#f5a623;">AI</span></div>
            </div>
        </div>
        <p style="
            color:#8a90a8; font-size:14px; margin:0; max-width:640px; line-height:1.6;
        ">
            Orchestrator–worker AI agent that plans, researches, writes, and illustrates
            full blog posts end-to-end — powered by LangGraph + Gemini.
        </p>
    </div>
    """, unsafe_allow_html=True)


def stat_card(label: str, value: str, accent: str = "#f5a623"):
    st.markdown(f"""
    <div style="
        background:#13161e; border:1px solid #252836; border-radius:10px;
        padding:1rem 1.2rem; height:100%;
    ">
        <div style="color:#555a72; font-size:11px; letter-spacing:.6px;
                    text-transform:uppercase; font-family:'DM Mono',monospace;
                    margin-bottom:.35rem;">{label}</div>
        <div style="color:{accent}; font-family:'DM Serif Display',serif;
                    font-size:1.55rem; font-weight:400;">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def section_heading(text: str, sub: str = ""):
    st.markdown(f"""
    <div style="margin: 1.4rem 0 1rem 0;">
        <div style="font-family:'DM Serif Display',serif; font-size:1.25rem;
                    color:#eef0f6;">{text}</div>
        {"<div style='color:#8a90a8;font-size:13px;margin-top:.25rem;'>"+sub+"</div>" if sub else ""}
    </div>
    """, unsafe_allow_html=True)


def blog_card(title: str, filename: str, mtime: str):
    st.markdown(f"""
    <div style="
        background:#13161e; border:1px solid #252836; border-radius:8px;
        padding:.7rem .9rem; margin-bottom:.4rem;
        transition: border-color .2s;
    ">
        <div style="color:#eef0f6; font-size:13px; font-weight:500;
                    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
            {title}
        </div>
        <div style="color:#555a72; font-family:'DM Mono',monospace;
                    font-size:10.5px; margin-top:.2rem;">
            {filename} · {mtime}
        </div>
    </div>
    """, unsafe_allow_html=True)


def node_badge(name: str):
    st.markdown(f"""
    <div style="
        display:inline-flex; align-items:center; gap:7px;
        background:#1a1e2a; border:1px solid #353a50;
        border-radius:6px; padding:.3rem .75rem;
        font-family:'DM Mono',monospace; font-size:12px; color:#2dd4c4;
        margin:.2rem 0;
    ">
        <span style="color:#f5a623;">▶</span> {name}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Helpers (unchanged logic, same as original)
# ─────────────────────────────────────────────
def safe_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"


def bundle_zip(md_text: str, md_filename: str, images_dir: Path) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(md_filename, md_text.encode("utf-8"))
        if images_dir.exists() and images_dir.is_dir():
            for p in images_dir.rglob("*"):
                if p.is_file():
                    z.write(p, arcname=str(p))
    return buf.getvalue()


def images_zip(images_dir: Path) -> Optional[bytes]:
    if not images_dir.exists() or not images_dir.is_dir():
        return None
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in images_dir.rglob("*"):
            if p.is_file():
                z.write(p, arcname=str(p))
    return buf.getvalue()


def try_stream(graph_app, inputs: Dict[str, Any]) -> Iterator[Tuple[str, Any]]:
    try:
        for step in graph_app.stream(inputs, stream_mode="updates"):
            yield ("updates", step)
        out = graph_app.invoke(inputs)
        yield ("final", out)
        return
    except Exception:
        pass
    try:
        for step in graph_app.stream(inputs, stream_mode="values"):
            yield ("values", step)
        out = graph_app.invoke(inputs)
        yield ("final", out)
        return
    except Exception:
        pass
    out = graph_app.invoke(inputs)
    yield ("final", out)


def extract_latest_state(current_state: Dict[str, Any], step_payload: Any) -> Dict[str, Any]:
    if isinstance(step_payload, dict):
        if len(step_payload) == 1 and isinstance(next(iter(step_payload.values())), dict):
            inner = next(iter(step_payload.values()))
            current_state.update(inner)
        else:
            current_state.update(step_payload)
    return current_state


_MD_IMG_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)")
_CAPTION_LINE_RE = re.compile(r"^\*(?P<cap>.+)\*$")


def _resolve_image_path(src: str) -> Path:
    return Path(src.strip().lstrip("./")).resolve()


def render_markdown_with_local_images(md: str):
    matches = list(_MD_IMG_RE.finditer(md))
    if not matches:
        st.markdown(md, unsafe_allow_html=False)
        return
    parts: List[Tuple[str, str]] = []
    last = 0
    for m in matches:
        before = md[last: m.start()]
        if before:
            parts.append(("md", before))
        alt = (m.group("alt") or "").strip()
        src = (m.group("src") or "").strip()
        parts.append(("img", f"{alt}|||{src}"))
        last = m.end()
    tail = md[last:]
    if tail:
        parts.append(("md", tail))
    i = 0
    while i < len(parts):
        kind, payload = parts[i]
        if kind == "md":
            st.markdown(payload, unsafe_allow_html=False)
            i += 1
            continue
        alt, src = payload.split("|||", 1)
        caption = None
        if i + 1 < len(parts) and parts[i + 1][0] == "md":
            nxt = parts[i + 1][1].lstrip()
            if nxt.strip():
                first_line = nxt.splitlines()[0].strip()
                mcap = _CAPTION_LINE_RE.match(first_line)
                if mcap:
                    caption = mcap.group("cap").strip()
                    rest = "\n".join(nxt.splitlines()[1:])
                    parts[i + 1] = ("md", rest)
        if src.startswith("http://") or src.startswith("https://"):
            st.image(src, caption=caption or (alt or None), use_container_width=True)
        else:
            img_path = _resolve_image_path(src)
            if img_path.exists():
                st.image(str(img_path), caption=caption or (alt or None), use_container_width=True)
            else:
                st.warning(f"Image not found: `{src}`")
        i += 1


def list_past_blogs() -> List[Path]:
    files = [p for p in Path(".").glob("*.md") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def read_md_file(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def extract_title_from_md(md: str, fallback: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            t = line[2:].strip()
            return t or fallback
    return fallback


def count_words(md: str) -> int:
    return len(re.sub(r"[#*`>\[\]()!_~\-]", " ", md).split())


# ─────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────
if "last_out" not in st.session_state:
    st.session_state["last_out"] = None
if "logs" not in st.session_state:
    st.session_state["logs"] = []
if "gen_stats" not in st.session_state:
    st.session_state["gen_stats"] = {}

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: .8rem 0 1.2rem 0;">
        <div style="font-family:'DM Serif Display',serif; font-size:1.25rem; color:#eef0f6;">
            BlogForge <span style="color:#f5a623;">AI</span>
        </div>
        <div style="color:#555a72; font-size:11px; font-family:'DM Mono',monospace;
                    letter-spacing:.4px; margin-top:.2rem;">
            AGENTIC BLOG WRITER
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="color:#8a90a8;font-size:11.5px;letter-spacing:.5px;text-transform:uppercase;font-family:\'DM Mono\',monospace;margin-bottom:.5rem;">New Blog</div>', unsafe_allow_html=True)

    topic = st.text_area(
        "Topic",
        placeholder="e.g. How Mixture-of-Experts works in modern LLMs",
        height=110,
        label_visibility="collapsed",
    )

    col_date, col_blank = st.columns([3, 1])
    with col_date:
        as_of = st.date_input("As-of date", value=date.today(), label_visibility="visible")

    st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
    run_btn = st.button("🚀  Generate Blog", type="primary", use_container_width=True)

    # ── Stats strip (shown after a run) ──
    stats = st.session_state.get("gen_stats", {})
    if stats:
        st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)
        s1, s2, s3 = st.columns(3)
        with s1:
            st.markdown(f"""
            <div style="background:#13161e;border:1px solid #252836;border-radius:8px;
                        padding:.5rem .6rem;text-align:center;">
                <div style="color:#f5a623;font-family:'DM Serif Display',serif;font-size:1.1rem;">
                    {stats.get('sections', '—')}
                </div>
                <div style="color:#555a72;font-size:10px;font-family:'DM Mono',monospace;">sections</div>
            </div>
            """, unsafe_allow_html=True)
        with s2:
            st.markdown(f"""
            <div style="background:#13161e;border:1px solid #252836;border-radius:8px;
                        padding:.5rem .6rem;text-align:center;">
                <div style="color:#2dd4c4;font-family:'DM Serif Display',serif;font-size:1.1rem;">
                    {stats.get('words', '—')}
                </div>
                <div style="color:#555a72;font-size:10px;font-family:'DM Mono',monospace;">words</div>
            </div>
            """, unsafe_allow_html=True)
        with s3:
            st.markdown(f"""
            <div style="background:#13161e;border:1px solid #252836;border-radius:8px;
                        padding:.5rem .6rem;text-align:center;">
                <div style="color:#ff9f6b;font-family:'DM Serif Display',serif;font-size:1.1rem;">
                    {stats.get('images', '—')}
                </div>
                <div style="color:#555a72;font-size:10px;font-family:'DM Mono',monospace;">images</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Past blogs ──
    st.markdown('<hr style="margin:1.2rem 0;border-color:#252836;">', unsafe_allow_html=True)
    st.markdown('<div style="color:#8a90a8;font-size:11.5px;letter-spacing:.5px;text-transform:uppercase;font-family:\'DM Mono\',monospace;margin-bottom:.7rem;">Past Blogs</div>', unsafe_allow_html=True)

    past_files = list_past_blogs()
    if not past_files:
        st.markdown('<div style="color:#555a72;font-size:12.5px;padding:.4rem 0;">No saved blogs yet.</div>', unsafe_allow_html=True)
        selected_md_file = None
    else:
        options: List[str] = []
        file_by_label: Dict[str, Path] = {}
        for p in past_files[:30]:
            try:
                md_text = read_md_file(p)
                title = extract_title_from_md(md_text, p.stem)
            except Exception:
                title = p.stem
            label = f"{title[:36]}…" if len(title) > 36 else title
            full_label = f"{title}|||{p.name}"
            options.append(full_label)
            file_by_label[full_label] = p

        display_options = [o.split("|||")[0] for o in options]
        selected_idx = st.radio(
            "blogs",
            range(len(options)),
            format_func=lambda i: display_options[i],
            label_visibility="collapsed",
        )
        selected_md_file = file_by_label[options[selected_idx]] if options else None

        if st.button("📂  Load Selected Blog", use_container_width=True):
            if selected_md_file:
                md_text = read_md_file(selected_md_file)
                wc = count_words(md_text)
                st.session_state["last_out"] = {
                    "plan": None,
                    "evidence": [],
                    "image_specs": [],
                    "final": md_text,
                }
                st.session_state["gen_stats"] = {
                    "sections": "—",
                    "words": f"{wc:,}",
                    "images": "—",
                }
                st.session_state["topic_prefill"] = extract_title_from_md(md_text, selected_md_file.stem)
                st.rerun()

# ─────────────────────────────────────────────
# Main content
# ─────────────────────────────────────────────
hero_header()

tab_plan, tab_evidence, tab_preview, tab_images, tab_logs = st.tabs(
    ["  🧩 Plan  ", "  🔎 Evidence  ", "  📝 Preview  ", "  🖼️ Images  ", "  🧾 Logs  "]
)

logs: List[str] = []


def log(msg: str):
    logs.append(msg)


# ─────────────────────────────────────────────
# Run graph
# ─────────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.warning("Please enter a topic before generating.")
        st.stop()

    st.session_state["logs"] = []

    inputs: Dict[str, Any] = {
        "topic": topic.strip(),
        "mode": "",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "plan": None,
        "as_of": as_of.isoformat(),
        "recency_days": 7,
        "sections": [],
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],
        "final": "",
    }

    # ── Live progress panel ──
    st.markdown("""
    <div style="background:#13161e;border:1px solid #353a50;border-radius:10px;
                padding:1.2rem 1.4rem;margin-bottom:1rem;">
        <div style="font-family:'DM Mono',monospace;font-size:11px;color:#f5a623;
                    letter-spacing:.5px;margin-bottom:.8rem;">▶ AGENT RUNNING</div>
    """, unsafe_allow_html=True)

    status = st.status("Initialising agent…", expanded=True)
    progress_area = st.empty()

    st.markdown("</div>", unsafe_allow_html=True)

    current_state: Dict[str, Any] = {}
    last_node = None

    for kind, payload in try_stream(app, inputs):
        if kind in ("updates", "values"):
            node_name = None
            if isinstance(payload, dict) and len(payload) == 1 and isinstance(next(iter(payload.values())), dict):
                node_name = next(iter(payload.keys()))
            if node_name and node_name != last_node:
                status.write(f"**Node:** `{node_name}`")
                last_node = node_name

            current_state = extract_latest_state(current_state, payload)

            # Live summary card
            ev_count = len(current_state.get("evidence", []) or [])
            sec_count = len(current_state.get("sections", []) or [])
            img_count = len(current_state.get("image_specs", []) or [])
            task_count = len((current_state.get("plan") or {}).get("tasks", [])) if isinstance(current_state.get("plan"), dict) else "—"
            mode_val = current_state.get("mode") or "—"

            progress_area.markdown(f"""
            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:.6rem;margin-top:.4rem;">
                {"".join([
                    f'<div style="background:#0d0f14;border:1px solid #252836;border-radius:8px;padding:.5rem .7rem;text-align:center;">'
                    f'<div style="color:{c};font-family:\'DM Mono\',monospace;font-size:.95rem;font-weight:500;">{v}</div>'
                    f'<div style="color:#555a72;font-size:10px;margin-top:.2rem;">{l}</div>'
                    f'</div>'
                    for l, v, c in [
                        ("mode", mode_val, "#f5a623"),
                        ("tasks", str(task_count), "#eef0f6"),
                        ("evidence", str(ev_count), "#2dd4c4"),
                        ("sections", str(sec_count), "#eef0f6"),
                        ("images", str(img_count), "#ff9f6b"),
                    ]
                ])}
            </div>
            """, unsafe_allow_html=True)

            log(f"[{kind}] {json.dumps(payload, default=str)[:1200]}")

        elif kind == "final":
            out = payload
            final_md = out.get("final", "")
            wc = count_words(final_md)
            sec_n = len(out.get("sections", []) or [])
            img_n = len(out.get("image_specs", []) or [])

            st.session_state["last_out"] = out
            st.session_state["gen_stats"] = {
                "sections": sec_n or len((out.get("plan") or {}).get("tasks", [])) if isinstance(out.get("plan"), dict) else "—",
                "words": f"{wc:,}",
                "images": img_n,
            }
            status.update(label="✅ Blog generated successfully", state="complete", expanded=False)
            log("[final] received final state")
            st.rerun()

# ─────────────────────────────────────────────
# Render result
# ─────────────────────────────────────────────
out = st.session_state.get("last_out")

if out:
    # ── Plan tab ──
    with tab_plan:
        section_heading("Blog Plan", "Structured outline generated by the orchestrator agent")
        plan_obj = out.get("plan")
        if not plan_obj:
            st.info("No plan data available (blog may have been loaded from file).")
        else:
            if hasattr(plan_obj, "model_dump"):
                plan_dict = plan_obj.model_dump()
            elif isinstance(plan_obj, dict):
                plan_dict = plan_obj
            else:
                plan_dict = json.loads(json.dumps(plan_obj, default=str))

            # Meta row
            st.markdown(f"""
            <div style="background:#13161e;border:1px solid #252836;border-radius:10px;
                        padding:1.1rem 1.4rem;margin-bottom:1.2rem;">
                <div style="font-family:'DM Serif Display',serif;font-size:1.35rem;
                            color:#eef0f6;margin-bottom:.8rem;">
                    {plan_dict.get('blog_title','—')}
                </div>
                <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">
                    <div>
                        <span style="color:#555a72;font-size:11px;font-family:'DM Mono',monospace;
                                     letter-spacing:.4px;text-transform:uppercase;">Audience</span>
                        <div style="color:#eef0f6;font-size:13.5px;margin-top:.2rem;">{plan_dict.get('audience','—')}</div>
                    </div>
                    <div>
                        <span style="color:#555a72;font-size:11px;font-family:'DM Mono',monospace;
                                     letter-spacing:.4px;text-transform:uppercase;">Tone</span>
                        <div style="color:#eef0f6;font-size:13.5px;margin-top:.2rem;">{plan_dict.get('tone','—')}</div>
                    </div>
                    <div>
                        <span style="color:#555a72;font-size:11px;font-family:'DM Mono',monospace;
                                     letter-spacing:.4px;text-transform:uppercase;">Kind</span>
                        <div style="color:#f5a623;font-size:13.5px;font-family:'DM Mono',monospace;
                                    margin-top:.2rem;">{plan_dict.get('blog_kind','—')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            tasks = plan_dict.get("tasks", [])
            if tasks:
                df = pd.DataFrame([
                    {
                        "ID": t.get("id"),
                        "Section Title": t.get("title"),
                        "Target Words": t.get("target_words"),
                        "Research": "✓" if t.get("requires_research") else "—",
                        "Citations": "✓" if t.get("requires_citations") else "—",
                        "Code": "✓" if t.get("requires_code") else "—",
                        "Tags": ", ".join(t.get("tags") or []),
                    }
                    for t in tasks
                ]).sort_values("ID")
                st.dataframe(df, use_container_width=True, hide_index=True)

                with st.expander("📋 Full task details (JSON)"):
                    st.json(tasks)

    # ── Evidence tab ──
    with tab_evidence:
        section_heading("Research Evidence", "Web sources gathered by the Tavily research agent")
        evidence = out.get("evidence") or []
        if not evidence:
            st.markdown("""
            <div style="background:#13161e;border:1px solid #252836;border-radius:10px;
                        padding:1.5rem;color:#8a90a8;font-size:13.5px;">
                No evidence collected — either <code style="color:#f5a623;">closed_book</code> mode was
                selected, or no Tavily API key is configured.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:#2dd4c4;font-family:\'DM Mono\',monospace;font-size:12px;margin-bottom:.8rem;">{len(evidence)} sources retrieved</div>', unsafe_allow_html=True)
            rows = []
            for e in evidence:
                if hasattr(e, "model_dump"):
                    e = e.model_dump()
                rows.append({
                    "Title": e.get("title"),
                    "Published": e.get("published_at", "—"),
                    "Source": e.get("source", "—"),
                    "URL": e.get("url"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Preview tab ──
    with tab_preview:
        final_md = out.get("final") or ""
        if not final_md:
            st.warning("No blog content available.")
        else:
            # Word count bar
            wc = count_words(final_md)
            read_min = max(1, wc // 200)
            st.markdown(f"""
            <div style="display:flex;gap:1.2rem;align-items:center;
                        margin-bottom:1.2rem;flex-wrap:wrap;">
                <div style="background:#13161e;border:1px solid #252836;border-radius:8px;
                            padding:.45rem .9rem;display:flex;align-items:center;gap:.5rem;">
                    <span style="color:#f5a623;font-size:13px;">📝</span>
                    <span style="color:#eef0f6;font-family:'DM Mono',monospace;font-size:12.5px;">
                        {wc:,} words
                    </span>
                </div>
                <div style="background:#13161e;border:1px solid #252836;border-radius:8px;
                            padding:.45rem .9rem;display:flex;align-items:center;gap:.5rem;">
                    <span style="color:#2dd4c4;font-size:13px;">⏱</span>
                    <span style="color:#eef0f6;font-family:'DM Mono',monospace;font-size:12.5px;">
                        ~{read_min} min read
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Content
            st.markdown('<div style="background:#13161e;border:1px solid #252836;border-radius:12px;padding:2rem 2.2rem;">', unsafe_allow_html=True)
            render_markdown_with_local_images(final_md)
            st.markdown('</div>', unsafe_allow_html=True)

            # Downloads
            st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
            plan_obj = out.get("plan")
            if hasattr(plan_obj, "blog_title"):
                blog_title = plan_obj.blog_title
            elif isinstance(plan_obj, dict):
                blog_title = plan_obj.get("blog_title", "blog")
            else:
                blog_title = extract_title_from_md(final_md, "blog")

            md_filename = f"{safe_slug(blog_title)}.md"
            c1, c2, c3 = st.columns(3)
            with c1:
                st.download_button("⬇️  Download Markdown", data=final_md.encode("utf-8"),
                                   file_name=md_filename, mime="text/markdown", use_container_width=True)
            with c2:
                bundle = bundle_zip(final_md, md_filename, Path("images"))
                st.download_button("📦  Download Bundle (MD + images)", data=bundle,
                                   file_name=f"{safe_slug(blog_title)}_bundle.zip",
                                   mime="application/zip", use_container_width=True)
            with c3:
                st.download_button("📋  Copy as Text", data=final_md.encode("utf-8"),
                                   file_name=md_filename, mime="text/plain", use_container_width=True)

    # ── Images tab ──
    with tab_images:
        section_heading("Generated Images", "AI-created visuals embedded in the blog")
        specs = out.get("image_specs") or []
        images_dir = Path("images")

        if not specs and not images_dir.exists():
            st.markdown("""
            <div style="background:#13161e;border:1px solid #252836;border-radius:10px;
                        padding:1.5rem;color:#8a90a8;font-size:13.5px;">
                No images were generated for this blog post.
            </div>
            """, unsafe_allow_html=True)
        else:
            if specs:
                section_heading("Image Plan")
                st.json(specs)

            if images_dir.exists():
                files = [p for p in images_dir.iterdir() if p.is_file()]
                if files:
                    cols = st.columns(min(len(files), 2))
                    for idx, p in enumerate(sorted(files)):
                        with cols[idx % 2]:
                            st.image(str(p), caption=p.name, use_container_width=True)

                    z = images_zip(images_dir)
                    if z:
                        st.download_button("⬇️  Download All Images (.zip)", data=z,
                                           file_name="images.zip", mime="application/zip")

    # ── Logs tab ──
    with tab_logs:
        section_heading("Agent Logs", "Raw event stream from the LangGraph execution")
        if logs:
            st.session_state["logs"].extend(logs)

        col_log, col_ctrl = st.columns([5, 1])
        with col_ctrl:
            if st.button("🗑  Clear", use_container_width=True):
                st.session_state["logs"] = []
                st.rerun()
        with col_log:
            st.text_area(
                "event_log",
                value="\n\n".join(st.session_state["logs"][-80:]),
                height=520,
                label_visibility="collapsed",
            )

else:
    # ── Empty state ──
    with tab_preview:
        st.markdown("""
        <div style="
            display:flex; flex-direction:column; align-items:center;
            justify-content:center; padding:5rem 2rem; text-align:center;
        ">
            <div style="font-size:3rem;margin-bottom:1rem;">✍️</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.6rem;
                        color:#eef0f6;margin-bottom:.6rem;">
                Ready to write something great?
            </div>
            <div style="color:#8a90a8;font-size:14px;max-width:420px;line-height:1.7;">
                Enter a topic in the sidebar and click
                <span style="color:#f5a623;font-weight:600;">Generate Blog</span>
                to kick off the AI agent pipeline.
            </div>
        </div>
        """, unsafe_allow_html=True)