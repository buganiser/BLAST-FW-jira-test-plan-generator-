# Findings — SCRUM-10 Test Plan Generator

## Research & Discoveries

### Jira REST API (Cloud)
- **Base URL**: `https://{domain}.atlassian.net/rest/api/3/`
- **Authentication**: Basic Auth with `email:api_token`
- **Get Issue**: `GET /issue/{issueIdOrKey}?fields=summary,description,acceptanceCriteria,priority,labels,components,fixVersions,assignee,reporter,created,updated,status,issuetype`
- **Add Comment**: `POST /issue/{issueIdOrKey}/comment` with body in ADF (Atlassian Document Format)

### Acceptance Criteria Location
- Jira doesn't have a native "acceptance criteria" field by default
- Common patterns:
  1. Custom field (e.g., `customfield_XXXXX`)
  2. Embedded in description (markdown/ADF) with headers like "## Acceptance Criteria"
  3. In a separate "Test Plan" or "QA" custom field
- **Action**: Fetch full description and parse for AC patterns

### IEEE 829 Test Plan Standard
- 16 sections (Identifier through Approvals)
- Key sections for automation:
  - Test Items → derived from acceptance criteria
  - Features to Test → from AC + ticket summary
  - Approach → standardized based on issue type
  - Risks → from priority, labels, components
  - Schedule → minimal (milestones only)

### Atlassian Document Format (ADF)
- Jira Cloud returns description in ADF (JSON)
- Need ADF → Markdown conversion for parsing
- Comments must be posted in ADF format

### Existing Tools/Repos (GitHub Search)
- `atlassian-api` / `jira-python` — Python Jira clients
- `jira.js` / `atlassian-jira` — Node.js clients
- `adf-transformer` — ADF ↔ Markdown conversion
- No existing "Jira ticket → IEEE 829 test plan" generators found

### Implementation Discoveries (During Build)

#### ADF Parsing
- Built custom ADF → text converter handling: doc, paragraph, text, heading, bulletList, orderedList, listItem, codeBlock, panel, hardBreak
- Supports marks: strong, em, code
- Handles nested structures recursively

#### Acceptance Criteria Extraction
- Regex patterns for common headers: "Acceptance Criteria", "AC:", "## AC", "### Acceptance"
- Falls back to full description if no explicit AC section found
- Parses numbered/bulleted items into structured list

#### Risk Mapping
- Jira Priority → Risk Level mapping:
  - Highest/High → High
  - Medium → Medium
  - Low/Lowest → Low
- Bug issue type → High risk
- Story issue type → Medium risk

#### React Frontend
- Vite + React 18 + TypeScript
- Proxy to backend API in development
- Markdown preview with basic HTML rendering
- Download generated .md files

#### FastAPI Backend
- Auto-generated OpenAPI docs at /docs
- CORS configured for localhost:3000
- Endpoints: /generate, /ticket/{key}, /download/{key}, /list, /health

## Constraints

| Constraint | Impact |
|------------|--------|
| Jira Cloud vs Server | Different API versions; assume Cloud (REST API v3) |
| Custom fields unknown | Must fetch all fields and search for AC |
| ADF parsing required | Need ADF → text/markdown conversion |
| Rate limiting | Jira Cloud: 100 req/min; add delays if batching |
| Permissions | API token needs "Browse Projects", "Add Comments" |
| Comment size limit | Jira comments ~32KB; truncate large test plans |

## Decisions

1. **Language**: Python (rich Jira ecosystem: `requests`, custom ADF parser)
2. **Config**: `.env` file for credentials (not committed)
3. **Output dir**: `test-plans/` (created if not exists)
4. **AC parsing**: Search description for headers: "Acceptance Criteria", "AC:", "## AC", "### Acceptance"
5. **Risk mapping**: Priority High→High, Medium→Medium, Low→Low; Bug→High; Story→Medium
6. **Comment format**: Post as ADF with markdown-like rendering in Jira
7. **Frontend**: React + Vite + TypeScript for fast development
8. **API**: FastAPI for automatic OpenAPI docs and validation

## Open Questions

- [ ] What is the exact Jira domain? (e.g., `company.atlassian.net`) — **RESOLVED: anub131091.atlassian.net**
- [ ] Is there a custom field for acceptance criteria? (Need field ID) — **RESOLVED: Parsing from description**
- [ ] Should we support Jira Server/DC too? (Different auth/API) — **Deferred: Cloud only for now**
- [ ] Any specific test plan sections required beyond IEEE 829? — **No, standard IEEE 829**

## Test Results ✅

- [x] Jira connection test (authenticated as Anubhava Srivastava)
- [x] Fetch ticket SCRUM-10 (Bug: Hardcoded secret key in app.py)
- [x] Acceptance criteria parsed from description
- [x] Test plan generated with 1 test item (High risk)
- [x] Markdown file saved to test-plans/TP-SCRUM-10.md
- [x] JSON file saved to test-plans/TP-SCRUM-10.json
- [x] Jira comment posted successfully to SCRUM-10
- [x] FastAPI backend server starts on port 8000
- [x] Health endpoint: GET /api/health
- [x] Ticket info endpoint: GET /api/ticket/SCRUM-10
- [x] Generate endpoint: POST /api/generate (with post_to_jira=false, save_json=true)
- [x] Download endpoint: GET /api/download/SCRUM-10
- [x] Frontend builds successfully (npm run build)
- [x] All 15 IEEE 829 sections populated in output
- [x] CLI: `python main.py SCRUM-10 --no-post --json` — Local generation only
- [x] CLI: `python main.py SCRUM-10 --json` — Local + Jira comment