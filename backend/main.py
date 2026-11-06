"""FastAPI application and RCA endpoints."""

from collections.abc import Generator
from typing import Literal

from fastapi import Depends, FastAPI, File, Form as FormField, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from db import (
    AuditLog,
    CapaRecord,
    CauseRecord,
    EvidenceRecord,
    Investigation,
    SessionLocal,
    WhyRecord,
    create_tables,
)
from graph import graph
from pdf_utils import extract_document_text
from schemas import FormState


app = FastAPI(title="AIVOA RCA Co-Pilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    form: FormState = Field(default_factory=FormState)


class ChatResponse(BaseModel):
    reply: str
    form: FormState
    changed: list[str]


class SaveInvestigationRequest(BaseModel):
    form: FormState
    no_confirmed_root_cause: bool = False
    actor: str = "user"


class SaveInvestigationResponse(BaseModel):
    id: int
    status: str
    form: FormState


class CauseReviewRequest(BaseModel):
    status: Literal["confirmed", "rejected"]
    actor: str = "user"


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def initialize_database() -> None:
    create_tables()


def _invoke_graph(
    message: str,
    form: FormState,
    document_text: str = "",
) -> ChatResponse:
    result = graph.invoke(
        {
            "message": message,
            "document_text": document_text,
            "form": form.model_dump(),
            "changed": [],
        }
    )
    return ChatResponse(
        reply=result["reply"],
        form=FormState.model_validate(result["form"]),
        changed=result.get("changed", []),
    )


def _form_from_investigation(investigation: Investigation) -> FormState:
    analysis = {
        "whys": [
            {
                "level": why.level,
                "question": why.question,
                "answer": why.answer,
                "evidence_needed": why.evidence_needed,
            }
            for why in investigation.whys
        ],
        "causes": [
            {
                "id": cause.cause_id,
                "text": cause.text,
                "category": cause.category,
                "is_probable_root": cause.is_probable_root,
                "confidence": cause.confidence,
                "source_quote": cause.source_quote,
                "status": cause.status,
            }
            for cause in investigation.causes
        ],
        "evidence": [
            {
                "item": item.item,
                "status": item.status,
                "why_needed": item.why_needed,
                "related_cause_id": item.related_cause_id,
            }
            for item in investigation.evidence_items
        ],
        "capas": [
            {
                "id": capa.capa_id,
                "type": capa.type,
                "action": capa.action,
                "rationale": capa.rationale,
                "effectiveness_check": capa.effectiveness_check,
                "linked_cause_id": capa.linked_cause_id,
            }
            for capa in investigation.capas
        ],
    }
    return FormState(
        summary=investigation.summary,
        risk=investigation.risk,
        analysis=analysis,
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return _invoke_graph(request.message, request.form)


@app.post("/api/chat/upload", response_model=ChatResponse)
async def upload_document(
    file: UploadFile = File(...),
    message: str = FormField(""),
    form: str = FormField(...),
) -> ChatResponse:
    try:
        form_state = FormState.model_validate_json(form)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid form data: {exc}",
        ) from exc

    content = await file.read()
    try:
        document_text = extract_document_text(file.filename or "", content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return await run_in_threadpool(
        _invoke_graph,
        message or "Analyze the uploaded investigation document.",
        form_state,
        document_text,
    )


@app.post("/api/investigations", response_model=SaveInvestigationResponse)
def save_investigation(
    request: SaveInvestigationRequest,
    db: Session = Depends(get_db),
) -> SaveInvestigationResponse:
    form_data = request.form.model_dump()
    causes = form_data["analysis"]["causes"]
    has_confirmed_cause = any(
        cause["status"] == "confirmed"
        for cause in causes
    )
    if not has_confirmed_cause and not request.no_confirmed_root_cause:
        raise HTTPException(
            status_code=400,
            detail=(
                "Confirm at least one cause or set "
                "no_confirmed_root_cause to true before saving."
            ),
        )

    investigation = Investigation(
        status="open",
        summary=form_data["summary"],
        risk=form_data["risk"],
    )
    db.add(investigation)
    db.flush()

    for cause in causes:
        db.add(
            CauseRecord(
                investigation_id=investigation.id,
                cause_id=cause["id"],
                text=cause["text"],
                category=cause["category"],
                is_probable_root=cause["is_probable_root"],
                confidence=cause["confidence"],
                source_quote=cause["source_quote"],
                status=cause["status"],
            )
        )

    for why in form_data["analysis"]["whys"]:
        db.add(WhyRecord(investigation_id=investigation.id, **why))

    for item in form_data["analysis"]["evidence"]:
        db.add(EvidenceRecord(investigation_id=investigation.id, **item))

    for capa in form_data["analysis"]["capas"]:
        db.add(
            CapaRecord(
                investigation_id=investigation.id,
                capa_id=capa["id"],
                type=capa["type"],
                action=capa["action"],
                rationale=capa["rationale"],
                effectiveness_check=capa["effectiveness_check"],
                linked_cause_id=capa["linked_cause_id"],
            )
        )

    db.add(
        AuditLog(
            investigation_id=investigation.id,
            actor=request.actor,
            action="investigation_saved",
            after=form_data,
        )
    )
    db.commit()
    db.refresh(investigation)

    return SaveInvestigationResponse(
        id=investigation.id,
        status=investigation.status,
        form=request.form,
    )


@app.get(
    "/api/investigations/{investigation_id}",
    response_model=SaveInvestigationResponse,
)
def get_investigation(
    investigation_id: int,
    db: Session = Depends(get_db),
) -> SaveInvestigationResponse:
    investigation = db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    return SaveInvestigationResponse(
        id=investigation.id,
        status=investigation.status,
        form=_form_from_investigation(investigation),
    )


@app.patch("/api/investigations/{investigation_id}/causes/{cause_id}")
def review_cause(
    investigation_id: int,
    cause_id: str,
    request: CauseReviewRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    investigation = db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    cause = (
        db.query(CauseRecord)
        .filter_by(
            investigation_id=investigation_id,
            cause_id=cause_id,
        )
        .first()
    )
    if cause is None:
        raise HTTPException(status_code=404, detail="Cause not found.")

    previous_status = cause.status
    cause.status = request.status
    db.add(
        AuditLog(
            investigation_id=investigation_id,
            actor=request.actor,
            action=f"cause_{request.status}",
            before={"cause_id": cause_id, "status": previous_status},
            after={"cause_id": cause_id, "status": request.status},
        )
    )
    db.commit()

    return {"cause_id": cause_id, "status": cause.status}