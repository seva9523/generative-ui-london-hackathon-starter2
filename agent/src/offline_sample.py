"""Canned FundLens dashboard inputs for OFFLINE=1 mode.

When OFFLINE=1 is set, the /fixed agent serves a deterministic sample
dashboard with NO Gemini call and no API key (see fixed_agent.py). These
args are passed verbatim to `render_dashboard(**OFFLINE_DASHBOARD_ARGS)`,
so they MUST satisfy that tool's typed inputs.
"""
from __future__ import annotations

from typing import Any

OFFLINE_DASHBOARD_ARGS: dict[str, Any] = {
    "eyebrow": "INVESTMENT SNAPSHOT · B2B SAAS · SEED",
    "title": "Northstar Analytics",
    "subtitle": "Evidence suggests a seed-stage analytics startup selling workflow intelligence to finance teams; pricing and full retention detail are not stated.",
    "kpis": [
        {
            "label": "Stage",
            "value": "Seed",
            "delta": "",
            "caption": "Sector / industry: B2B SaaS analytics",
        },
        {
            "label": "Funding ask",
            "value": "$2.5M",
            "delta": "",
            "caption": "Use of funds: product, GTM, and hiring",
        },
        {
            "label": "Business model",
            "value": "SaaS",
            "delta": "",
            "caption": "Pricing: Not stated",
        },
        {
            "label": "Readiness",
            "value": "Medium",
            "delta": "",
            "caption": "Traction shown; retention and pricing require diligence",
        },
    ],
    "trend": [
        {"label": "Jan", "value": 12},
        {"label": "Feb", "value": 18},
        {"label": "Mar", "value": 27},
        {"label": "Apr", "value": 39},
        {"label": "May", "value": 52},
        {"label": "Jun", "value": 68},
    ],
    "share": [
        {"label": "TAM", "value": 18},
        {"label": "SAM", "value": 4.2},
        {"label": "SOM", "value": 0.35},
    ],
    "rows": [
        {
            "name": "Pricing evidence missing",
            "category": "Financial",
            "value": "Deck states SaaS model but pricing is Not stated",
            "delta": "High",
        },
        {
            "name": "Retention not stated",
            "category": "Product",
            "value": "No cohort retention or churn data found",
            "delta": "High",
        },
        {
            "name": "Crowded analytics market",
            "category": "Market",
            "value": "Competitive advantage requires diligence",
            "delta": "Medium",
        },
        {
            "name": "GTM repeatability",
            "category": "GTM",
            "value": "Pilot-to-paid conversion evidence is limited",
            "delta": "Medium",
        },
    ],
    "questions": [
        {
            "name": "What is current ARR and net revenue retention?",
            "category": "Priority",
            "value": "Confirms revenue quality and expansion potential",
            "delta": "High",
        },
        {
            "name": "What pricing tiers and gross margins are expected?",
            "category": "Priority",
            "value": "Business model is stated, pricing is Not stated",
            "delta": "High",
        },
        {
            "name": "Which competitors are displaced in paid accounts?",
            "category": "Priority",
            "value": "Tests competitive advantage claims",
            "delta": "Medium",
        },
        {
            "name": "How will the $2.5M round extend runway?",
            "category": "Priority",
            "value": "Use of funds is directional but milestones need detail",
            "delta": "Medium",
        },
    ],
    "team_signals": "Founder / team signals: enterprise analytics experience is stated; prior startup outcomes are Not stated.",
    "scope_options": [
        {"label": "Investment Snapshot", "value": "snapshot"},
        {"label": "Traction", "value": "traction"},
        {"label": "Market", "value": "market"},
        {"label": "Risks", "value": "risks"},
        {"label": "Diligence", "value": "diligence"},
        {"label": "Team", "value": "team"},
    ],
    "scope_selected": "snapshot",
}
