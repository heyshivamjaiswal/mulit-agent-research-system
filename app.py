import markdown as md_lib
import streamlit as st

from src.pipelines.pipeline import research_pipeline

st.set_page_config(page_title="Research Desk", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
# ink       - background, near-black warm graphite (not pure #000, keeps it soft)
# ink-2     - panel background, one step up from ink
# paper     - the report surface, a true off-white (this is where the serif lives)
# line      - hairline borders / dividers on ink
# teal      - "verified / complete" accent, used for finished stages and links
# brass     - "in progress" accent, used only for the active stage
# rust      - error state only, never decorative
# ink-soft  - secondary text on ink
STAGES = [
    ("search", "01", "Search", "Finding sources"),
    ("read", "02", "Read", "Extracting the page"),
    ("write", "03", "Write", "Drafting the report"),
    ("critique", "04", "Critique", "Scoring the draft"),
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --ink: #15171c;
    --ink-2: #1c1f26;
    --paper: #f7f4ec;
    --line: #2c303a;
    --teal: #4f9384;
    --brass: #c99a52;
    --rust: #b5654f;
    --ink-soft: #8a8f9c;
}

#MainMenu, header, footer {visibility: hidden;}
.stDeployButton {display: none;}

html, body, [class*="css"] {
    background-color: var(--ink) !important;
    color: #e8e6df;
    font-family: 'IBM Plex Mono', monospace;
}

.block-container {
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    max-width: 1180px;
}

/* -------- Masthead -------- */
.masthead {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    border-bottom: 1px solid var(--line);
    padding-bottom: 1.1rem;
    margin-bottom: 2.2rem;
}
.masthead-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #e8e6df;
    font-weight: 600;
}
.masthead-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--ink-soft);
    letter-spacing: 0.05em;
}

/* -------- Inputs -------- */
.stTextInput input {
    background-color: var(--ink-2) !important;
    border: 1px solid var(--line) !important;
    border-radius: 2px !important;
    color: #e8e6df !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.92rem !important;
    padding: 0.7rem 0.85rem !important;
}
.stTextInput input:focus {
    border-color: var(--teal) !important;
    box-shadow: none !important;
}
.stTextInput label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ink-soft) !important;
}

div.stButton > button {
    background-color: transparent;
    border: 1px solid #e8e6df;
    border-radius: 2px;
    color: #e8e6df;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.55rem 1.4rem;
    transition: all 0.15s ease;
}
div.stButton > button:hover {
    background-color: #e8e6df;
    color: var(--ink);
    border-color: #e8e6df;
}
div.stButton > button:active {
    transform: scale(0.98);
}
div.stButton > button:disabled {
    opacity: 0.35;
    border-color: var(--ink-soft);
    color: var(--ink-soft);
}

/* -------- Stage rail (the signature element) -------- */
.rail { padding-top: 0.4rem; }
.rail-item { display: flex; gap: 0.85rem; position: relative; padding-bottom: 1.9rem; }
.rail-item:last-child { padding-bottom: 0; }
.rail-connector {
    position: absolute;
    left: 10px;
    top: 24px;
    width: 1px;
    height: calc(100% - 10px);
    background: var(--line);
    overflow: hidden;
}
.rail-connector.filled { background: var(--teal); }
.rail-connector.running::after {
    content: "";
    position: absolute;
    top: 0; left: -6px;
    width: 13px; height: 40%;
    background: var(--brass);
    animation: scan 1.1s linear infinite;
}
@keyframes scan {
    0% { top: -40%; }
    100% { top: 100%; }
}
.rail-dot {
    width: 21px; height: 21px;
    border-radius: 50%;
    border: 1px solid var(--line);
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.62rem;
    color: var(--ink-soft);
    background: var(--ink);
    z-index: 1;
}
.rail-dot.done { border-color: var(--teal); color: var(--teal); background: rgba(79,147,132,0.1); }
.rail-dot.running { border-color: var(--brass); color: var(--brass); }
.rail-dot.error { border-color: var(--rust); color: var(--rust); }
.rail-label {
    font-size: 0.86rem; font-weight: 500; color: #e8e6df;
}
.rail-label.pending { color: var(--ink-soft); }
.rail-detail {
    font-size: 0.72rem; color: var(--ink-soft); margin-top: 0.15rem;
}
.rail-detail.running { color: #e8e6df; }
.rail-cursor {
    display: inline-block;
    width: 6px; height: 11px;
    background: var(--brass);
    margin-left: 3px;
    vertical-align: -1px;
    animation: blink 1s step-end infinite;
}
@keyframes blink {
    0%, 49% { opacity: 1; }
    50%, 100% { opacity: 0; }
}

/* -------- Paper panel (report surface) -------- */
.paper {
    background: var(--paper);
    color: #1c1a15;
    border-radius: 2px;
    padding: 2.6rem 3rem;
    font-family: 'Newsreader', serif;
    font-size: 1.05rem;
    line-height: 1.68;
}
.paper h1, .paper h2, .paper h3 {
    font-family: 'Newsreader', serif;
    font-weight: 600;
    color: #1c1a15;
}
.paper a { color: #2f6c5e; }
.paper ul, .paper ol { padding-left: 1.4rem; }
.paper li { margin-bottom: 0.3rem; }
.paper strong { font-weight: 600; }
.paper hr { border: none; border-top: 1px solid #d8d2c2; margin: 1.6rem 0; }
.paper p { margin: 0 0 1rem; }

/* -------- Critique card -------- */
.critique {
    background: var(--ink-2);
    border: 1px solid var(--line);
    border-radius: 2px;
    padding: 1.8rem 2rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.88rem;
    line-height: 1.7;
    color: #e8e6df;
}
.critique ul, .critique ol { padding-left: 1.3rem; }
.critique li { margin-bottom: 0.35rem; }
.critique strong { color: #f0eee8; }
.critique p { margin: 0 0 0.9rem; }

.section-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--ink-soft);
    margin-bottom: 0.6rem;
}

.source-row {
    display: flex; align-items: baseline; gap: 0.7rem;
    padding: 0.85rem 0;
    border-bottom: 1px solid var(--line);
    font-family: 'IBM Plex Mono', monospace;
}
.source-row:last-child { border-bottom: none; }
.source-num { color: var(--ink-soft); font-size: 0.78rem; flex-shrink: 0; }
.source-title { color: #e8e6df; font-size: 0.88rem; }
.source-link { color: var(--teal); font-size: 0.76rem; word-break: break-all; }
.source-link a { color: var(--teal); text-decoration: none; }
.source-link a:hover { text-decoration: underline; }

.stTabs [data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.76rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ink-soft);
    padding-bottom: 0.7rem;
}
.stTabs [aria-selected="true"] { color: #e8e6df !important; border-bottom: 2px solid var(--teal) !important; }

.stExpander {
    border: 1px solid var(--line) !important;
    border-radius: 2px !important;
    background: var(--ink-2) !important;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

if "status" not in st.session_state:
    st.session_state.status = {key: "idle" for key, *_ in STAGES}
if "detail" not in st.session_state:
    st.session_state.detail = {key: "" for key, *_ in STAGES}
if "result" not in st.session_state:
    st.session_state.result = None


def render_rail():
    rows = []
    for i, (key, num, label, desc) in enumerate(STAGES):
        status = st.session_state.status[key]
        is_running = status == "running"
        connector_cls = "filled" if status == "done" else ("running" if is_running else "")
        dot_content = "\u2713" if status == "done" else ("\u00d7" if status == "error" else num)
        label_cls = "pending" if status == "idle" else ""
        detail_cls = "running" if is_running else ""
        cursor = '<span class="rail-cursor"></span>' if is_running else ""
        connector_html = "" if i == len(STAGES) - 1 else f'<div class="rail-connector {connector_cls}"></div>'
        # NOTE: this must stay a single line with no leading whitespace.
        # Markdown treats 4+ leading spaces as a code block, which was
        # escaping the HTML into literal text instead of rendering it.
        rows.append(
            f'<div class="rail-item">{connector_html}'
            f'<div class="rail-dot {status}">{dot_content}</div>'
            f'<div><div class="rail-label {label_cls}">{label}</div>'
            f'<div class="rail-detail {detail_cls}">{desc}{cursor}</div></div></div>'
        )
    return f'<div class="rail">{"".join(rows)}</div>'


st.markdown(
    '<div class="masthead">'
    '<div class="masthead-title">Research Desk</div>'
    '<div class="masthead-sub">search &nbsp;/&nbsp; read &nbsp;/&nbsp; write &nbsp;/&nbsp; critique</div>'
    '</div>',
    unsafe_allow_html=True,
)

input_col, button_col = st.columns([5, 1])
with input_col:
    topic = st.text_input("Topic", placeholder="e.g. the state of solid-state batteries in 2026", label_visibility="visible")
with button_col:
    st.markdown("<div style='height: 1.85rem'></div>", unsafe_allow_html=True)
    run_clicked = st.button("Run research", use_container_width=True)

rail_col, content_col = st.columns([1, 3], gap="large")

with rail_col:
    rail_placeholder = st.empty()
    rail_placeholder.markdown(render_rail(), unsafe_allow_html=True)

with content_col:
    content_placeholder = st.empty()
    if not st.session_state.result and not run_clicked:
        content_placeholder.markdown(
            '<div class="section-eyebrow">Awaiting a topic</div>'
            '<div style="color: var(--ink-soft); font-size: 0.88rem;">'
            "Enter a topic on the left and run the pipeline. Each stage reports in as it finishes."
            "</div>",
            unsafe_allow_html=True,
        )

if run_clicked:
    if not topic.strip():
        content_placeholder.markdown(
            '<div class="section-eyebrow" style="color: var(--rust);">No topic entered</div>'
            '<div style="color: var(--ink-soft); font-size: 0.88rem;">Type a topic before running the pipeline.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.session_state.status = {key: "idle" for key, *_ in STAGES}
        st.session_state.result = None

        def on_step(stage: str, status: str, detail: str = ""):
            st.session_state.status[stage] = status
            if detail:
                st.session_state.detail[stage] = detail[:140]
            rail_placeholder.markdown(render_rail(), unsafe_allow_html=True)

        try:
            result = research_pipeline(topic.strip(), on_step=on_step)
            st.session_state.result = result
        except Exception as e:
            # mark whichever stage was running as errored
            for key, status in st.session_state.status.items():
                if status == "running":
                    st.session_state.status[key] = "error"
            rail_placeholder.markdown(render_rail(), unsafe_allow_html=True)
            content_placeholder.markdown(
                f'<div class="section-eyebrow" style="color: var(--rust);">Pipeline stopped</div>'
                f'<div style="color: var(--ink-soft); font-size: 0.88rem;">{str(e)}</div>',
                unsafe_allow_html=True,
            )
            result = None

        if st.session_state.result:
            result = st.session_state.result
            with content_placeholder.container():
                tab_report, tab_sources, tab_critique, tab_raw = st.tabs(
                    ["Report", "Sources", "Critique", "Raw"]
                )

                with tab_report:
                    report_html = md_lib.markdown(result["report"], extensions=["extra", "sane_lists"])
                    st.markdown(f'<div class="paper">{report_html}</div>', unsafe_allow_html=True)
                    st.download_button(
                        "Download report (.md)",
                        data=result["report"],
                        file_name=f"{topic.strip().replace(' ', '_')[:40]}_report.md",
                        mime="text/markdown",
                    )

                with tab_sources:
                    if result["sources"]:
                        rows = "".join(
                            f'<div class="source-row"><span class="source-num">{i+1:02d}</span>'
                            f'<div><div class="source-title">{s["title"]}</div>'
                            f'<div class="source-link"><a href="{s["url"]}" target="_blank">{s["url"]}</a></div>'
                            f'</div></div>'
                            for i, s in enumerate(result["sources"])
                        )
                        st.markdown(rows, unsafe_allow_html=True)
                    else:
                        st.markdown(
                            '<span style="color: var(--ink-soft); font-size: 0.85rem;">'
                            "No sources were parsed out of this run.</span>",
                            unsafe_allow_html=True,
                        )

                with tab_critique:
                    critique_html = md_lib.markdown(result["feedback"], extensions=["extra", "sane_lists"])
                    st.markdown(f'<div class="critique">{critique_html}</div>', unsafe_allow_html=True)

                with tab_raw:
                    with st.expander("Search agent — full output", expanded=False):
                        st.code(result["search_results"], language=None)
                    with st.expander("Reader agent — full output", expanded=False):
                        st.code(result["scraped_content"], language=None)