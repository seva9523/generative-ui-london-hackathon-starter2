"""Fixed-schema dashboard agent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CUSTOMIZATION SEAM #5 — Swap the agent flow (fixed-schema dashboard)
See HACKATHON.md §5 for the full recipe. For a different fixed dashboard,
rewrite the layout JSON at agent/src/a2ui/schemas/dashboard.json and the
`render_dashboard` tool's typed inputs; reword the system prompt for your
domain. The dynamic Q&A flow lives in dynamic_agent.py.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The user attaches a startup pitch deck PDF in the chat. The agent reads the
PDF text (inlined into the user message by InlineDocumentsMiddleware) and
calls `render_dashboard` with conservative investment-analysis data. The
dashboard surface behaves like an investment committee memo and preserves
missing facts as "Not stated".
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

from copilotkit import CopilotKitMiddleware, a2ui
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver

from src.catalog import CATALOG_ID, CATALOG_PROMPT

SCHEMA_DIR = Path(__file__).parent / "a2ui" / "schemas"
DASHBOARD_SCHEMA = a2ui.load_schema(SCHEMA_DIR / "dashboard.json")
SURFACE = "pdf-dashboard"


# NOTE (Gemini typed-array fix): every list parameter on render_dashboard
# below is typed as `list[<TypedDict>]`, NOT `list[dict]`. Gemini's
# function-declaration validator rejects untyped arrays with
# "parameters.properties[X].items: missing field". A TypedDict compiles to a
# concrete object schema, so these arrays carry the `items` Gemini requires.
# Keep them typed — do not loosen to `list[dict]`.
class Kpi(TypedDict):
    label: str
    value: str
    delta: str
    caption: str


class Point(TypedDict):
    label: str
    value: float


class Row(TypedDict):
    name: str
    category: str
    value: str
    delta: str


class ScopeOption(TypedDict):
    label: str
    value: str


@tool
def render_dashboard(
    eyebrow: str,
    title: str,
    subtitle: str,
    kpis: list[Kpi],
    trend: list[Point],
    share: list[Point],
    rows: list[Row],
    questions: list[Row],
    team_signals: str,
    scope_options: list[ScopeOption],
    scope_selected: str,
) -> str:
    """Render the FundLens investment committee dashboard for a pitch deck.

    Pass data INLINE. Call ONCE per turn. Use only facts stated in the deck.
    Missing values must be the exact string "Not stated". Never invent
    traction, revenue, valuation, customers, or funding ask.

    Required shapes:
      - kpis: EXACTLY 4 cards:
          1. Stage
          2. Funding ask
          3. Business model
          4. Readiness
        Use short `value` strings and put context/evidence in `caption`.
        Use `delta` only for explicitly stated growth/change; otherwise "".

      - trend: 3–8 traction/revenue/growth points. If no numerical traction
        appears, pass [{label:"Not stated", value:0}].
      - share: 3–5 market-opportunity or segment points. If no market numbers
        appear, pass [{label:"Not stated", value:0}].
      - rows: 4–8 Risk Register rows. Each row uses
        {name, category, value, delta}, where value is the evidence and delta
        is High|Medium|Low|Not stated.
      - questions: 4–8 Due Diligence Questions rows using the same Row shape;
        `name` is the question, `category` is priority, `value` is why it
        matters, and `delta` is High|Medium|Low.
      - team_signals: Founder / team strengths in neutral language, or
        "Not stated".
      - scope_options: 3–6 chips tailored to pitch-deck analysis, e.g.
        Investment Snapshot, Traction, Market, Risks, Diligence, Team.
      - scope_selected: the active chip value.
    """
    payload = {
        "eyebrow": eyebrow,
        "title": title,
        "subtitle": subtitle,
        "kpis": kpis,
        "trend": trend,
        "share": share,
        "rows": rows,
        "questions": questions,
        "team_signals": team_signals,
        "scope": {"options": scope_options, "selected": scope_selected},
    }
    return a2ui.render(
        operations=[
            a2ui.create_surface(SURFACE, catalog_id=CATALOG_ID),
            a2ui.update_components(SURFACE, DASHBOARD_SCHEMA),
            a2ui.update_data_model(SURFACE, payload),
        ]
    )


SYSTEM_PROMPT = f"""\
You are FundLens AI, a premium venture-analysis copilot. You build and
maintain a live investment committee dashboard from a user's startup pitch
deck PDF.

## Non-negotiable evidence rules

- Use ONLY information found in the deck.
- If a field is missing, write exactly: Not stated.
- Do not infer numbers that are not present.
- Do not produce fake traction, revenue, valuation, customers, partnerships,
  funding ask, or use-of-funds details.
- Use neutral investment language: "evidence suggests", "not stated",
  "requires diligence".

## How a turn works

The user may do three things on any turn:
  A) Attach a startup pitch deck PDF + chat (initial render).
  B) Send a chat message ("create an investment committee memo",
     "show top investor risks", "what is missing from this deck?").
  C) Click a scope chip on the dashboard. The runtime delivers this as a
     tool result `log_a2ui_event` with content like:
        User performed action "select_chip" on surface "pdf-dashboard".
        Context: {{"value": "risks", "label": "Scope"}}

In every case, decide whether to re-render the dashboard, answer briefly in
chat, or both.

## The render contract

When you render, call `render_dashboard(...)` ONCE with structured data for
these sections:
  1. Investment Snapshot
  2. Traction Signals
  3. Market Opportunity
  4. Risk Register
  5. Due Diligence Questions
  6. Founder / Team Signals

Extract and display where stated: company name, one-line summary, sector /
industry, startup stage, funding ask, business model, key traction metrics,
revenue / growth signals, market opportunity, competitive advantage, founder
/ team strengths, main investor risks, due diligence questions, and an
overall investment readiness score ONLY if enough evidence exists.
Otherwise use Not stated.

Suggested scope chips: Investment Snapshot, Traction, Market, Risks,
Diligence, Team. Tailor labels to the deck when useful. After a chip click,
set `scope_selected` to the clicked value and re-render the same surface.

## Hard rules

- Render the dashboard whenever the user attaches a pitch deck, asks to
  render/re-render, asks for an IC memo/dashboard, or clicks a chip.
- Call `render_dashboard` AT MOST ONCE per turn. Never twice.
- Use ONLY numbers that actually appear in the deck.
- Missing data is itself a diligence finding; show it as Not stated.
- If the user asks for a brand-new visualization not covered by the fixed
  schema (for example a custom matrix), direct them to Dynamic Analysis.

## Chat tone

Be brief, investor-grade, and neutral. After the first render, suggest one
or two follow-ups such as "Show top investor risks" or "Prioritize due
diligence questions".

{CATALOG_PROMPT}
"""


# Gemini 3.5 Flash via the native Google Gen AI SDK — same provider as the
# dynamic agent and the PDF extractor (see FROZEN.md "LLM provider"). The
# native SDK replays Gemini's thought_signature across tool turns, which the
# OpenAI-compat path does not.
#
# Constructed lazily (not at import time): ChatGoogleGenerativeAI validates
# the API key in its constructor and raises with no key. Building it lazily
# lets `import main` succeed with OFFLINE=1 and no key (the offline branch of
# build_fixed_agent never touches the live model). Online behavior is
# unchanged — the client is built on the first build_fixed_agent() call.
def _build_model() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.getenv("MODEL", "gemini-3.5-flash"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )


def build_fixed_agent():
    if os.getenv("OFFLINE") == "1":
        # CUSTOMIZATION SEAM (offline): no Gemini call, no API key. A
        # deterministic stub chat model drives the REAL create_agent ReAct
        # loop + the REAL render_dashboard tool, so the emitted A2UI envelope
        # is byte-for-byte the production shape (createSurface +
        # updateComponents + updateDataModel wrapped in a2ui_operations).
        from src.offline_fixed import build_offline_fixed_agent

        return build_offline_fixed_agent(render_dashboard, SYSTEM_PROMPT)

    return create_agent(
        model=_build_model(),
        tools=[render_dashboard],
        # CopilotKitMiddleware forwards frontend tools + agent context (e.g.
        # useAgentContext payloads) to the LLM.
        middleware=[CopilotKitMiddleware()],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )


graph = build_fixed_agent()
