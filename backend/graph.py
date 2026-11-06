"""LangGraph workflow for RCA assistance."""

import json
import os
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel
from langgraph.graph import END, START, StateGraph

from prompts import (
    ANALYSIS_PROMPT,
    CHAT_PROMPT,
    EDIT_PROMPT,
    EXTRACT_PROMPT,
    INVESTIGATOR_PERSONA,
    RESPONSE_PROMPT,
)
from schemas import (
    Analysis,
    Cause,
    FormState,
    InvestigationSummary,
    RiskAssessment,
)


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class RCAState(TypedDict, total=False):
    message: str
    document_text: str
    form: dict
    intent: str
    changed: list[str]
    reply: str


class RouteDecision(BaseModel):
    intent: Literal["log", "edit", "question"]


class AnalysisResult(BaseModel):
    risk: RiskAssessment
    analysis: Analysis


def _make_model() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Set it in the project .env file.")

    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=0,
        api_key=api_key,
    )


model = _make_model()


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _merge_summary(
    current: dict,
    updates: dict,
    *,
    include_nulls: bool = False,
) -> tuple[dict, list[str]]:
    merged = dict(current)
    changed = []

    for field, value in updates.items():
        if value is None and not include_nulls:
            continue
        if merged.get(field) != value:
            merged[field] = value
            changed.append(f"summary.{field}")

    return merged, changed


def route_node(state: RCAState) -> dict:
    if state.get("document_text"):
        return {"intent": "log"}

    form = state.get("form") or {}
    summary = form.get("summary") or {}
    has_summary = any(value not in (None, "") for value in summary.values())

    if not has_summary:
        return {"intent": "log"}

    decision_model = model.with_structured_output(RouteDecision)
    decision = decision_model.invoke(
        [
            ("system", INVESTIGATOR_PERSONA),
            (
                "human",
                f"Classify the user's message as log (new incident), "
                f"edit (correct investigation data), or question "
                f"(ask for information without changing the form).\n\n"
                f"Current summary:\n{_json_text(summary)}\n\n"
                f"User message:\n{state.get('message', '')}",
            ),
        ]
    )
    return {"intent": decision.intent}


def extract_node(state: RCAState) -> dict:
    text = state.get("document_text") or state.get("message", "")
    summary_model = model.with_structured_output(InvestigationSummary)
    extracted = summary_model.invoke(
        [
            ("system", f"{INVESTIGATOR_PERSONA}\n\n{EXTRACT_PROMPT}"),
            ("human", f"Incident text:\n{text}"),
        ]
    )

    form = state.get("form") or FormState().model_dump()
    summary, changed = _merge_summary(
        form.get("summary") or {},
        extracted.model_dump(),
    )
    form["summary"] = summary
    return {"form": form, "changed": changed}


def edit_node(state: RCAState) -> dict:
    form = state.get("form") or FormState().model_dump()
    current_summary = form.get("summary") or {}

    patch_model = model.with_structured_output(InvestigationSummary)
    patch = patch_model.invoke(
        [
            ("system", f"{INVESTIGATOR_PERSONA}\n\n{EDIT_PROMPT}"),
            (
                "human",
                f"Current summary:\n{_json_text(current_summary)}\n\n"
                f"User correction:\n{state.get('message', '')}",
            ),
        ]
    )

    summary, changed = _merge_summary(
        current_summary,
        patch.model_dump(),
    )
    form["summary"] = summary
    return {"form": form, "changed": changed}


def analyze_node(state: RCAState) -> dict:
    form = state.get("form") or FormState().model_dump()
    summary = form.get("summary") or {}

    current_analysis = form.get("analysis") or {}
    existing_causes = current_analysis.get("causes") or []
    locked_causes = [
        cause
        for cause in existing_causes
        if cause.get("status") in ("confirmed", "rejected")
    ]

    analysis_model = model.with_structured_output(AnalysisResult)
    result = analysis_model.invoke(
        [
            ("system", f"{INVESTIGATOR_PERSONA}\n\n{ANALYSIS_PROMPT}"),
            (
                "human",
                f"Investigation summary:\n{_json_text(summary)}\n\n"
                f"Source text for this turn:\n"
                f"{state.get('document_text') or state.get('message', '')}\n\n"
                f"Human-confirmed or human-rejected causes to preserve exactly:\n"
                f"{_json_text(locked_causes)}",
            ),
        ]
    )

    locked_by_id = {cause["id"]: cause for cause in locked_causes}
    suggested_causes = []

    for cause in result.analysis.causes:
        if cause.id not in locked_by_id:
            suggested_causes.append(
                cause.model_copy(update={"status": "suggested"})
            )

    result.analysis.causes = [
        *suggested_causes,
        *[
            Cause.model_validate(cause)
            for cause in locked_causes
        ],
    ]

    form["risk"] = result.risk.model_dump()
    form["analysis"] = result.analysis.model_dump()
    return {"form": form}


def chat_node(state: RCAState) -> dict:
    form = state.get("form") or FormState().model_dump()
    response = model.invoke(
        [
            ("system", f"{INVESTIGATOR_PERSONA}\n\n{CHAT_PROMPT}"),
            (
                "human",
                f"Current investigation:\n{_json_text(form)}\n\n"
                f"User question:\n{state.get('message', '')}",
            ),
        ]
    )
    return {"reply": response.content}


def respond_node(state: RCAState) -> dict:
    form = state.get("form") or FormState().model_dump()
    risk = form.get("risk") or {}
    analysis = form.get("analysis") or {}
    missing_evidence = [
        item.get("item")
        for item in analysis.get("evidence", [])
        if item.get("status") == "missing"
    ]

    response = model.invoke(
        [
            ("system", f"{INVESTIGATOR_PERSONA}\n\n{RESPONSE_PROMPT}"),
            (
                "human",
                f"User message: {state.get('message', '')}\n"
                f"Changed fields: {_json_text(state.get('changed', []))}\n"
                f"Risk severity: {risk.get('severity')}\n"
                f"Missing evidence: {_json_text(missing_evidence[:3])}\n"
                f"Form:\n{_json_text(form)}",
            ),
        ]
    )
    return {"reply": response.content}


def _after_route(state: RCAState) -> str:
    intent = state.get("intent", "log")
    if intent == "question":
        return "chat"
    if intent == "edit":
        return "edit"
    return "extract"


def build_graph():
    workflow = StateGraph(RCAState)

    workflow.add_node("route", route_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("edit", edit_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("chat", chat_node)
    workflow.add_node("respond", respond_node)

    workflow.add_edge(START, "route")
    workflow.add_conditional_edges(
        "route",
        _after_route,
        {
            "extract": "extract",
            "edit": "edit",
            "chat": "chat",
        },
    )
    workflow.add_edge("extract", "analyze")
    workflow.add_edge("edit", "analyze")
    workflow.add_edge("analyze", "respond")
    workflow.add_edge("respond", END)
    workflow.add_edge("chat", END)

    return workflow.compile()


graph = build_graph()