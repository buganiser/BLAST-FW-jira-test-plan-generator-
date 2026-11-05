#!/usr/bin/env python3
"""
Main CLI entry point for Jira Test Plan Generator.
Orchestrates the full pipeline: fetch ticket -> generate test plan -> save -> post to Jira.
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from config import config
from jira_client import JiraClient, JiraTicket
from test_plan_generator import TestPlanGenerator
from markdown_renderer import MarkdownRenderer


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_test_plan(ticket_key: str, post_to_jira: bool = True, save_json: bool = False) -> tuple[str, str]:
    """
    Full pipeline: fetch ticket, generate test plan, save markdown, optionally post to Jira.
    Returns: (markdown_filepath, test_plan_json)
    """
    logger.info(f"Starting test plan generation for {ticket_key}")

    # Initialize components
    jira_client = JiraClient()
    generator = TestPlanGenerator()
    renderer = MarkdownRenderer()

    # Test connection
    logger.info("Testing Jira connection...")
    if not jira_client.test_connection():
        logger.error("Failed to connect to Jira. Check credentials.")
        sys.exit(1)

    # Fetch ticket
    logger.info(f"Fetching ticket {ticket_key}...")
    try:
        ticket = jira_client.get_issue(ticket_key)
        logger.info(f"Fetched: {ticket.key} - {ticket.summary}")
        logger.info(f"Priority: {ticket.priority}, Type: {ticket.issue_type}")
        if ticket.acceptance_criteria:
            logger.info(f"Found acceptance criteria ({len(ticket.acceptance_criteria)} chars)")
        else:
            logger.warning("No acceptance criteria found in description")
    except Exception as e:
        logger.error(f"Failed to fetch ticket: {e}")
        sys.exit(1)

    # Generate test plan
    logger.info("Generating test plan...")
    test_plan = generator.generate(ticket)
    logger.info(f"Generated test plan with {len(test_plan.test_items)} test items")

    # Save Markdown
    logger.info("Saving Markdown file...")
    md_path = renderer.save(test_plan)
    logger.info(f"Saved to {md_path}")

    # Optionally save JSON
    if save_json:
        json_path = renderer.save_json(test_plan)
        logger.info(f"Saved JSON to {json_path}")

    # Optionally post to Jira
    if post_to_jira:
        logger.info("Posting test plan as Jira comment...")
        try:
            # Render markdown for comment (truncated if too long)
            comment_text = renderer.render(test_plan)
            # Jira comment has size limits, truncate if needed
            if len(comment_text) > 30000:
                comment_text = comment_text[:30000] + "\n\n... (truncated, see full file)"
            jira_client.add_comment(ticket_key, comment_text)
            logger.info(f"Successfully posted comment to {ticket_key}")
        except Exception as e:
            logger.error(f"Failed to post Jira comment: {e}")
            logger.info("Markdown file saved locally. You can manually copy it to Jira.")

    return str(md_path), test_plan.to_json()


def main():
    parser = argparse.ArgumentParser(
        description="Generate IEEE 829 Test Plan from Jira ticket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py SCRUM-10                    # Generate and post to Jira
  python main.py SCRUM-10 --no-post          # Generate only, don't post to Jira
  python main.py SCRUM-10 --json             # Also save JSON output
  python main.py SCRUM-10 --no-post --json   # Generate only, save both formats
        """
    )
    parser.add_argument('ticket_key', help='Jira ticket key (e.g., SCRUM-10)')
    parser.add_argument('--no-post', action='store_true', help='Do not post comment to Jira')
    parser.add_argument('--json', action='store_true', help='Also save JSON output')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate config
    errors = config.validate()
    if errors:
        logger.error("Configuration errors:")
        for err in errors:
            logger.error(f"  - {err}")
        logger.error("Please check your .env file")
        sys.exit(1)

    # Run pipeline
    try:
        md_path, _ = generate_test_plan(
            ticket_key=args.ticket_key,
            post_to_jira=not args.no_post,
            save_json=args.json
        )
        logger.info(f"Done! Test plan saved to: {md_path}")
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()