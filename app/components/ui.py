# app/components/ui.py
"""
Reusable HTML component functions for the PDF Compliance Scanner.
Each function returns an HTML string for st.markdown(html, unsafe_allow_html=True).
"""

def risk_badge(risk_level: str) -> str:
    """Returns a styled badge span for critical/high/medium/low."""
    level = risk_level.lower()
    colors = {
        "critical": ("var(--red)", "badge-critical"),
        "high": ("var(--high)", "badge-high"),
        "medium": ("var(--medium)", "badge-medium"),
        "low": ("var(--low)", "badge-low"),
        "info": ("var(--ice)", "badge-info"),
    }
    color, cls = colors.get(level, ("var(--text-muted)", "badge-info"))
    return f'<span class="badge {cls}">● {level.upper()}</span>'


def section_header(module_num: str, title: str, subtitle: str, accent_color: str = "var(--amber)") -> str:
    """Returns the standard page header HTML with MODULE label, title, subtitle."""
    parts = title.split(" ", 1)
    title_html = f'{parts[0]} <span style="color:{accent_color}">{parts[1]}</span>' if len(parts) == 2 else title
    return (
        f'<div class="animate-fadein" style="padding:0 0 24px">'
        f'<div class="caption-label">MODULE {module_num}</div>'
        f'<h1 style="font-family:\'Space Mono\',monospace;font-size:33px;font-weight:700;color:var(--text);margin:6px 0 4px;letter-spacing:-0.01em">{title_html}</h1>'
        f'<p style="color:var(--text-muted);font-size:17px;margin:0">{subtitle}</p>'
        f'</div>'
    )


def metric_grid(metrics: list) -> str:
    """
    Renders a CSS grid of metric cells.
    metrics: list of {"label": str, "value": str/int, "color": str}
    """
    n = len(metrics)
    cells = ""
    for m in metrics:
        cells += (
            f'<div style="background:var(--surface);padding:16px 12px;text-align:center">'
            f'<div class="caption-label" style="margin-bottom:6px">{m["label"]}</div>'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:29px;font-weight:700;color:{m["color"]}">{m["value"]}</div>'
            f'</div>'
        )
    return (
        f'<div style="display:grid;grid-template-columns:repeat({n},1fr);gap:1px;background:var(--border);border:1px solid var(--border);margin-bottom:24px">'
        f'{cells}'
        f'</div>'
    )


def alert_banner(message: str, alert_type: str = "info") -> str:
    """Returns a styled banner with left border and icon."""
    config = {
        "info": ("var(--ice)", "rgba(56,200,232,0.08)", "ℹ"),
        "warning": ("var(--medium)", "rgba(232,200,56,0.08)", "⚠"),
        "error": ("var(--red)", "rgba(255,69,69,0.08)", "✕"),
        "success": ("var(--low)", "rgba(79,209,128,0.08)", "✓"),
    }
    color, bg, icon = config.get(alert_type, config["info"])
    return (
        f'<div style="background:{bg};border-left:3px solid {color};border-radius:0 3px 3px 0;padding:12px 16px;display:flex;align-items:center;gap:10px;margin:8px 0">'
        f'<span style="font-family:\'Space Mono\',monospace;font-size:19px;color:{color}">{icon}</span>'
        f'<span style="font-family:\'Space Mono\',monospace;font-size:14px;color:var(--text);letter-spacing:0.04em">{message}</span>'
        f'</div>'
    )


def loading_message(message: str) -> str:
    """Returns an animated blinking cursor message."""
    return (
        f'<div style="font-family:\'Space Mono\',monospace;font-size:14px;color:var(--amber);letter-spacing:0.1em;animation:blink 1s step-end infinite">'
        f'■ {message}<span>_</span>'
        f'</div>'
    )


def section_divider(label: str = "") -> str:
    """Returns a full-width divider, optionally with a centered label."""
    if label:
        return (
            f'<div style="display:flex;align-items:center;gap:12px;margin:20px 0">'
            f'<div style="flex:1;height:1px;background:var(--border)"></div>'
            f'<div class="caption-label">{label}</div>'
            f'<div style="flex:1;height:1px;background:var(--border)"></div>'
            f'</div>'
        )
    return '<div style="height:1px;background:var(--border);margin:24px 0"></div>'


def flag_count_row(pii: int, confidential: int, encoding: int, abuse: int) -> str:
    """Returns a 4-cell horizontal strip with colored top accent bars."""
    return (
        f'<div class="caption-label" style="margin-bottom:10px">ISSUE BREAKDOWN BY TYPE</div>'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border:1px solid var(--border);margin-bottom:24px">'
        f'<div style="background:var(--surface);padding:14px;border-left:3px solid var(--red)"><div class="caption-label" style="color:var(--red);margin-bottom:4px">PII FLAGS</div><div style="font-family:\'JetBrains Mono\',monospace;font-size:33px;font-weight:700;color:var(--red)">{pii}</div></div>'
        f'<div style="background:var(--surface);padding:14px;border-left:3px solid var(--high)"><div class="caption-label" style="color:var(--high);margin-bottom:4px">CONFIDENTIAL</div><div style="font-family:\'JetBrains Mono\',monospace;font-size:33px;font-weight:700;color:var(--high)">{confidential}</div></div>'
        f'<div style="background:var(--surface);padding:14px;border-left:3px solid var(--ice)"><div class="caption-label" style="color:var(--ice);margin-bottom:4px">ENCODING</div><div style="font-family:\'JetBrains Mono\',monospace;font-size:33px;font-weight:700;color:var(--ice)">{encoding}</div></div>'
        f'<div style="background:var(--surface);padding:14px;border-left:3px solid var(--medium)"><div class="caption-label" style="color:var(--medium);margin-bottom:4px">ABUSE</div><div style="font-family:\'JetBrains Mono\',monospace;font-size:33px;font-weight:700;color:var(--medium)">{abuse}</div></div>'
        f'</div>'
    )


def empty_state(title: str, subtitle: str, icon: str = "□") -> str:
    """Returns a centered empty state with icon and sarcastic note."""
    return (
        f'<div style="text-align:center;padding:64px 24px;border:1px dashed var(--border);border-radius:4px;margin-top:24px">'
        f'<div style="font-family:\'Space Mono\',monospace;font-size:53px;color:var(--border-bright);margin-bottom:16px">{icon}</div>'
        f'<div style="font-family:\'Space Mono\',monospace;font-size:16px;color:var(--text-muted);letter-spacing:0.1em;margin-bottom:8px">{title}</div>'
        f'<div style="font-family:\'DM Sans\',sans-serif;font-size:16px;color:var(--text-muted)">{subtitle}<br><span style="font-style:italic;opacity:0.7">The system doesn\'t judge. Neither do we. Much.</span></div>'
        f'</div>'
    )


def terminal_block(lines: list, title: str = "OUTPUT") -> str:
    """Returns an HTML terminal window with colored dots and formatted lines."""
    line_divs = ""
    for line in lines:
        color = "var(--red)" if line.strip().startswith("ERROR") else "var(--medium)" if line.strip().startswith("WARNING") else "var(--low)" if line.strip().startswith("OK") else "var(--text-muted)"
        line_divs += f'<div style="color:{color}">{line}</div>'

    return (
        f'<div style="border:1px solid var(--border);border-radius:4px;overflow:hidden;margin:12px 0">'
        f'<div style="background:var(--surface);padding:8px 14px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border)">'
        f'<div style="width:10px;height:10px;border-radius:50%;background:#FF5F57"></div>'
        f'<div style="width:10px;height:10px;border-radius:50%;background:#FFBD2E"></div>'
        f'<div style="width:10px;height:10px;border-radius:50%;background:#28C840"></div>'
        f'<div style="font-family:\'Space Mono\',monospace;font-size:13px;color:var(--text-muted);margin-left:8px;letter-spacing:0.1em">{title}</div>'
        f'</div>'
        f'<div style="background:#0A0A0A;padding:16px;font-family:\'JetBrains Mono\',monospace;font-size:14px;line-height:1.8">{line_divs}</div>'
        f'</div>'
    )


def scan_result_header(
    pdf_name: str, upload_id: str, elapsed: float, highest_risk: str
) -> str:
    """Returns a styled scan completion header with filename, ID, timing, and risk badge."""
    badge_html = risk_badge(highest_risk)
    return (
        f'<div style="background:var(--surface);border:1px solid var(--border);border-radius:3px;padding:20px 24px;display:flex;justify-content:space-between;align-items:center;margin:16px 0">'
        f'<div><div class="caption-label">SCAN COMPLETE</div><div style="font-family:\'JetBrains Mono\',monospace;font-size:18px;color:var(--text);margin:6px 0 4px">{pdf_name}</div><div style="font-family:\'JetBrains Mono\',monospace;font-size:14px;color:var(--text-muted)">ID: {upload_id} · elapsed: {elapsed:.1f}s</div></div>'
        f'<div style="text-align:right">{badge_html}<div style="font-family:\'Space Mono\',monospace;font-size:12px;color:var(--text-muted);margin-top:6px;letter-spacing:0.1em">HIGHEST RISK LEVEL</div></div>'
        f'</div>'
    )


def render_sidebar_opener():
    """
    Renders a ☰ MENU button that reopens the sidebar.
    On click, injects JS (via same-origin iframe) that clicks the native
    Streamlit sidebar toggle — the most reliable workaround since
    st.switch_page() path resolution and st.rerun() both fail for this.
    """
    import streamlit as st
    import streamlit.components.v1 as components

    if st.button("☰  MENU", key="_sb_open_btn"):
        st.session_state["_open_sidebar_js"] = True
        st.rerun()

    if st.session_state.pop("_open_sidebar_js", False):
        # Inject JS into parent frame (same-origin) to click the sidebar toggle
        components.html("""
        <script>
        (function() {
            var doc = window.parent.document;
            // Try the collapsedControl reopen button first
            var btn = doc.querySelector('[data-testid="collapsedControl"] button');
            // Fallback: sidebar header collapse/expand button
            if (!btn) btn = doc.querySelector('[data-testid="stSidebarHeader"] button');
            if (btn) {
                btn.click();
            } else {
                // Retry after Streamlit has finished rendering
                setTimeout(function() {
                    var b = doc.querySelector('[data-testid="collapsedControl"] button')
                           || doc.querySelector('[data-testid="stSidebarHeader"] button');
                    if (b) b.click();
                }, 300);
            }
        })();
        </script>
        """, height=0, scrolling=False)


def render_common_sidebar():
    """Renders the standard Noir Amber sidebar branding and API settings expander."""
    import streamlit as st
    import textwrap
    import os
    
    with st.sidebar:
        st.markdown(textwrap.dedent("""
        <div style="margin-top: 40px; padding: 4px 0 20px">
          <div style="font-family:'Space Mono',monospace; font-size:21px; font-weight:700; color:var(--amber); letter-spacing:0.05em; margin-bottom:4px">
            COMPLIANCE<br>SCANNER
          </div>
          <div style="font-family:'Space Mono',monospace; font-size:10px; color:var(--text-muted); letter-spacing:0.05em; text-transform:uppercase">
            AI-Powered Document Compliance Guard
          </div>
        </div>
        """), unsafe_allow_html=True)


        with st.expander("⚙️  API CONFIGURATION", expanded=False):
            st.markdown("<div style='font-size:13px; color:var(--text-muted); margin-bottom:8px'>Override .env keys dynamically</div>", unsafe_allow_html=True)
            
            # Groq
            groq_key = st.text_input("Groq API Key", value=os.environ.get("GROQ_API_KEY", ""), type="password", help="Required for Llama3 models")
            if groq_key:
                os.environ["GROQ_API_KEY"] = groq_key
                
            # Gemini
            gemini_key = st.text_input("Gemini API Key", value=os.environ.get("GOOGLE_API_KEY", ""), type="password", help="Required if AI_PROVIDER=gemini")
            if gemini_key:
                os.environ["GOOGLE_API_KEY"] = gemini_key
                
            # Anthropic
            anthropic_key = st.text_input("Anthropic API Key", value=os.environ.get("ANTHROPIC_API_KEY", ""), type="password", help="Required if AI_PROVIDER=anthropic")
            if anthropic_key:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key

        st.markdown(textwrap.dedent("""
        <hr style="border:none;border-top:1px solid var(--border);margin:20px 0">
        <div class="caption-label" style="margin-bottom:10px">PIPELINE STACK</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:13px; color:var(--text-muted); line-height:1.9">
          Groq Llama 3<br>
          LangGraph DAG<br>
          PyMuPDF · ReportLab<br>
          ChromaDB RAG<br>
          SQLite Storage
        </div>
        <hr style="border:none;border-top:1px solid var(--border);margin:20px 0">
        <div style="font-family:'Space Mono',monospace; font-size:11px; color:#3A3A3A; letter-spacing:0.1em">
          PDF · DB · S3 · WAREHOUSE<br>
          ALL SYSTEMS OPERATIONAL
        </div>
        """), unsafe_allow_html=True)

