"""Shared agent tools: pitch deck PDF text → structured data for A2UI.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CUSTOMIZATION SEAM #3 — Swap demo data
See HACKATHON.md §3 for the full recipe.

FundLens AI treats the uploaded startup pitch deck as the data source. Keep
this extractor conservative: use only information found in the PDF, write
"Not stated" for missing facts, and never fabricate traction, revenue,
valuation, customers, or funding asks.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import json
import os
import re
from typing import TypedDict

from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

# We keep the extractor model cheap; this is structured JSON work, not chat.
# Gemini 3.5 Flash via the native Google Gen AI SDK — same provider as the
# primary agents (see main.py / FROZEN.md "LLM provider").
#
# Constructed lazily (not at import time): ChatGoogleGenerativeAI validates
# the API key in its constructor and raises with no key. Building it on first
# use lets `import main` succeed with OFFLINE=1 and no key (the OFFLINE /fixed
# path never reaches these tools). Online behavior is unchanged — the client
# is built the first time a tool runs, then cached.
_EXTRACTOR: ChatGoogleGenerativeAI | None = None


def _extractor() -> ChatGoogleGenerativeAI:
    global _EXTRACTOR
    if _EXTRACTOR is None:
        _EXTRACTOR = ChatGoogleGenerativeAI(
            model=os.getenv("MODEL", "gemini-3.5-flash"),
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0,
        )
    return _EXTRACTOR


class Kpi(TypedDict):
    label: str
    value: str
    delta: str
    caption: str


class Point(TypedDict):
    label: str
    value: float


class Row(TypedDict, total=False):
    name: str
    category: str
    value: str
    delta: str


def _strip_to_json(text: str) -> str:
    """LLM output may be wrapped in ```json fences. Strip them."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


@tool
def extract_dashboard_data(pdf_text: str, document_name: str) -> str:
    """Parse a startup pitch deck PDF into the FundLens dashboard shape.

    The PDF text comes from the user's most recent chat attachment.

    Returns a JSON string with this exact shape:
      {
        "eyebrow": "INVESTMENT SNAPSHOT · <company>",
        "title": "<company name>",
        "subtitle": "one-line investment summary",
        "kpis": [{label,value,delta,caption}, x4],
        "trend": [{label,value}, x3-8],
        "share": [{label,value}, x3-5],
        "rows": [{name,category,value,delta}, x4-8],
        "questions": [{name,category,value,delta}, x4-8],
        "team_signals": "short neutral founder/team summary"
      }
    Missing deck fields must be the literal string "Not stated". Never invent
    numbers, traction, revenue, valuation, customers, or funding asks.
    """
    sys = (
        "You are a careful venture analyst and data extractor for FundLens AI. "
        "Read the pitch deck PDF text and return ONLY a JSON object with the "
        "exact shape requested. No prose, no markdown fences. Use only "
        "information found in the PDF. If information is missing, write "
        "'Not stated'. Do not infer numbers that are not present. Do not "
        "produce fake traction, revenue, valuation, customers, or funding ask. "
        "Use neutral investment language such as 'evidence suggests', "
        "'not stated', and 'requires diligence'."
    )
    user = f"""\
Document name: {document_name}

Pitch deck PDF text (truncated to first 30k chars):
\"\"\"
{pdf_text[:30000]}
\"\"\"

Extract only what the deck states. Look for:
- company name, problem, solution, product, target customer
- sector / industry, startup stage, market size, market opportunity
- business model, pricing, go-to-market, partnerships
- traction, revenue, growth, customer/user metrics
- competitors, competitive advantage
- founder/team strengths
- funding ask, use of funds
- risks, missing information, investor questions

Return JSON with this shape:
{{
  "eyebrow": "INVESTMENT SNAPSHOT · SECTOR OR STAGE",
  "title": "Company name or Not stated",
  "subtitle": "One-line summary using only stated facts; include Not stated where needed",
  "kpis": [
    {{"label": "Stage", "value": "...", "delta": "", "caption": "Sector / industry: ..."}},
    {{"label": "Funding ask", "value": "...", "delta": "", "caption": "Use of funds: ..."}},
    {{"label": "Business model", "value": "...", "delta": "", "caption": "Pricing / buyer: ..."}},
    {{"label": "Readiness", "value": "High|Medium|Low|Not stated", "delta": "", "caption": "Only score if enough evidence exists; otherwise Not stated"}}
  ],
  "trend": [{{"label": "Traction metric", "value": 0}}, ...],
  "share": [{{"label": "Market / segment", "value": 0}}, ...],
  "rows": [{{"name": "Risk", "category": "Market|Product|GTM|Financial|Team|Legal|Other", "value": "Evidence or Not stated", "delta": "High|Medium|Low|Not stated"}}, ...],
  "questions": [{{"name": "Due diligence question", "category": "Priority", "value": "Why it matters", "delta": "High|Medium|Low"}}, ...],
  "team_signals": "Founder / team strengths, or Not stated"
}}

Guidance:
- trend should represent traction signals only when numerical metrics are present. If no traction numbers exist, return one point: {{"label":"Not stated","value":0}}.
- share should represent market opportunity only when numerical market/segment values are present. If no market numbers exist, return one point: {{"label":"Not stated","value":0}}.
- rows are the Risk Register. Include missing critical information as a risk.
- questions are investor due diligence questions by priority.
Return ONLY the JSON object.
"""
    out = _extractor().invoke([("system", sys), ("user", user)])
    raw = _strip_to_json(out.content if isinstance(out.content, str) else str(out.content))
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "eyebrow": "INVESTMENT SNAPSHOT",
            "title": document_name or "Not stated",
            "subtitle": "Could not extract structured pitch deck data.",
            "kpis": [
                {"label": "Stage", "value": "Not stated", "delta": "", "caption": "Sector / industry: Not stated"},
                {"label": "Funding ask", "value": "Not stated", "delta": "", "caption": "Use of funds: Not stated"},
                {"label": "Business model", "value": "Not stated", "delta": "", "caption": "Pricing / buyer: Not stated"},
                {"label": "Readiness", "value": "Not stated", "delta": "", "caption": "Requires diligence"},
            ],
            "trend": [{"label": "Not stated", "value": 0}],
            "share": [{"label": "Not stated", "value": 0}],
            "rows": [
                {"name": "Structured extraction", "category": "Other", "value": "Not stated", "delta": "Not stated"}
            ],
            "questions": [
                {"name": "What evidence supports the investment case?", "category": "Priority", "value": "Extraction failed", "delta": "High"}
            ],
            "team_signals": "Not stated",
        }
    return json.dumps(data)


@tool
def query_pdf(pdf_text: str, question: str) -> str:
    """Answer a user question about the pitch deck and return structured data
    that the dynamic agent can then render as a UI surface.

    Returns a JSON object: { "shape_hint": "stat|trend|share|table|text",
                             "title": "...", "summary": "...",
                             "data": <shape-appropriate payload> }
    The shape_hint is advice. The agent makes the final layout decision.
    """
    sys = (
        "You are a venture analyst answering investor questions about a startup "
        "pitch deck. Return ONLY a JSON object describing the answer as "
        "structured data. No prose, no markdown fences. Use only information "
        "found in the PDF. If information is missing, write 'Not stated'. Do "
        "not infer numbers that are not present. Do not produce fake traction, "
        "revenue, valuation, customers, or funding ask. Pick the most natural "
        "shape for the answer:\n"
        "- 'stat'  → { value, delta?, caption? } for a single investment metric\n"
        "- 'trend' → [{label, value}, ...] for traction or growth over time\n"
        "- 'share' → [{label, value}, ...] for market / segment breakdowns\n"
        "- 'table' → { columns:[{key,label}], rows:[{...}] } for risks, diligence, missing info\n"
        "- 'text'  → string for partner-memo or qualitative analysis\n"
    )
    user = f"""\
Investor question: {question}

Pitch deck PDF text (truncated):
\"\"\"
{pdf_text[:30000]}
\"\"\"

Return JSON shaped like:
{{
  "shape_hint": "stat|trend|share|table|text",
  "title": "Investor-grade title",
  "summary": "Neutral summary using only deck evidence; use Not stated for missing facts",
  "data": <payload above>
}}

Useful investor analyses include:
- investment committee memo
- top investor risks
- missing deck information
- due diligence questions by priority
- traction versus market opportunity
- fundability assessment
- weakest slide from an investor perspective
- VC partner memo
"""
    out = _extractor().invoke([("system", sys), ("user", user)])
    raw = _strip_to_json(out.content if isinstance(out.content, str) else str(out.content))
    try:
        json.loads(raw)  # validate
        return raw
    except json.JSONDecodeError:
        return json.dumps(
            {
                "shape_hint": "text",
                "title": "Pitch deck analysis",
                "summary": "Could not produce structured output.",
                "data": "Not stated",
            }
        )
