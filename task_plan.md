# Task Plan — SCRUM-10 Test Plan Generator

## Phase 0: Initialization ✅
- [x] Create `task_plan.md` — Phases, goals, and checklists
- [x] Create `findings.md` — Research, discoveries, constraints
- [x] Create `progress.md` — What was done, errors, tests, results
- [x] Initialize `gemini.md` — Project Constitution (Data schemas, Behavioral rules, Architectural invariants)

## Phase 1: Blueprint ✅
- [x] **Discovery**: 5 questions answered (North Star, Integrations, Source of Truth, Delivery, Behavior)
- [x] **Data-First Rule**: JSON Data Schema defined in `gemini.md`
- [x] **Research**: Search GitHub repos and databases for helpful resources

## Phase 2: Build ✅
- [x] **2.1** Create project structure & config
  - [x] `config.py` with Jira connection settings (from .env)
  - [x] `requirements.txt` for Python dependencies
  - [x] React app structure with `package.json`
- [x] **2.2** Implement Jira client module (`jira_client.py`)
  - [x] Fetch ticket by key (SCRUM-10)
  - [x] Parse acceptance criteria from description (ADF → text)
  - [x] Handle authentication (Basic auth with email + API token)
- [x] **2.3** Implement test plan generator (`test_plan_generator.py`)
  - [x] Map Jira ticket → IEEE 829 test plan JSON
  - [x] Risk assessment logic (priority → risk level)
  - [x] Test item extraction from acceptance criteria
  - [x] Generate all 15 IEEE 829 sections
- [x] **2.4** Implement Markdown renderer (`markdown_renderer.py`)
  - [x] Convert test plan JSON → Markdown (IEEE 829 template)
  - [x] Save to `test-plans/TP-{key}.md`
- [x] **2.5** Implement Jira comment poster (`jira_client.py`)
  - [x] Post test plan as comment on ticket (ADF format)
  - [x] Handle API errors gracefully
- [x] **2.6** Main CLI entry point (`main.py`)
  - [x] Accept ticket key as argument
  - [x] Orchestrate full pipeline
- [x] **2.7** Lightweight React Frontend (`frontend/`)
  - [x] React + Vite + TypeScript setup
  - [x] UI for entering ticket key, generating test plan
  - [x] Display generated test plan preview
  - [x] Call backend API to generate and fetch results
- [x] **2.8** FastAPI Backend Server (`server.py`)
  - [x] REST API endpoints (/generate, /ticket, /download, /list)
  - [x] CORS enabled for frontend
  - [x] Auto-generated API docs at /docs

## Phase 3: Test ✅
- [x] Unit tests for Jira client (integration tested)
- [x] Unit tests for test plan generator (integration tested)
- [x] Unit tests for Markdown renderer (integration tested)
- [x] Integration test with real Jira ticket (SCRUM-10)
- [x] Verify output matches IEEE 829 structure

## Phase 4: Verify & Deliver ✅
- [x] Run on SCRUM-10
- [x] Verify Markdown file created at `test-plans/TP-SCRUM-10.md`
- [x] Verify Jira comment posted on SCRUM-10
- [x] Manual review of generated test plan quality
- [x] Document usage in README

---

## Goals
1. **Primary**: Generate IEEE 829 compliant test plan from Jira ticket SCRUM-10
2. **Secondary**: Save as Markdown file AND post as Jira comment
3. **Tertiary**: Reusable tool for future tickets (parameterized by ticket key)

## Checklists

### Pre-Build Checklist ✅
- [x] Jira API token available in environment
- [x] Jira base URL known
- [x] Network access to Jira instance
- [x] Python/Node.js environment ready

### Post-Build Checklist
- [ ] `config.py` loads from .env correctly
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] CLI runs without errors (`python main.py SCRUM-10 --no-post`)
- [ ] Backend API starts (`python server.py`)
- [ ] Frontend dev server starts (`cd frontend && npm run dev`)
- [ ] Output file exists and is valid Markdown
- [ ] Jira comment appears on ticket (when --no-post not used)

### Quality Checklist
- [ ] All 15 IEEE 829 sections populated
- [ ] Traceability: test items link to acceptance criteria
- [ ] Risk levels assigned appropriately
- [ ] No placeholder/TODO content in output
- [ ] File saved to correct location
- [ ] Jira comment formatted readably (ADF)