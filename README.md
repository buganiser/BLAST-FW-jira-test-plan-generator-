# Jira Test Plan Generator

Generate IEEE 829 compliant test plans from Jira tickets automatically. Features a Python backend with FastAPI and a React + TypeScript frontend.

## Features

- 🎯 **IEEE 829 Compliant** - Full 15-section test plan structure
- 🔄 **Jira Integration** - Fetch tickets, parse acceptance criteria (ADF), post comments
- 🌐 **React Frontend** - Modern UI for generating and previewing test plans
- 📄 **Markdown Output** - Save test plans as `.md` files
- 📦 **JSON Export** - Structured data for CI/CD integration
- ⚡ **FastAPI Backend** - REST API with auto-generated docs

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend │────▶│   Jira Cloud    │
│   (Port 3000)   │     │   (Port 8000)    │     │   REST API v3   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Test Plan Gen   │
                        │  + Markdown      │
                        └──────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Jira Cloud account with API token

### Configuration

1. Copy `.env.example` to `.env` and fill in your Jira credentials:
```env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=SCRUM
```

### Run Everything (Windows)

```cmd
start.bat
```

### Run Everything (Linux/macOS)

```bash
chmod +x start.sh
./start.sh
```

### Manual Start

**Backend:**
```bash
pip install -r requirements.txt
python server.py
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:3000
```

## Usage

### Via Web UI
1. Open http://localhost:3000
2. Enter Jira ticket key (e.g., `SCRUM-10`)
3. Click "Generate Test Plan"
4. Preview or download the Markdown file

### Via CLI
```bash
python main.py SCRUM-10              # Generate + post to Jira
python main.py SCRUM-10 --no-post    # Generate only (local file)
python main.py SCRUM-10 --json       # Also save JSON output
```

### Via API
```bash
# Generate test plan
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"ticket_key": "SCRUM-10", "post_to_jira": true, "save_json": true}'

# Get ticket info
curl http://localhost:8000/api/ticket/SCRUM-10

# Download test plan
curl http://localhost:8000/api/download/SCRUM-10 -o TP-SCRUM-10.md
```

## Project Structure

```
BLAST_fw/
├── config.py              # Configuration management (.env)
├── jira_client.py         # Jira REST API client (ADF parsing)
├── test_plan_generator.py # IEEE 829 test plan generation
├── markdown_renderer.py   # Markdown output (IEEE 829 template)
├── main.py                # CLI entry point
├── server.py              # FastAPI backend server
├── requirements.txt       # Python dependencies
├── start.bat / start.sh   # Startup scripts
├── frontend/              # React + Vite + TypeScript
│   ├── src/
│   │   ├── App.tsx        # Main UI component
│   │   ├── main.tsx       # Entry point
│   │   └── index.css      # Styles
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── test-plans/            # Generated test plans (output)
├── .env                   # Jira credentials (not committed)
├── gemini.md              # Project constitution (BLAST)
├── task_plan.md           # Task tracking (BLAST)
├── findings.md            # Research findings (BLAST)
└── progress.md            # Progress log (BLAST)
```

## Test Plan Sections (IEEE 829)

1. **Introduction** - Purpose, Scope, References, Overview
2. **Test Items** - What to test with risk levels
3. **Features to be Tested** - From acceptance criteria
4. **Features Not to be Tested** - Explicit exclusions
5. **Approach** - Strategy, Techniques, Tools, Entry/Exit Criteria
6. **Pass/Fail Criteria** - Item and plan level
7. **Suspension/Resumption Criteria**
8. **Test Deliverables** - Documents produced
9. **Testing Tasks** - Work breakdown with owners/effort
10. **Environmental Needs** - HW, SW, Network, Data, Tools
11. **Responsibilities** - RACI matrix
12. **Staffing and Training**
13. **Schedule** - Milestones
14. **Risks and Contingencies** - Risk register
15. **Approvals** - Sign-off table

## Acceptance Criteria Parsing

The tool automatically extracts acceptance criteria from ticket descriptions by looking for:
- `## Acceptance Criteria`
- `## AC`
- `Acceptance Criteria:`
- `AC:`

Supports both Atlassian Document Format (ADF) and Markdown descriptions.

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `JIRA_BASE_URL` | - | Jira Cloud base URL |
| `JIRA_EMAIL` | - | Jira account email |
| `JIRA_API_TOKEN` | - | Jira API token |
| `JIRA_PROJECT_KEY` | `SCRUM` | Project key prefix |
| `OUTPUT_DIR` | `test-plans` | Output directory |
| `FILENAME_TEMPLATE` | `TP-{key}.md` | Output filename pattern |

## Development

### Running Tests
```bash
# Backend tests (when added)
pytest

# Frontend tests (when added)
cd frontend && npm test
```

### Building Frontend for Production
```bash
cd frontend
npm run build
# Output in frontend/dist/
```

## Security Notes

- Never commit `.env` file (contains API tokens)
- API tokens have minimal required permissions: "Browse Projects", "Add Comments"
- Use HTTPS in production
- Consider adding authentication to the API for production use

## License

Internal tool - not for distribution.