# HANDOFF.md: AIVOA RCA Co-Pilot (full project brief)

Read this entire file before doing anything. Then read Section 12 (current state)
and continue from there. Do NOT restart the design or change the tech stack.

---

## 1. The task (AIVOA.AI "AI Product Engineer Challenge", 48-hour deadline)

Build a working AI-powered **Root Cause Analysis (RCA) module** for a pharmaceutical
manufacturer producing **Active Pharmaceutical Ingredients (API)**.

Real-world quality workflow: **Deviation Identification -> Root Cause Analysis -> CAPA**
(Corrective and Preventive Actions). A deviation is logged elsewhere (e.g. an assay
out of specification on an API batch). The RCA module investigates WHY it happened using
evidence and methods like 5 Whys / fishbone, then recommends CAPA.

### CRITICAL: what NOT to build
The reference demo video is for a **Customer Complaint** module. DO NOT build a Customer
Complaint, Deviation, or Change Control module. The video is used ONLY to copy the
**interaction pattern**. The form on the left must be an RCA INVESTIGATION form, not an
incident-logging form. Deviation details are only INPUT CONTEXT (pasted text, email, PDF).

### What the evaluators want to see
- Accept an incident/investigation document (PDF), pasted text, or email.
- AI extracts info and populates the RCA form.
- Supports 5 Whys and/or fishbone analysis.
- Identifies potential root causes and contributing factors.
- Highlights MISSING evidence/information.
- CAPA recommendations with short explanations.
- User can review/edit AI output before saving.
- AI causes are SUGGESTIONS unless supported by evidence and confirmed by a qualified person.
- Ownership: sensible product decisions, complete working flow.

---

## 2. Interaction pattern (from the reference video transcript)

Split screen:
- LEFT: the RCA investigation form.
- RIGHT: an "AI co-pilot" chat assistant.
- **The user must NOT fill the form manually.** All fills and updates happen through the
  AI chat. Form fields are read-only.

Three mandatory AI tools (mapped from the video to RCA):

1. **LOG tool.** User describes the incident in chat (e.g. "Assay OOS 94.1% on Metformin
   HCl API batch MFH260712A after drying in DRY-03, temperature excursion logged").
   AI extracts details, fills the form summary, AND uses its own reasoning to fill the
   analysis sections: risk assessment, 5 Whys, fishbone causes, missing evidence, CAPA.
2. **EDIT tool.** Natural-language correction (e.g. "Sorry, the batch number is
   CHG260712A and the affected quantity is 50 kg in 2 HDPE drums"). AI updates ONLY the
   named fields, PRESERVES everything else, and refreshes the dependent analysis sections.
3. **DOCUMENT EXTRACTION tool.** User uploads a PDF / email / text file. AI extracts
   details, populates the form, runs the analysis. Chat edits must still work afterwards.

The brief also says users must be able to review/edit AI output before saving. Our
resolution (a product decision): content edits happen ONLY via chat (edit tool). The form
has REVIEW ACTIONS only, not data entry: Confirm / Reject on each cause, a "Why?" view
showing the source quote, and a Save button.

---

## 3. Mandatory tech stack (do not change)

| Layer | Tech |
|---|---|
| Frontend | React + Redux (Redux Toolkit) |
| Backend | Python + FastAPI |
| AI | LangGraph + Groq (via langchain-groq) |
| Database | PostgreSQL (running in Docker) |

**Groq model: `openai/gpt-oss-120b`** (set via `GROQ_MODEL` in .env).
- `llama-3.3-70b-versatile` was RETIRED by Groq on 16 Aug 2026 (the user got a 404
  model_not_found). Do not use it.
- Fallback: `qwen/qwen3.8-27b` (visible in the user's account model list).
- Other models on the user's account: openai/gpt-oss-20b, openai/gpt-oss-safeguard-20b.
- Why gpt-oss-120b first: our agent depends on structured JSON output matching Pydantic
  schemas; Qwen models may only offer JSON object mode, not strict JSON schema mode.
- If `with_structured_output` errors on schema/strict mode, try
  `with_structured_output(Schema, method="json_schema")` or `method="json_mode"`
  (with the schema described in the prompt), or fall back to the Qwen model.

---

## 4. The user's environment (Windows)

- OS: Windows 10/11, PowerShell, VS Code. Project root: `C:\AIVOA`.
- System Python is 3.14.6 (too new for some packages). We use **Python 3.12.10** in a
  venv: `C:\AIVOA\backend\venv`. Always activate with `.\venv\Scripts\Activate.ps1`
  (prompt shows `(venv)`). If blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Node v24.18.1, npm 11.16.0, Docker 29.6.2 (Docker Desktop must be running), git 2.55.
- Postgres runs in Docker: container name `aivoa-db-1`, port 5432,
  user `rca`, password `rca`, database `rcadb`. Verified accepting connections.
  Start with `docker compose up -d` from `C:\AIVOA`.
- The user has unrelated old containers (loan-risk-*, hadoop namenode/datanode). Ignore them;
  they do not use port 5432.
- Python packages installed in the venv (requirements.txt): fastapi, uvicorn[standard],
  python-multipart, pydantic>=2, langgraph, langchain-groq, pypdf, sqlalchemy,
  psycopg2-binary, python-dotenv. pip is 26.3.
- `.env` (gitignored, at `C:\AIVOA\.env`) contains:
  `GROQ_API_KEY=gsk_...` (real key, NEVER print or commit it),
  `GROQ_MODEL=openai/gpt-oss-120b`,
  `DATABASE_URL=postgresql+psycopg2://rca:rca@localhost:5432/rcadb`.
  `.env.example` has the same keys with the API key blank.
- Load env in backend scripts with `load_dotenv("../.env")` when run from `backend/`.

### How to work with this user
- One step at a time. Give exact commands and file contents; wait for confirmation/output.
- The user is learning; explain briefly why. They must be able to explain the code in a
  video, so keep code clear and commented, not overly clever.
- Windows/PowerShell syntax for all commands. VS Code for editing.
- Files starting with a dot can be awkward on Windows; remind about hidden extensions.
- Never ask the user to paste secrets into chat.

---

## 5. Project structure

```
C:\AIVOA
├── HANDOFF.md
├── docker-compose.yml        # postgres:16
├── .gitignore                # .env, venv/, node_modules/, __pycache__/, samples/, *.mp4, *.pdf
├── .env / .env.example
├── backend/
│   ├── venv/
│   ├── requirements.txt
│   ├── main.py               # FastAPI app + endpoints
│   ├── schemas.py            # Pydantic RCA form schema (source of truth)
│   ├── graph.py              # LangGraph agent
│   ├── prompts.py            # all LLM prompts
│   ├── pdf_utils.py          # PDF/text extraction
│   ├── db.py                 # SQLAlchemy engine + models
│   └── tests/                # script tests with sample incidents
├── frontend/src/
│   ├── store/                # Redux slices: formSlice, chatSlice
│   ├── components/CoPilot/   # chat panel, input, upload, suggested prompts
│   ├── components/Form/      # read-only RCA form sections
│   └── api/                  # API client
└── samples/                  # fictional deviation PDF/email (PRIVATE, gitignored)
```

---

## 6. RCA form schema (backend/schemas.py: the foundation)

FormState = { summary, risk, analysis }

- **summary (InvestigationSummary)**: deviation_id, title, product_name, batch_number,
  process_step, equipment_id, date_detected, reported_by, problem_statement,
  affected_quantity, immediate_containment. All Optional (unknown => null).
- **risk (RiskAssessment)**: severity (Critical|Major|Minor), batch_impact,
  recommended_next_action, regulatory_reportability, rationale.
- **analysis**:
  - whys: [ {level, question, answer, evidence_needed} ] (max 5)
  - causes: [ {id, text, category (Man|Machine|Method|Material|Measurement|Environment),
    is_probable_root, confidence (low|medium|high), source_quote, status
    (suggested|confirmed|rejected)} ]
  - evidence: [ {item, status (available|missing), why_needed, related_cause_id} ]
  - capas: [ {id, type (Corrective|Preventive), action, rationale,
    effectiveness_check, linked_cause_id} ]

`status` on causes changes ONLY through human Confirm/Reject, never by the AI.

---

## 7. LangGraph agent design (backend/graph.py)

State: { message, document_text, form (dict), intent, changed (list of field paths), reply }

Flow: `router -> (extract | edit | chat) -> analyze -> respond`

- **router**: if document_text present => "extract". Else if summary is empty => "log".
  Else classify message as new incident / edit / question (small structured LLM call).
- **extract/log node**: LLM structured output -> InvestigationSummary from text/document.
  Merge into form.summary; record changed fields.
- **edit node (PATCH semantics)**: give the LLM the current summary + the user's correction;
  it must return ONLY the fields being corrected, all others null. Merge only non-null
  values. This is how "preserve all other information" is guaranteed.
- **analyze node**: given the summary, produce risk + whys + causes + evidence + capas in
  one structured call. Causes already confirmed/rejected by a human are LOCKED: pass them
  in, keep them unchanged, never regenerate over them. Assign stable ids (c1, c2.., k1..).
- **respond node**: 2-3 sentence chat reply: what changed, severity, top missing evidence,
  reminder that causes are suggestions pending QA confirmation.
- Optional: "chat" intent answers questions without modifying the form.

### Prompt rules (put in prompts.py)
- Persona: GMP quality investigator for an API manufacturer (ICH Q7, ICH Q9/Q10, 21 CFR 211.192).
- Use ONLY facts in the provided text. Unknown => null / "Not stated". Never invent
  batch numbers, dates, names.
- Never present a hypothesis as a confirmed cause. Mark confidence honestly.
- Every cause gets a source_quote from the input when one exists, otherwise null
  (and confidence stays low).
- Always list missing evidence (batch manufacturing record, equipment logs/calibration,
  operator training records, raw material CoA, environmental monitoring, method
  validation/analyst records, etc.), linked to the cause it would confirm or rule out.
- CAPA: corrective (fix this event) vs preventive (stop recurrence), with rationale and an
  effectiveness check each.

---

## 8. API endpoints (backend/main.py)

- `POST /api/chat` body {message, form} -> {reply, form, changed}
- `POST /api/chat/upload` multipart (file, message, form JSON string) -> {reply, form, changed}
  (PDF text via pypdf in pdf_utils.py; .txt/.eml decoded as text; if a PDF yields no text,
  optional OCR fallback with pytesseract)
- `POST /api/investigations` save (investigation + causes + whys + evidence + capas + audit_log)
- `GET /api/investigations/{id}` load
- `PATCH /api/investigations/{id}/causes/{cause_id}` confirm/reject (writes audit_log with
  actor + timestamp)
- CORS enabled for the React dev server (http://localhost:5173).
- Run: `uvicorn main:app --reload` from `backend/`.

The frontend sends the full current `form` with each chat call; the backend returns the
full updated `form` plus `changed` (list of field paths) for highlighting.

---

## 9. Database (PostgreSQL via SQLAlchemy, backend/db.py)

Tables: investigations(id, status, summary jsonb, risk jsonb, created_at, updated_at),
causes, whys, evidence_items, capas, audit_log(id, investigation_id, actor, action,
before jsonb, after jsonb, ts). Create tables on startup (create_all) for speed.
Log: every chat-driven change, every confirm/reject, and the save.

---

## 10. Frontend design (React + Redux Toolkit, Vite)

- Layout: left 60% form, right 40% co-pilot chat.
- Redux: `formSlice` {summary, risk, analysis, highlighted: []}, `chatSlice` {messages, loading}.
- `api/rca.js`: sendMessage(message, form), uploadDoc(file, form).
- On response: dispatch setForm(form) and setHighlighted(changed); highlighted fields
  flash for ~2 seconds. Chat shows the AI reply.
- Form sections (ALL read-only): Investigation Summary | Risk Assessment | 5 Whys |
  Fishbone (6 columns: Man, Machine, Method, Material, Measurement, Environment) |
  Causes list (confidence badge, probable-root marker, source quote "Why?", Confirm/Reject
  buttons) | Evidence (available vs missing) | CAPA table (Corrective/Preventive).
- Banner on Causes: "AI suggestions, not confirmed root causes."
- Note on form: "Use the co-pilot to update this form."
- Co-pilot: message list, text input, paperclip upload, 3 suggested-prompt chips.
- Save bar: Save is blocked until at least one cause is confirmed OR the user ticks
  "No confirmed root cause yet". Saving calls POST /api/investigations.

---

## 11. Build order and demo plan

Steps:
1. [x] Requirements verified; project scaffolded; Postgres running; venv + packages installed.
2. [x] Groq connection verified with `openai/gpt-oss-120b`.
3. [ ] schemas.py written; test structured output with a sample incident.
4. [ ] graph.py: extract, edit, analyze, respond; test via script with 3-4 sample incidents
       (log, edit with patch semantics, locked causes preserved).
5. [ ] pdf_utils.py + FastAPI endpoints (/chat, /chat/upload); test with curl/Swagger (/docs).
6. [ ] db.py + save/load/confirm-reject + audit log.
7. [ ] React + Redux UI: layout, read-only form, chat, upload, highlight-on-change.
8. [ ] Sample test PDF/email (fictional: Metformin HCl API, IP/BP grade, batch MFH260712A,
       assay OOS 94.1%, dryer DRY-03 temperature excursion, missing calibration record).
9. [ ] Prompt tuning: no invented facts, honest confidence, good missing-evidence list.
10. [ ] Video 1 (product demo, 5-8 min) and Video 2 (code walkthrough, 5-10 min).

Demo script (Video 1): show empty read-only form -> LOG via chat (form + analysis fill) ->
EDIT via chat ("batch is CHG260712A, qty 50 kg in 2 HDPE drums": highlight changed fields,
rest unchanged) -> upload sample PDF (extraction + analysis) -> edit again by chat ->
confirm one cause, reject one, review missing evidence -> Save -> reload and show persisted
record + audit trail.

Code walkthrough (Video 2): frontend structure -> API endpoints -> PDF extraction ->
LangGraph nodes + Groq structured output -> how the response populates the form via Redux ->
DB save + audit log.

---

## 12. Current state (UPDATE EVERY SESSION)

Done: environment, scaffold, Postgres, venv + packages, Groq connection test passed,
schemas.py content designed (see Section 6). Temporary test files (test_groq.py,
list_models.py) were deleted on purpose.
Next step: write/verify backend/schemas.py, run a structured-output test with a sample
incident (extract InvestigationSummary; unknown fields must be null), then build graph.py.
Files that exist but may still be empty: db.py, graph.py, main.py, pdf_utils.py, prompts.py.

---

## 13. Rules and gotchas

- NEVER upload the project, source code, demo videos, assignment files, screenshots, or
  sample documents to GitHub or any public repo. Keep `samples/` gitignored.
- Never expose or log the GROQ_API_KEY.
- Do not build Customer Complaint / Deviation / Change Control modules.
- AI causes are suggestions. Only humans confirm. Re-analysis must not overwrite
  confirmed/rejected causes.
- Groq models get retired; keep the model name in .env (`GROQ_MODEL`), never hard-code it.
- Deliverables: working app, Video 1 (demo), Video 2 (code walkthrough). Submission form:
  https://forms.gle/8Kfx62tHv6oMZRdD7

---

## 14. Prompt to give a new AI

"I'm building the project described in HANDOFF.md. Read it fully, then continue from
Section 12. Do not change the tech stack or restart the design. Work one step at a time
with exact Windows PowerShell commands and complete file contents, and wait for my output
before moving on. Here are my current files: [paste the relevant ones]."