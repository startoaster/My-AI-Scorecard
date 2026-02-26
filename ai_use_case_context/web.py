"""
Web dashboard for the AI Use Case Context Framework.

A lightweight Flask app that provides:
  - Portfolio dashboard with risk heatmap, blocker list, and dimension overview
  - Per-use-case score reports with flag details
  - Actions: resolve, accept risk, begin review, add flags
  - Demo data seeding for quick evaluation
  - Python hooks for staying in sync with the underlying API

Run directly:
    python -m ai_use_case_context.web

Or from code:
    from ai_use_case_context.web import create_app, get_dashboard, on

    # Access the live dashboard from Python
    dashboard = get_dashboard()
    dashboard.register(my_use_case)

    # Subscribe to web events
    @on("flag_resolved")
    def handle_resolve(use_case_name, flag_index, flag):
        print(f"Flag resolved on {use_case_name}: {flag.description}")

    app = create_app()
    app.run()
"""

from __future__ import annotations

import html
from datetime import datetime, timedelta
from typing import Callable

from flask import Flask, request, redirect, url_for

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    RiskFlag,
    UseCaseContext,
)
from ai_use_case_context.dashboard import GovernanceDashboard
from ai_use_case_context.escalation import EscalationPolicy


# ---------------------------------------------------------------------------
# Shared state (in-memory for this lightweight server)
# ---------------------------------------------------------------------------

_dashboard = GovernanceDashboard()
_escalation_policy = EscalationPolicy()

# ---------------------------------------------------------------------------
# Event hook system — keeps Python callers in sync with web actions
# ---------------------------------------------------------------------------

# Event names:
#   "use_case_registered"  -> (use_case: UseCaseContext)
#   "flag_added"           -> (use_case_name: str, flag: RiskFlag)
#   "flag_resolved"        -> (use_case_name: str, flag_index: int, flag: RiskFlag)
#   "flag_accepted"        -> (use_case_name: str, flag_index: int, flag: RiskFlag)
#   "flag_review_started"  -> (use_case_name: str, flag_index: int, flag: RiskFlag)
#   "escalation_applied"   -> (use_case_name: str, count: int, results: list)
#   "dashboard_reset"      -> ()

_hooks: dict[str, list[Callable]] = {}


def on(event: str, callback: Callable | None = None):
    """Register a callback for a web dashboard event.

    Can be used as a decorator or called directly::

        @on("flag_resolved")
        def my_handler(use_case_name, flag_index, flag):
            ...

        # or
        on("flag_resolved", my_handler)
    """
    def _register(fn: Callable) -> Callable:
        _hooks.setdefault(event, []).append(fn)
        return fn

    if callback is not None:
        _register(callback)
        return callback
    return _register


def off(event: str, callback: Callable | None = None):
    """Remove a hook. If callback is None, removes all hooks for the event."""
    if callback is None:
        _hooks.pop(event, None)
    elif event in _hooks:
        _hooks[event] = [cb for cb in _hooks[event] if cb is not callback]


def _emit(event: str, *args, **kwargs):
    """Fire all callbacks registered for an event."""
    for cb in _hooks.get(event, []):
        cb(*args, **kwargs)


# ---------------------------------------------------------------------------
# Dashboard access — two-way sync between Python and web
# ---------------------------------------------------------------------------

def get_dashboard() -> GovernanceDashboard:
    """Return the live GovernanceDashboard backing the web UI.

    Any changes you make to the returned object (register use cases,
    modify flags, etc.) are immediately reflected in the web interface.
    """
    return _dashboard


def set_dashboard(dashboard: GovernanceDashboard) -> None:
    """Replace the web UI's backing dashboard with your own instance.

    Use this to point the web UI at a dashboard you've already built
    in Python, so the web view stays in sync with your application state.
    """
    global _dashboard
    _dashboard = dashboard
    _emit("dashboard_reset")


def get_escalation_policy() -> EscalationPolicy:
    """Return the escalation policy used by the web UI."""
    return _escalation_policy


def set_escalation_policy(policy: EscalationPolicy) -> None:
    """Replace the escalation policy used by the web UI."""
    global _escalation_policy
    _escalation_policy = policy

# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

_LEVEL_COLORS = {
    RiskLevel.NONE: ("#6b7280", "#f3f4f6"),      # gray
    RiskLevel.LOW: ("#2563eb", "#dbeafe"),         # blue
    RiskLevel.MEDIUM: ("#d97706", "#fef3c7"),      # amber
    RiskLevel.HIGH: ("#ea580c", "#ffedd5"),         # orange
    RiskLevel.CRITICAL: ("#dc2626", "#fee2e2"),    # red
}

_STATUS_COLORS = {
    ReviewStatus.OPEN: "#f59e0b",
    ReviewStatus.IN_REVIEW: "#3b82f6",
    ReviewStatus.RESOLVED: "#10b981",
    ReviewStatus.ACCEPTED: "#8b5cf6",
    ReviewStatus.BLOCKED: "#ef4444",
}


def _e(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(str(text))


def _badge(text: str, fg: str, bg: str) -> str:
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
        f'font-size:0.8rem;font-weight:600;color:{fg};background:{bg}">'
        f'{_e(text)}</span>'
    )


def _level_badge(level: RiskLevel) -> str:
    fg, bg = _LEVEL_COLORS.get(level, ("#6b7280", "#f3f4f6"))
    return _badge(level.name, fg, bg)


def _status_badge(status: ReviewStatus) -> str:
    color = _STATUS_COLORS.get(status, "#6b7280")
    return _badge(status.value, "#fff", color)


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

_CSS = """
:root { --bg: #f8fafc; --card: #fff; --border: #e2e8f0; --text: #1e293b; --muted: #64748b; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       background: var(--bg); color: var(--text); line-height: 1.5; }
.container { max-width: 1100px; margin: 0 auto; padding: 24px 16px; }
nav { background: #0f172a; color: #fff; padding: 12px 0; }
nav .container { display: flex; align-items: center; gap: 24px; }
nav a { color: #94a3b8; text-decoration: none; font-weight: 500; font-size: 0.95rem; }
nav a:hover, nav a.active { color: #fff; }
nav .brand { font-weight: 700; font-size: 1.15rem; color: #fff; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
.card h3 { font-size: 0.85rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.card .num { font-size: 2rem; font-weight: 700; }
.section { background: var(--card); border: 1px solid var(--border); border-radius: 12px;
           padding: 24px; margin-bottom: 24px; }
.section h2 { margin-bottom: 16px; font-size: 1.25rem; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 0.9rem; }
th { color: var(--muted); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }
tr:last-child td { border-bottom: none; }
.heatmap { display: grid; grid-template-columns: 180px repeat(4, 1fr); gap: 2px; font-size: 0.85rem; }
.heatmap .header { font-weight: 600; color: var(--muted); padding: 8px; text-align: center; font-size: 0.75rem; text-transform: uppercase; }
.heatmap .label { padding: 8px; font-weight: 500; display: flex; align-items: center; }
.heatmap .cell { padding: 8px; text-align: center; border-radius: 6px; font-weight: 600; }
a.btn { display: inline-block; padding: 6px 14px; border-radius: 8px; font-size: 0.85rem;
        text-decoration: none; font-weight: 500; border: 1px solid var(--border); color: var(--text);
        background: var(--card); cursor: pointer; }
a.btn:hover { background: #f1f5f9; }
a.btn-primary { background: #2563eb; color: #fff; border-color: #2563eb; }
a.btn-primary:hover { background: #1d4ed8; }
.actions { display: flex; gap: 6px; flex-wrap: wrap; }
form.inline { display: inline; }
form.inline button { padding: 4px 12px; border-radius: 6px; font-size: 0.8rem;
                     border: 1px solid var(--border); cursor: pointer; background: var(--card); }
form.inline button:hover { background: #f1f5f9; }
select, input[type=text], input[type=number] { padding: 6px 10px; border: 1px solid var(--border);
       border-radius: 6px; font-size: 0.9rem; }
.form-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: end; margin-bottom: 12px; }
.form-group { display: flex; flex-direction: column; gap: 2px; }
.form-group label { font-size: 0.75rem; color: var(--muted); font-weight: 600; text-transform: uppercase; }
.flash { padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 0.9rem; }
.flash-success { background: #dcfce7; color: #166534; }
.flash-error { background: #fee2e2; color: #991b1b; }
.empty { color: var(--muted); text-align: center; padding: 32px; font-size: 0.95rem; }
"""


def _layout(title: str, body: str, active: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(title)} — AI Governance</title>
<style>{_CSS}</style></head>
<body>
<nav><div class="container">
  <a href="/" class="brand">AI Governance</a>
  <a href="/" class="{'active' if active == 'dashboard' else ''}">Dashboard</a>
  <a href="/scores" class="{'active' if active == 'scores' else ''}">Score Reports</a>
  <a href="/reviewers" class="{'active' if active == 'reviewers' else ''}">Reviewers</a>
  <a href="/seed" class="{'active' if active == 'seed' else ''}">Seed Demo Data</a>
</div></nav>
<div class="container">{body}</div>
</body></html>"""


# ---------------------------------------------------------------------------
# Flask app factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    app = Flask(__name__)

    def _flash_html(msg: str, kind: str = "success") -> str:
        return f'<div class="flash flash-{kind}">{_e(msg)}</div>'

    # ---- Dashboard (home) ------------------------------------------------

    @app.route("/")
    def dashboard():
        ucs = _dashboard.use_cases
        total = len(ucs)
        blocked = _dashboard.blocked_use_cases()
        clear = _dashboard.clear_use_cases()
        all_flags = _dashboard.all_flags()
        blocking_count = sum(1 for _, f in all_flags if f.is_blocking)
        pending_count = sum(1 for _, f in all_flags if f.needs_review)

        # KPI cards
        body = '<h1 style="margin-bottom:20px">Portfolio Dashboard</h1>'
        body += '<div class="cards">'
        body += f'<div class="card"><h3>Use Cases</h3><div class="num">{total}</div></div>'
        body += (
            f'<div class="card"><h3>Blocked</h3>'
            f'<div class="num" style="color:#dc2626">{len(blocked)}</div></div>'
        )
        body += f'<div class="card"><h3>Clear</h3><div class="num" style="color:#10b981">{len(clear)}</div></div>'
        body += f'<div class="card"><h3>Total Flags</h3><div class="num">{len(all_flags)}</div></div>'
        body += f'<div class="card"><h3>Blocking</h3><div class="num" style="color:#ea580c">{blocking_count}</div></div>'
        body += f'<div class="card"><h3>Pending Review</h3><div class="num" style="color:#d97706">{pending_count}</div></div>'
        body += '</div>'

        # Risk heatmap
        if ucs:
            scores = _dashboard.portfolio_risk_scores()
            body += '<div class="section"><h2>Risk Heatmap</h2><div class="heatmap">'
            body += '<div class="header"></div>'
            for dim in RiskDimension:
                short = dim.value.split("/")[0].split("(")[0].strip()
                body += f'<div class="header">{_e(short)}</div>'
            for uc_name, dim_scores in scores.items():
                body += f'<div class="label"><a href="/use-case/{_e(uc_name)}" style="color:inherit;text-decoration:none">{_e(uc_name)}</a></div>'
                for dim in RiskDimension:
                    val = dim_scores.get(dim.value, 0)
                    level = RiskLevel(val)
                    fg, bg = _LEVEL_COLORS[level]
                    body += f'<div class="cell" style="background:{bg};color:{fg}">{level.name}</div>'
            body += '</div></div>'

        # Dimension overview
        body += '<div class="section"><h2>Dimension Overview</h2><table>'
        body += '<tr><th>Dimension</th><th>Max Level</th><th>Open</th><th>Blocking</th><th>Total</th><th>Affected Use Cases</th></tr>'
        for dim in RiskDimension:
            ds = _dashboard.dimension_summary(dim)
            body += f'<tr><td>{_e(dim.value)}</td><td>{_level_badge(ds.max_level)}</td>'
            body += f'<td>{ds.open_flags}</td><td>{ds.blocking_flags}</td><td>{ds.total_flags}</td>'
            body += f'<td>{_e(", ".join(ds.affected_use_cases) or "—")}</td></tr>'
        body += '</table></div>'

        # Use case list
        body += '<div class="section"><h2>Use Cases</h2>'
        if not ucs:
            body += '<div class="empty">No use cases registered. <a href="/seed">Seed demo data</a> or <a href="/add-use-case">add one</a>.</div>'
        else:
            body += '<table><tr><th>Name</th><th>Phase</th><th>Status</th><th>Max Risk</th><th>Flags</th><th></th></tr>'
            for uc in ucs:
                status = "BLOCKED" if uc.is_blocked() else "CLEAR"
                sc = "#dc2626" if uc.is_blocked() else "#10b981"
                body += f'<tr><td><a href="/use-case/{_e(uc.name)}">{_e(uc.name)}</a></td>'
                body += f'<td>{_e(uc.workflow_phase or "—")}</td>'
                body += f'<td style="color:{sc};font-weight:600">{status}</td>'
                body += f'<td>{_level_badge(uc.max_risk_level())}</td>'
                body += f'<td>{len(uc.risk_flags)}</td>'
                body += f'<td><a class="btn" href="/use-case/{_e(uc.name)}">View</a></td></tr>'
            body += '</table>'
        body += '<div style="margin-top:16px"><a class="btn btn-primary" href="/add-use-case">+ Add Use Case</a></div>'
        body += '</div>'

        return _layout("Dashboard", body, active="dashboard")

    # ---- Score reports ---------------------------------------------------

    @app.route("/scores")
    def scores():
        ucs = _dashboard.use_cases

        body = '<h1 style="margin-bottom:20px">Score Reports</h1>'

        if not ucs:
            body += '<div class="section"><div class="empty">No use cases registered. <a href="/seed">Seed demo data</a> to get started.</div></div>'
            return _layout("Score Reports", body, active="scores")

        for uc in ucs:
            risk_scores = uc.risk_score()
            total_score = sum(risk_scores.values())
            max_possible = len(RiskDimension) * RiskLevel.CRITICAL.value

            body += '<div class="section">'
            body += f'<h2><a href="/use-case/{_e(uc.name)}" style="color:inherit;text-decoration:none">{_e(uc.name)}</a></h2>'
            body += f'<p style="color:var(--muted);margin-bottom:16px">{_e(uc.description or uc.workflow_phase or "")}</p>'

            # Score bar
            pct = int((total_score / max_possible) * 100) if max_possible else 0
            bar_color = "#10b981" if pct <= 25 else "#d97706" if pct <= 50 else "#ea580c" if pct <= 75 else "#dc2626"
            body += f'<div style="margin-bottom:16px"><strong>Composite Risk Score: {total_score} / {max_possible}</strong>'
            body += f'<div style="background:#e2e8f0;border-radius:8px;height:12px;margin-top:6px;overflow:hidden">'
            body += f'<div style="width:{pct}%;height:100%;background:{bar_color};border-radius:8px;transition:width 0.3s"></div>'
            body += '</div></div>'

            # Per-dimension scores
            body += '<table><tr><th>Dimension</th><th>Score</th><th>Level</th><th>Open Flags</th></tr>'
            for dim in RiskDimension:
                val = risk_scores.get(dim.value, 0)
                level = RiskLevel(val)
                open_count = sum(
                    1 for f in uc.get_flags_by_dimension(dim)
                    if f.status not in (ReviewStatus.RESOLVED, ReviewStatus.ACCEPTED)
                )
                body += f'<tr><td>{_e(dim.value)}</td>'
                body += f'<td><strong>{val}</strong> / {RiskLevel.CRITICAL.value}</td>'
                body += f'<td>{_level_badge(level)}</td>'
                body += f'<td>{open_count}</td></tr>'
            body += '</table></div>'

        # Escalation check
        body += '<div class="section"><h2>Escalation Check</h2>'
        any_escalations = False
        for uc in ucs:
            results = _escalation_policy.check_use_case(uc)
            if results:
                any_escalations = True
                for r in results:
                    body += f'<div class="flash flash-error">'
                    body += f'<strong>{_e(uc.name)}</strong>: {_e(r.message)}'
                    body += '</div>'
        if not any_escalations:
            body += '<div class="empty">No flags currently require escalation.</div>'
        body += '</div>'

        return _layout("Score Reports", body, active="scores")

    # ---- Reviewer workload -----------------------------------------------

    @app.route("/reviewers")
    def reviewers():
        workload = _dashboard.reviewer_workload()

        body = '<h1 style="margin-bottom:20px">Reviewer Workload</h1>'
        if not workload:
            body += '<div class="section"><div class="empty">No pending reviews.</div></div>'
            return _layout("Reviewers", body, active="reviewers")

        for reviewer, items in sorted(workload.items(), key=lambda x: -len(x[1])):
            body += '<div class="section">'
            body += f'<h2>{_e(reviewer)} <span style="color:var(--muted);font-weight:400;font-size:1rem">({len(items)} item{"s" if len(items) != 1 else ""})</span></h2>'
            body += '<table><tr><th>Use Case</th><th>Dimension</th><th>Level</th><th>Status</th><th>Description</th></tr>'
            for uc_name, flag in items:
                body += f'<tr><td><a href="/use-case/{_e(uc_name)}">{_e(uc_name)}</a></td>'
                body += f'<td>{_e(flag.dimension.value)}</td>'
                body += f'<td>{_level_badge(flag.level)}</td>'
                body += f'<td>{_status_badge(flag.status)}</td>'
                body += f'<td>{_e(flag.description)}</td></tr>'
            body += '</table></div>'

        return _layout("Reviewers", body, active="reviewers")

    # ---- Use case detail -------------------------------------------------

    @app.route("/use-case/<name>")
    def use_case_detail(name):
        uc = _dashboard._use_cases.get(name)
        if not uc:
            return _layout("Not Found", '<div class="section"><div class="empty">Use case not found.</div></div>')

        flash = ""
        msg = request.args.get("msg")
        if msg:
            flash = _flash_html(msg)

        body = flash
        body += f'<h1 style="margin-bottom:4px">{_e(uc.name)}</h1>'
        if uc.description:
            body += f'<p style="color:var(--muted);margin-bottom:4px">{_e(uc.description)}</p>'
        body += f'<p style="color:var(--muted);margin-bottom:20px">Phase: {_e(uc.workflow_phase or "—")} &nbsp;|&nbsp; Tags: {_e(", ".join(uc.tags) or "—")}</p>'

        # Status card
        status_label = "BLOCKED" if uc.is_blocked() else "CLEAR"
        status_color = "#dc2626" if uc.is_blocked() else "#10b981"
        body += '<div class="cards">'
        body += f'<div class="card"><h3>Status</h3><div class="num" style="color:{status_color}">{status_label}</div></div>'
        body += f'<div class="card"><h3>Max Risk</h3><div class="num">{_level_badge(uc.max_risk_level())}</div></div>'
        body += f'<div class="card"><h3>Total Flags</h3><div class="num">{len(uc.risk_flags)}</div></div>'
        body += f'<div class="card"><h3>Blockers</h3><div class="num" style="color:#ea580c">{len(uc.get_blockers())}</div></div>'
        body += '</div>'

        # Score breakdown
        risk_scores = uc.risk_score()
        body += '<div class="section"><h2>Risk Score Breakdown</h2><table>'
        body += '<tr><th>Dimension</th><th>Score</th><th>Level</th></tr>'
        for dim in RiskDimension:
            val = risk_scores.get(dim.value, 0)
            body += f'<tr><td>{_e(dim.value)}</td><td>{val} / {RiskLevel.CRITICAL.value}</td><td>{_level_badge(RiskLevel(val))}</td></tr>'
        body += '</table></div>'

        # Flags table
        body += '<div class="section"><h2>Risk Flags</h2>'
        if not uc.risk_flags:
            body += '<div class="empty">No flags yet.</div>'
        else:
            body += '<table><tr><th>Dimension</th><th>Level</th><th>Description</th><th>Reviewer</th><th>Status</th><th>Actions</th></tr>'
            for i, flag in enumerate(uc.risk_flags):
                body += f'<tr><td>{_e(flag.dimension.value)}</td>'
                body += f'<td>{_level_badge(flag.level)}</td>'
                body += f'<td>{_e(flag.description)}</td>'
                body += f'<td>{_e(flag.reviewer)}</td>'
                body += f'<td>{_status_badge(flag.status)}</td>'
                body += '<td class="actions">'
                if flag.status == ReviewStatus.OPEN:
                    body += f'<form class="inline" method="post" action="/use-case/{_e(name)}/flag/{i}/review"><button>Begin Review</button></form>'
                if flag.status in (ReviewStatus.OPEN, ReviewStatus.IN_REVIEW, ReviewStatus.BLOCKED):
                    body += f'<form class="inline" method="post" action="/use-case/{_e(name)}/flag/{i}/resolve"><button style="color:#10b981">Resolve</button></form>'
                    body += f'<form class="inline" method="post" action="/use-case/{_e(name)}/flag/{i}/accept"><button style="color:#8b5cf6">Accept Risk</button></form>'
                body += '</td></tr>'
            body += '</table>'
        body += '</div>'

        # Add flag form
        body += '<div class="section"><h2>Add Risk Flag</h2>'
        body += f'<form method="post" action="/use-case/{_e(name)}/add-flag">'
        body += '<div class="form-row">'
        body += '<div class="form-group"><label>Dimension</label><select name="dimension">'
        for dim in RiskDimension:
            body += f'<option value="{dim.name}">{_e(dim.value)}</option>'
        body += '</select></div>'
        body += '<div class="form-group"><label>Level</label><select name="level">'
        for lvl in RiskLevel:
            if lvl != RiskLevel.NONE:
                body += f'<option value="{lvl.name}">{lvl.name}</option>'
        body += '</select></div>'
        body += '<div class="form-group" style="flex:1"><label>Description</label><input type="text" name="description" style="width:100%" required></div>'
        body += '</div>'
        body += '<button class="btn btn-primary" type="submit" style="border:none;padding:8px 20px;color:#fff;cursor:pointer">Add Flag</button>'
        body += '</form></div>'

        # Escalation
        results = _escalation_policy.check_use_case(uc)
        if results:
            body += '<div class="section"><h2>Escalation Alerts</h2>'
            for r in results:
                body += f'<div class="flash flash-error">{_e(r.message)}</div>'
            body += f'<form method="post" action="/use-case/{_e(name)}/escalate">'
            body += '<button class="btn" style="background:#dc2626;color:#fff;border-color:#dc2626;cursor:pointer" type="submit">Apply Escalations</button>'
            body += '</form></div>'

        body += f'<div style="margin-top:16px"><a class="btn" href="/">&larr; Back to Dashboard</a></div>'
        return _layout(uc.name, body)

    # ---- Actions ---------------------------------------------------------

    @app.route("/use-case/<name>/flag/<int:idx>/resolve", methods=["POST"])
    def resolve_flag(name, idx):
        uc = _dashboard._use_cases.get(name)
        if uc and 0 <= idx < len(uc.risk_flags):
            uc.risk_flags[idx].resolve("Resolved via web dashboard")
            _emit("flag_resolved", name, idx, uc.risk_flags[idx])
        return redirect(url_for("use_case_detail", name=name, msg="Flag resolved"))

    @app.route("/use-case/<name>/flag/<int:idx>/accept", methods=["POST"])
    def accept_flag(name, idx):
        uc = _dashboard._use_cases.get(name)
        if uc and 0 <= idx < len(uc.risk_flags):
            uc.risk_flags[idx].accept_risk("Risk accepted via web dashboard")
            _emit("flag_accepted", name, idx, uc.risk_flags[idx])
        return redirect(url_for("use_case_detail", name=name, msg="Risk accepted"))

    @app.route("/use-case/<name>/flag/<int:idx>/review", methods=["POST"])
    def review_flag(name, idx):
        uc = _dashboard._use_cases.get(name)
        if uc and 0 <= idx < len(uc.risk_flags):
            uc.risk_flags[idx].begin_review()
            _emit("flag_review_started", name, idx, uc.risk_flags[idx])
        return redirect(url_for("use_case_detail", name=name, msg="Review started"))

    @app.route("/use-case/<name>/add-flag", methods=["POST"])
    def add_flag(name):
        uc = _dashboard._use_cases.get(name)
        if uc:
            dim = RiskDimension[request.form["dimension"]]
            level = RiskLevel[request.form["level"]]
            desc = request.form.get("description", "").strip()
            if desc:
                flag = uc.flag_risk(dim, level, desc)
                _emit("flag_added", name, flag)
        return redirect(url_for("use_case_detail", name=name, msg="Flag added"))

    @app.route("/use-case/<name>/escalate", methods=["POST"])
    def escalate(name):
        uc = _dashboard._use_cases.get(name)
        if uc:
            results = _escalation_policy.apply_escalations(uc)
            count = len(results)
            _emit("escalation_applied", name, count, results)
            return redirect(url_for("use_case_detail", name=name, msg=f"{count} escalation(s) applied"))
        return redirect(url_for("use_case_detail", name=name))

    # ---- Add use case ----------------------------------------------------

    @app.route("/add-use-case", methods=["GET", "POST"])
    def add_use_case():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            desc = request.form.get("description", "").strip()
            phase = request.form.get("phase", "").strip()
            tags_raw = request.form.get("tags", "").strip()
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
            if name:
                uc = UseCaseContext(name=name, description=desc, workflow_phase=phase, tags=tags)
                _dashboard.register(uc)
                _emit("use_case_registered", uc)
                return redirect(url_for("use_case_detail", name=name, msg="Use case created"))

        body = '<h1 style="margin-bottom:20px">Add Use Case</h1>'
        body += '<div class="section"><form method="post">'
        body += '<div class="form-row"><div class="form-group" style="flex:1"><label>Name</label><input type="text" name="name" style="width:100%" required></div></div>'
        body += '<div class="form-row"><div class="form-group" style="flex:1"><label>Description</label><input type="text" name="description" style="width:100%"></div></div>'
        body += '<div class="form-row">'
        body += '<div class="form-group" style="flex:1"><label>Workflow Phase</label><input type="text" name="phase" style="width:100%"></div>'
        body += '<div class="form-group" style="flex:1"><label>Tags (comma-separated)</label><input type="text" name="tags" style="width:100%"></div>'
        body += '</div>'
        body += '<button class="btn btn-primary" type="submit" style="border:none;padding:8px 20px;color:#fff;cursor:pointer;margin-top:8px">Create Use Case</button>'
        body += '</form></div>'
        body += '<div style="margin-top:16px"><a class="btn" href="/">&larr; Back to Dashboard</a></div>'
        return _layout("Add Use Case", body)

    # ---- Seed demo data --------------------------------------------------

    @app.route("/seed")
    def seed():
        _dashboard._use_cases.clear()

        # 1. AI Upscaling - Hero Shots
        uc1 = UseCaseContext(
            name="AI Upscaling - Hero Shots",
            description="Use AI super-resolution on key character close-ups",
            workflow_phase="Element Regeneration",
            tags=["upscaling", "characters", "post-production"],
        )
        uc1.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "Character likenesses may trigger actor likeness rights")
        uc1.flag_risk(RiskDimension.ETHICAL, RiskLevel.MEDIUM, "AI may subtly alter skin tones or features")
        uc1.flag_risk(RiskDimension.TECHNICAL, RiskLevel.LOW, "Output resolution capped at 4K")
        f = uc1.flag_risk(RiskDimension.COMMS, RiskLevel.LOW, "Minor PR consideration for AI-enhanced shots")
        f.resolve("Covered by standard AI disclosure in credits")

        # 2. AI Background Extension
        uc2 = UseCaseContext(
            name="AI Background Extension",
            description="Use generative AI to extend set backgrounds for wide shots",
            workflow_phase="Element Regeneration",
            tags=["generation", "backgrounds", "set-extension"],
        )
        uc2.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.MEDIUM, "Generated content may resemble copyrighted locations")
        uc2.flag_risk(RiskDimension.TECHNICAL, RiskLevel.MEDIUM, "Temporal consistency across frames needs validation")

        # 3. AI Voice Synthesis
        uc3 = UseCaseContext(
            name="AI Voice Synthesis - ADR",
            description="AI-generated dialogue replacement for minor background characters",
            workflow_phase="Audio Post-Production",
            tags=["voice", "synthesis", "ADR"],
        )
        uc3.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.CRITICAL, "Voice synthesis may violate SAG-AFTRA agreements")
        uc3.flag_risk(RiskDimension.ETHICAL, RiskLevel.HIGH, "Consent and disclosure requirements for AI voices")
        uc3.flag_risk(RiskDimension.COMMS, RiskLevel.HIGH, "Public backlash risk if AI voice use is perceived negatively")
        uc3.flag_risk(RiskDimension.TECHNICAL, RiskLevel.MEDIUM, "Voice quality may not match production standards")

        # 4. AI Color Grading
        uc4 = UseCaseContext(
            name="AI Color Grading Assistant",
            description="AI-suggested color grades based on mood and reference frames",
            workflow_phase="Color & Finishing",
            tags=["color", "grading", "finishing"],
        )
        uc4.flag_risk(RiskDimension.TECHNICAL, RiskLevel.LOW, "AI suggestions are advisory only — colorist has final say")
        f = uc4.flag_risk(RiskDimension.ETHICAL, RiskLevel.LOW, "Minimal bias concern for color palette suggestions")
        f.resolve("No human likeness involved — low risk confirmed")

        # 5. AI Script Analysis (stale flag for escalation demo)
        uc5 = UseCaseContext(
            name="AI Script Analysis",
            description="NLP-based script breakdown for scheduling and budgeting",
            workflow_phase="Pre-Production",
            tags=["NLP", "script", "scheduling"],
        )
        stale = uc5.flag_risk(RiskDimension.ETHICAL, RiskLevel.MEDIUM, "Bias in scene complexity scoring")
        stale.created_at = datetime.now() - timedelta(days=5)

        for uc in [uc1, uc2, uc3, uc4, uc5]:
            _dashboard.register(uc)

        body = '<h1 style="margin-bottom:20px">Demo Data Seeded</h1>'
        body += '<div class="section">'
        body += '<p>5 use cases with realistic risk flags have been loaded:</p><ul style="margin:12px 0 12px 20px">'
        body += '<li><strong>AI Upscaling - Hero Shots</strong> — 1 blocker (Legal/IP HIGH)</li>'
        body += '<li><strong>AI Background Extension</strong> — 2 flags, needs review</li>'
        body += '<li><strong>AI Voice Synthesis - ADR</strong> — 4 flags, CRITICAL blocker</li>'
        body += '<li><strong>AI Color Grading Assistant</strong> — clear, low risk</li>'
        body += '<li><strong>AI Script Analysis</strong> — stale flag (5 days old, will trigger escalation)</li>'
        body += '</ul>'
        body += '<a class="btn btn-primary" href="/">Go to Dashboard</a>'
        body += '</div>'
        return _layout("Seed Demo Data", body, active="seed")

    return app


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import sys

    port = 5000
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg in ("--port", "-p") and i < len(sys.argv) - 1:
            port = int(sys.argv[i + 1])

    app = create_app()
    print(f"Starting AI Governance Dashboard on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
