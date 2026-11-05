"""
FastAPI Backend Server for Jira Test Plan Generator.
Provides REST API endpoints for the React frontend.
"""
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config import config
from jira_client import JiraClient
from test_plan_generator import TestPlanGenerator
from markdown_renderer import MarkdownRenderer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Jira Test Plan Generator API",
    description="Generate IEEE 829 test plans from Jira tickets",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
jira_client = JiraClient()
generator = TestPlanGenerator()
renderer = MarkdownRenderer()


class GenerateRequest(BaseModel):
    ticket_key: str
    post_to_jira: bool = True
    save_json: bool = False


class GenerateResponse(BaseModel):
    success: bool
    markdown: Optional[str] = None
    json: Optional[dict] = None
    file_path: Optional[str] = None
    error: Optional[str] = None


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "jira-test-plan-generator"}


@app.get("/api/ticket/{ticket_key}")
async def get_ticket(ticket_key: str):
    """Fetch and return basic ticket info for preview."""
    try:
        ticket = jira_client.get_issue(ticket_key.upper())
        return {
            "key": ticket.key,
            "summary": ticket.summary,
            "priority": ticket.priority,
            "issue_type": ticket.issue_type,
            "acceptance_criteria": ticket.acceptance_criteria[:500] if ticket.acceptance_criteria else ""
        }
    except Exception as e:
        logger.error(f"Failed to fetch ticket {ticket_key}: {e}")
        raise HTTPException(status_code=404, detail=f"Ticket not found: {e}")


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_test_plan(request: GenerateRequest):
    """Generate test plan from Jira ticket."""
    ticket_key = request.ticket_key.upper().strip()

    try:
        # Fetch ticket
        logger.info(f"Fetching ticket {ticket_key}...")
        ticket = jira_client.get_issue(ticket_key)

        # Generate test plan
        logger.info(f"Generating test plan for {ticket_key}...")
        test_plan = generator.generate(ticket)

        # Save Markdown
        md_path = renderer.save(test_plan)
        logger.info(f"Saved Markdown to {md_path}")

        # Optionally save JSON
        json_data = None
        if request.save_json:
            json_path = renderer.save_json(test_plan)
            logger.info(f"Saved JSON to {json_path}")
            json_data = test_plan.to_json()

        # Optionally post to Jira
        if request.post_to_jira:
            logger.info(f"Posting comment to {ticket_key}...")
            try:
                comment_text = renderer.render(test_plan)
                if len(comment_text) > 30000:
                    comment_text = comment_text[:30000] + "\n\n... (truncated, see full file)"
                jira_client.add_comment(ticket_key, comment_text)
                logger.info(f"Posted comment to {ticket_key}")
            except Exception as e:
                logger.error(f"Failed to post Jira comment: {e}")
                # Don't fail the whole request, just log

        # Read back markdown for response
        with open(md_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        return GenerateResponse(
            success=True,
            markdown=markdown_content,
            json=json_data,
            file_path=str(md_path)
        )

    except Exception as e:
        logger.error(f"Generation failed for {ticket_key}: {e}")
        return GenerateResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/download/{ticket_key}")
async def download_test_plan(ticket_key: str):
    """Download generated test plan as Markdown file."""
    ticket_key = ticket_key.upper().strip()
    filename = f"TP-{ticket_key}.md"
    filepath = Path(config.output.directory) / filename

    if not filepath.exists():
        # Try to generate it
        try:
            ticket = jira_client.get_issue(ticket_key)
            test_plan = generator.generate(ticket)
            renderer.save(test_plan)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Test plan not found: {e}")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/markdown"
    )


@app.get("/api/list")
async def list_test_plans():
    """List all generated test plans."""
    output_dir = Path(config.output.directory)
    if not output_dir.exists():
        return {"plans": []}

    plans = []
    for file in output_dir.glob("TP-*.md"):
        plans.append({
            "filename": file.name,
            "size": file.stat().st_size,
            "modified": file.stat().st_mtime
        })

    return {"plans": sorted(plans, key=lambda x: x["modified"], reverse=True)}


if __name__ == "__main__":
    import uvicorn

    # Validate config
    errors = config.validate()
    if errors:
        logger.error("Configuration errors:")
        for err in errors:
            logger.error(f"  - {err}")
        exit(1)

    logger.info("Starting Jira Test Plan Generator API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)