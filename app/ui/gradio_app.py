import json
import os
import tempfile

import gradio as gr

from app.ui.api_client import NexusCLMClient

CSS = """
:root {
  --bg-primary: #1a1b23;
  --bg-secondary: #22232e;
  --bg-card: #2a2b38;
  --text-primary: #e4e4e7;
  --text-secondary: #a1a1aa;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --border: #33344a;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
}
body { background: var(--bg-primary) !important; color: var(--text-primary) !important; }
.gr-box { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
.gr-form { background: var(--bg-secondary) !important; }
label { color: var(--text-primary) !important; }
input, textarea, select { background: var(--bg-primary) !important; color: var(--text-primary) !important; border-color: var(--border) !important; }
button.gr-button { border-radius: 6px !important; font-weight: 500 !important; }
button#login-btn { background: var(--accent) !important; color: white !important; }
button#login-btn:hover { background: var(--accent-hover) !important; }
button.sidebar-btn { background: transparent !important; color: var(--text-secondary) !important; border: none !important; text-align: left !important; padding: 10px 16px !important; font-size: 15px !important; width: 100% !important; }
button.sidebar-btn:hover { background: var(--bg-card) !important; color: var(--text-primary) !important; }
button.sidebar-btn.active { background: var(--bg-card) !important; color: var(--accent) !important; border-left: 3px solid var(--accent) !important; }
#sidebar { background: var(--bg-secondary) !important; border-right: 1px solid var(--border) !important; padding: 16px !important; min-height: 100vh !important; }
#content { padding: 24px !important; background: var(--bg-primary) !important; min-height: 100vh !important; }
h1, h2, h3 { color: var(--text-primary) !important; }
.card { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; padding: 16px !important; margin-bottom: 12px !important; }
.risk-high { color: var(--danger) !important; font-weight: bold !important; }
.risk-mid { color: var(--warning) !important; font-weight: bold !important; }
.risk-low { color: var(--success) !important; font-weight: bold !important; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
.badge-compliant { background: #166534; color: #86efac; }
.badge-noncompliant { background: #7f1d1d; color: #fca5a5; }
.badge-partial { background: #713f12; color: #fcd34d; }
.badge-na { background: #1e3a5f; color: #93c5fd; }
footer { display: none !important; }
"""

client = NexusCLMClient()


def _risk_class(score: float) -> str:
    if score >= 0.7:
        return "risk-high"
    if score >= 0.4:
        return "risk-mid"
    return "risk-low"


def _compliance_badge(status: str) -> str:
    m = {"compliant": "badge badge-compliant", "non_compliant": "badge badge-noncompliant", "partial": "badge badge-partial", "not_applicable": "badge badge-na"}
    cls = m.get(status, "badge badge-na")
    return f'<span class="{cls}">{status.replace("_", " ").title()}</span>'


async def _handle_login(email: str, password: str, login_btn: gr.EventData):
    result = await client.login(email, password)
    if result["success"]:
        return (
            result["data"]["name"],
            result["data"]["email"],
            result["data"]["access_token"],
            gr.update(visible=False),
            gr.update(visible=True),
        )
    return "", "", "", gr.update(visible=True), gr.update(visible=False)


async def _handle_register(email: str, password: str, name: str):
    if not name.strip():
        return "Name is required", "", "", "", gr.update(visible=True), gr.update(visible=False)
    if len(password) < 6:
        return "Password must be at least 6 characters", "", "", "", gr.update(visible=True), gr.update(visible=False)
    result = await client.register(email, password, name)
    if result["success"]:
        return (
            "",
            result["data"]["name"],
            result["data"]["email"],
            result["data"]["access_token"],
            gr.update(visible=False),
            gr.update(visible=True),
        )
    return result.get("error", "Registration failed"), "", "", "", gr.update(visible=True), gr.update(visible=False)


async def _load_dashboard():
    data = await client.get_dashboard()
    contracts = await client.list_contracts()
    guidelines = await client.list_guidelines()
    total_contracts = len(contracts)
    total_guidelines = len(guidelines)
    risk_overview = data.get("risk_overview", [])
    avg_risk = 0.0
    if risk_overview:
        avg_risk = sum(r["overall_risk_score"] for r in risk_overview) / len(risk_overview)
    risk_cls = _risk_class(avg_risk)

    html = f"""
    <div style="display:flex;gap:16px;margin-bottom:24px;">
      <div class="card" style="flex:1;text-align:center;"><h3>Contracts</h3><span style="font-size:32px;font-weight:bold;">{total_contracts}</span></div>
      <div class="card" style="flex:1;text-align:center;"><h3>Guidelines</h3><span style="font-size:32px;font-weight:bold;">{total_guidelines}</span></div>
      <div class="card" style="flex:1;text-align:center;"><h3>Avg Risk</h3><span style="font-size:32px;font-weight:bold;" class="{risk_cls}">{avg_risk:.0%}</span></div>
    </div>
    <h2>Recent Analyses</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px;">Contract</th><th style="text-align:left;padding:8px;">Risk</th><th style="text-align:left;padding:8px;">Date</th></tr>
    """
    for r in risk_overview[-10:]:
        rc = _risk_class(r["overall_risk_score"])
        html += f'<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">{r["file_name"]}</td><td style="padding:8px;" class="{rc}">{r["overall_risk_score"]:.0%}</td><td style="padding:8px;">{str(r["analysis_date"])[:19]}</td></tr>'
    html += "</table>"
    return html


async def _list_contracts_ui():
    contracts = await client.list_contracts()
    if not contracts:
        return "<p>No contracts uploaded yet.</p>", []
    html = '<table style="width:100%;border-collapse:collapse;"><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px;">File</th><th style="text-align:left;padding:8px;">Party</th><th style="text-align:left;padding:8px;">Status</th><th style="text-align:left;padding:8px;">Date</th></tr>'
    choices = []
    for c in contracts:
        choices.append((f"{c['file_name']} ({c['party']})", c["id"]))
        html += f'<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">{c["file_name"]}</td><td style="padding:8px;">{c["party"]}</td><td style="padding:8px;">{c["status"]}</td><td style="padding:8px;">{str(c["created_at"])[:19]}</td></tr>'
    html += "</table>"
    return html, choices


async def _list_guidelines_ui():
    guidelines = await client.list_guidelines()
    if not guidelines:
        return "<p>No guidelines uploaded yet.</p>"
    html = '<table style="width:100%;border-collapse:collapse;"><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px;">Type</th><th style="text-align:left;padding:8px;">Scope</th><th style="text-align:left;padding:8px;">Risk</th><th style="text-align:left;padding:8px;">Text</th></tr>'
    for g in guidelines:
        html += f'<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">{g.get("guideline_type","")}</td><td style="padding:8px;">{g.get("guideline_scope","")}</td><td style="padding:8px;">{g.get("risk_level","")}</td><td style="padding:8px;">{g.get("standard_text","")[:100]}</td></tr>'
    html += "</table>"
    return html


async def _handle_upload_company(file):
    if file is None:
        return "No file selected", *await _list_contracts_ui()
    result = await client.upload_contract(file, "company")
    if result["success"]:
        return f"Uploaded: {result['data']['file_name']}", *await _list_contracts_ui()
    return f"Error: {result['error']}", *await _list_contracts_ui()


async def _handle_upload_client(file):
    if file is None:
        return "No file selected", *await _list_contracts_ui()
    result = await client.upload_contract(file, "client")
    if result["success"]:
        return f"Uploaded: {result['data']['file_name']}", *await _list_contracts_ui()
    return f"Error: {result['error']}", *await _list_contracts_ui()


async def _refresh_contracts():
    html, choices = await _list_contracts_ui()
    return html, choices, choices, choices


async def _handle_guideline_upload(company_json: str, client_json: str):
    msgs = []
    if company_json.strip():
        try:
            data = json.loads(company_json)
            guidelines = data if isinstance(data, list) else data.get("guidelines", [data])
            r = await client.upload_company_guidelines(guidelines)
            msgs.append(f"Company: {r.get('data',{}).get('message','ok') if r.get('success') else r.get('error')}")
        except json.JSONDecodeError:
            msgs.append("Company JSON invalid")
    if client_json.strip():
        try:
            data = json.loads(client_json)
            guidelines = data if isinstance(data, list) else data.get("guidelines", [data])
            r = await client.upload_user_guidelines(guidelines)
            msgs.append(f"Client: {r.get('data',{}).get('message','ok') if r.get('success') else r.get('error')}")
        except json.JSONDecodeError:
            msgs.append("Client JSON invalid")
    return "; ".join(msgs), await _list_guidelines_ui()


async def _handle_analyze(contract_id: str):
    if not contract_id:
        return "Select a contract first", ""
    result = await client.analyze_contract(contract_id)
    if not result["success"]:
        return f"Analysis failed: {result['error']}", ""
    data = result["data"]
    rc = _risk_class(data["overall_risk_score"])
    html = f'<div class="card" style="text-align:center;"><h2>Risk Score</h2><span style="font-size:48px;font-weight:bold;" class="{rc}">{data["overall_risk_score"]:.0%}</span><p>{data["risk_summary"]}</p></div>'

    if data.get("clauses"):
        html += '<h2>Clauses</h2><table style="width:100%;border-collapse:collapse;"><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px;">Type</th><th style="text-align:left;padding:8px;">Summary</th></tr>'
        for clause in data["clauses"]:
            html += f'<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">{clause["clause_type"]}</td><td style="padding:8px;">{clause["summary"][:150]}</td></tr>'
        html += "</table>"

    if data.get("missing_clauses"):
        html += '<h2>Missing Clauses</h2><table style="width:100%;border-collapse:collapse;"><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px;">Type</th><th style="text-align:left;padding:8px;">Severity</th><th style="text-align:left;padding:8px;">Reason</th></tr>'
        for m in data["missing_clauses"]:
            html += f'<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">{m["clause_type"]}</td><td style="padding:8px;">{m["severity"]}</td><td style="padding:8px;">{m["reason"][:200]}</td></tr>'
        html += "</table>"

    if data.get("mismatches"):
        html += '<h2>Mismatches</h2><table style="width:100%;border-collapse:collapse;"><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px;">Issue</th><th style="text-align:left;padding:8px;">Severity</th></tr>'
        for m in data["mismatches"]:
            html += f'<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">{m["issue"][:200]}</td><td style="padding:8px;">{m["severity"]}</td></tr>'
        html += "</table>"

    if data.get("party_conflicts"):
        html += '<h2>Party Conflicts</h2><table style="width:100%;border-collapse:collapse;"><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px;">Topic</th><th style="text-align:left;padding:8px;">Severity</th></tr>'
        for p in data["party_conflicts"]:
            html += f'<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">{p["topic"]}</td><td style="padding:8px;">{p["severity"]}</td></tr>'
        html += "</table>"

    return f"Analysis complete", html


async def _handle_compare(company_id: str, client_id: str):
    if not company_id or not client_id:
        return "Select both contracts", ""
    result = await client.compare_contracts(company_id, client_id)
    if not result["success"]:
        return f"Comparison failed: {result['error']}", ""
    data = result["data"]
    rc = _risk_class(data["overall_risk_score"])
    html = f'<div class="card" style="text-align:center;"><h2>Combined Risk Score</h2><span style="font-size:48px;font-weight:bold;" class="{rc}">{data["overall_risk_score"]:.0%}</span><p>{data["risk_summary"]}</p></div>'

    ca = data.get("company_analysis", {})
    cb = data.get("client_analysis", {})
    html += '<div style="display:flex;gap:16px;">'
    for label, ana in [("Company", ca), ("Client", cb)]:
        rc2 = _risk_class(ana.get("overall_risk_score", 0))
        html += f'<div class="card" style="flex:1;text-align:center;"><h3>{label}</h3><span style="font-size:28px;font-weight:bold;" class="{rc2}">{ana.get("overall_risk_score",0):.0%}</span></div>'
    html += "</div>"

    if data.get("cross_gaps"):
        html += '<h2>Cross-Gaps</h2><table style="width:100%;border-collapse:collapse;"><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px;">Clause Type</th><th style="text-align:left;padding:8px;">Present In</th><th style="text-align:left;padding:8px;">Severity</th></tr>'
        for g in data["cross_gaps"]:
            html += f'<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">{g["clause_type"]}</td><td style="padding:8px;">{g["present_in"]}</td><td style="padding:8px;">{g["severity"]}</td></tr>'
        html += "</table>"

    if data.get("term_conflicts"):
        html += '<h2>Term Conflicts</h2><table style="width:100%;border-collapse:collapse;"><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px;">Clause Type</th><th style="text-align:left;padding:8px;">Severity</th></tr>'
        for t in data["term_conflicts"]:
            html += f'<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">{t["clause_type"]}</td><td style="padding:8px;">{t["severity"]}</td></tr>'
        html += "</table>"

    return "Comparison complete", html


def _set_page(page: str):
    updates = {p: gr.update(visible=False) for p in ["dashboard_page", "contracts_page", "guidelines_page", "analyze_page", "compare_page"]}
    updates[page] = gr.update(visible=True)
    return tuple(updates[p] for p in ["dashboard_page", "contracts_page", "guidelines_page", "analyze_page", "compare_page"])


def create_app():
    with gr.Blocks(css=CSS, title="NexusCLM", theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate")) as app:
        # ─── STATES ────────────────────────────────────────────
        token_state = gr.State("")
        user_name = gr.State("")
        user_email = gr.State("")

        # ─── LOGIN SCREEN ──────────────────────────────────────
        with gr.Column(visible=True, elem_id="login_section", scale=1, min_width=400) as login_section:
            gr.Markdown("# NexusCLM", elem_id="login-title")
            gr.Markdown("### Contract Intelligence Engine")
            with gr.Row(equal_height=True):
                with gr.Column(scale=1):
                    pass
                with gr.Column(scale=2, min_width=400):
                    login_email = gr.Textbox(label="Email", placeholder="you@example.com")
                    login_password = gr.Textbox(label="Password", type="password", placeholder="min 6 characters")
                    login_name = gr.Textbox(label="Name (for registration)", placeholder="Your Name")
                    login_msg = gr.Markdown("")
                    with gr.Row():
                        login_btn = gr.Button("Login", variant="primary", elem_id="login-btn")
                        register_btn = gr.Button("Register")
                with gr.Column(scale=1):
                    pass

        # ─── MAIN APP SCREEN ───────────────────────────────────
        with gr.Row(visible=False, elem_id="app_section") as app_section:
            # ═══ SIDEBAR ════════════════════════════════════════
            with gr.Column(scale=1, elem_id="sidebar", min_width=200):
                gr.Markdown("## NexusCLM")
                user_display = gr.Markdown("")

                dashboard_btn = gr.Button("Dashboard", elem_classes="sidebar-btn")
                contracts_btn = gr.Button("Contracts", elem_classes="sidebar-btn")
                guidelines_btn = gr.Button("Guidelines", elem_classes="sidebar-btn")
                analyze_btn = gr.Button("Analyze", elem_classes="sidebar-btn")
                compare_btn = gr.Button("Compare", elem_classes="sidebar-btn")

                gr.Markdown("---")
                logout_btn = gr.Button("Logout", elem_classes="sidebar-btn")

            # ═══ CONTENT ═══════════════════════════════════════
            with gr.Column(scale=4, elem_id="content"):

                # -- Dashboard --
                with gr.Group(visible=True, elem_id="dashboard_page") as dashboard_page:
                    gr.Markdown("## Dashboard")
                    dashboard_html = gr.HTML("Loading...")
                    refresh_dash_btn = gr.Button("Refresh")

                # -- Contracts --
                with gr.Group(visible=False, elem_id="contracts_page") as contracts_page:
                    gr.Markdown("## Contracts")
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Upload Company Contract")
                            company_file = gr.File(file_types=[".pdf"], label="Company Contract")
                            company_upload_btn = gr.Button("Upload Company Contract", variant="primary")
                            company_msg = gr.Markdown("")
                        with gr.Column():
                            gr.Markdown("### Upload Client Contract")
                            client_file = gr.File(file_types=[".pdf"], label="Client Contract")
                            client_upload_btn = gr.Button("Upload Client Contract", variant="primary")
                            client_msg = gr.Markdown("")
                    gr.Markdown("### Existing Contracts")
                    contracts_html = gr.HTML("")
                    refresh_contracts_btn = gr.Button("Refresh Contracts")

                # -- Guidelines --
                with gr.Group(visible=False, elem_id="guidelines_page") as guidelines_page:
                    gr.Markdown("## Guidelines")
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Company Guidelines (JSON)")
                            company_guidelines_input = gr.Code(label="Company Guidelines JSON", language="json", value='[\n  {"type": "indemnification", "text": "Indemnification must be mutual", "risk_level": "high"}\n]')
                        with gr.Column():
                            gr.Markdown("### Client Guidelines (JSON)")
                            client_guidelines_input = gr.Code(label="Client Guidelines JSON", language="json", value='[\n  {"type": "liability", "text": "Liability cap must not exceed contract value", "risk_level": "medium"}\n]')
                    guideline_upload_btn = gr.Button("Upload Guidelines", variant="primary")
                    guideline_msg = gr.Markdown("")
                    gr.Markdown("### Existing Guidelines")
                    guidelines_html = gr.HTML("")
                    refresh_guidelines_btn = gr.Button("Refresh Guidelines")

                # -- Analyze --
                with gr.Group(visible=False, elem_id="analyze_page") as analyze_page:
                    gr.Markdown("## Analyze Contract")
                    analyze_contract_dropdown = gr.Dropdown(label="Select Contract", choices=[], value=None, interactive=True)
                    analyze_btn2 = gr.Button("Run Analysis", variant="primary")
                    analyze_msg = gr.Markdown("")
                    analyze_results = gr.HTML("")

                # -- Compare --
                with gr.Group(visible=False, elem_id="compare_page") as compare_page:
                    gr.Markdown("## Compare Contracts")
                    with gr.Row():
                        with gr.Column():
                            compare_company_dropdown = gr.Dropdown(label="Company Contract", choices=[], value=None, interactive=True)
                        with gr.Column():
                            compare_client_dropdown = gr.Dropdown(label="Client Contract", choices=[], value=None, interactive=True)
                    compare_btn2 = gr.Button("Run Comparison", variant="primary")
                    compare_msg = gr.Markdown("")
                    compare_results = gr.HTML("")

        # ═══ EVENT HANDLERS ════════════════════════════════════

        # Login / Register
        login_btn.click(
            _handle_login,
            inputs=[login_email, login_password],
            outputs=[user_name, user_email, token_state, login_section, app_section],
        ).then(
            lambda name, email: f"**{name}** ({email})",
            inputs=[user_name, user_email],
            outputs=[user_display],
        ).then(
            _load_dashboard, outputs=[dashboard_html]
        )

        register_btn.click(
            _handle_register,
            inputs=[login_email, login_password, login_name],
            outputs=[login_msg, user_name, user_email, token_state, login_section, app_section],
        ).then(
            lambda name, email: f"**{name}** ({email})",
            inputs=[user_name, user_email],
            outputs=[user_display],
        ).then(
            _load_dashboard, outputs=[dashboard_html]
        )

        # Sidebar navigation
        dashboard_btn.click(lambda: _set_page("dashboard_page"), outputs=[dashboard_page, contracts_page, guidelines_page, analyze_page, compare_page]).then(_load_dashboard, outputs=[dashboard_html])
        contracts_btn.click(lambda: _set_page("contracts_page"), outputs=[dashboard_page, contracts_page, guidelines_page, analyze_page, compare_page]).then(_list_contracts_ui, outputs=[contracts_html, contracts_html])
        guidelines_btn.click(lambda: _set_page("guidelines_page"), outputs=[dashboard_page, contracts_page, guidelines_page, analyze_page, compare_page]).then(_list_guidelines_ui, outputs=[guidelines_html])
        analyze_btn.click(lambda: _set_page("analyze_page"), outputs=[dashboard_page, contracts_page, guidelines_page, analyze_page, compare_page]).then(_refresh_contracts, outputs=[contracts_html, analyze_contract_dropdown, compare_company_dropdown, compare_client_dropdown])
        compare_btn.click(lambda: _set_page("compare_page"), outputs=[dashboard_page, contracts_page, guidelines_page, analyze_page, compare_page]).then(_refresh_contracts, outputs=[contracts_html, analyze_contract_dropdown, compare_company_dropdown, compare_client_dropdown])

        # Dashboard refresh
        refresh_dash_btn.click(_load_dashboard, outputs=[dashboard_html])

        # Contract uploads
        company_upload_btn.click(_handle_upload_company, inputs=[company_file], outputs=[company_msg, contracts_html, contracts_html]).then(_refresh_contracts, outputs=[contracts_html, analyze_contract_dropdown, compare_company_dropdown, compare_client_dropdown])
        client_upload_btn.click(_handle_upload_client, inputs=[client_file], outputs=[client_msg, contracts_html, contracts_html]).then(_refresh_contracts, outputs=[contracts_html, analyze_contract_dropdown, compare_company_dropdown, compare_client_dropdown])
        refresh_contracts_btn.click(_refresh_contracts, outputs=[contracts_html, analyze_contract_dropdown, compare_company_dropdown, compare_client_dropdown])

        # Guideline upload
        guideline_upload_btn.click(_handle_guideline_upload, inputs=[company_guidelines_input, client_guidelines_input], outputs=[guideline_msg, guidelines_html])
        refresh_guidelines_btn.click(_list_guidelines_ui, outputs=[guidelines_html])

        # Analyze
        analyze_btn2.click(lambda: gr.update(visible=True), outputs=[analyze_page]).then(_handle_analyze, inputs=[analyze_contract_dropdown], outputs=[analyze_msg, analyze_results]).then(_refresh_contracts, outputs=[contracts_html, analyze_contract_dropdown, compare_company_dropdown, compare_client_dropdown])

        # Compare
        compare_btn2.click(_handle_compare, inputs=[compare_company_dropdown, compare_client_dropdown], outputs=[compare_msg, compare_results]).then(_refresh_contracts, outputs=[contracts_html, analyze_contract_dropdown, compare_company_dropdown, compare_client_dropdown])

        # Logout
        logout_btn.click(
            lambda: ("", "", "", gr.update(visible=True), gr.update(visible=False)),
            outputs=[user_name, user_email, token_state, login_section, app_section],
        ).then(
            lambda: gr.update(value=""), outputs=[login_msg]
        )

    return app


app = create_app()
