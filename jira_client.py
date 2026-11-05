"""
Jira REST API Client for fetching tickets and posting comments.
Handles authentication, ADF parsing, and error handling.
"""
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import requests

from config import config, JiraConfig

logger = logging.getLogger(__name__)


@dataclass
class JiraTicket:
    """Parsed Jira ticket data."""
    id: str
    key: str
    summary: str
    description: str  # Raw ADF JSON string
    description_text: str  # Plain text extracted from ADF
    acceptance_criteria: str
    issue_type: str
    priority: str
    labels: list[str]
    components: list[str]
    fix_versions: list[str]
    assignee: Optional[str]
    reporter: Optional[str]
    created: str
    updated: str
    status: str
    raw_fields: dict = field(default_factory=dict)


class JiraClient:
    """Client for interacting with Jira Cloud REST API v3."""

    def __init__(self, jira_config: Optional[JiraConfig] = None):
        self.cfg = jira_config or config.jira
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': self.cfg.auth_header,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate Jira configuration."""
        errors = self.cfg.validate()
        if errors:
            raise ValueError(f"Invalid Jira config: {', '.join(errors)}")

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling."""
        url = f"{self.cfg.api_base}{endpoint}"
        logger.debug(f"{method} {url}")
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            logger.error(f"Jira API error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            raise

    def get_issue(self, issue_key: str) -> JiraTicket:
        """
        Fetch a Jira issue by key and parse into JiraTicket.
        Includes all fields needed for test plan generation.
        """
        fields = [
            'summary', 'description', 'issuetype', 'priority',
            'labels', 'components', 'fixVersions',
            'assignee', 'reporter', 'created', 'updated', 'status'
        ]
        fields_param = ','.join(fields)
        response = self._request('GET', f'/issue/{issue_key}?fields={fields_param}')
        data = response.json()

        return self._parse_issue(data)

    def _parse_issue(self, data: dict) -> JiraTicket:
        """Parse raw Jira API response into JiraTicket."""
        fields = data.get('fields', {})

        # Extract description (ADF format)
        description_adf = fields.get('description')
        description_text = ""
        acceptance_criteria = ""

        if description_adf:
            description_text = self._adf_to_text(description_adf)
            acceptance_criteria = self._extract_acceptance_criteria(description_text)

        # Parse assignee/reporter
        assignee = fields.get('assignee')
        reporter = fields.get('reporter')

        return JiraTicket(
            id=data.get('id', ''),
            key=data.get('key', ''),
            summary=fields.get('summary', ''),
            description=json.dumps(description_adf) if description_adf else '',
            description_text=description_text,
            acceptance_criteria=acceptance_criteria,
            issue_type=fields.get('issuetype', {}).get('name', 'Unknown'),
            priority=fields.get('priority', {}).get('name', 'Medium'),
            labels=fields.get('labels', []),
            components=[c.get('name', '') for c in fields.get('components', [])],
            fix_versions=[v.get('name', '') for v in fields.get('fixVersions', [])],
            assignee=assignee.get('displayName') if assignee else None,
            reporter=reporter.get('displayName') if reporter else None,
            created=fields.get('created', ''),
            updated=fields.get('updated', ''),
            status=fields.get('status', {}).get('name', 'Unknown'),
            raw_fields=fields
        )

    def _adf_to_text(self, adf: dict) -> str:
        """
        Convert Atlassian Document Format (ADF) to plain text.
        Handles basic ADF nodes: doc, paragraph, text, heading, bulletList, orderedList, listItem, codeBlock, panel.
        """
        def extract_text(node: Any) -> str:
            if isinstance(node, str):
                return node
            if not isinstance(node, dict):
                return ""

            node_type = node.get('type', '')
            content = node.get('content', [])

            if node_type == 'text':
                text = node.get('text', '')
                marks = node.get('marks', [])
                for mark in marks:
                    if mark.get('type') == 'strong':
                        text = f"**{text}**"
                    elif mark.get('type') == 'em':
                        text = f"*{text}*"
                    elif mark.get('type') == 'code':
                        text = f"`{text}`"
                return text

            elif node_type in ('paragraph', 'heading'):
                level = node.get('attrs', {}).get('level', 1) if node_type == 'heading' else 0
                prefix = '#' * level + ' ' if level > 0 else ''
                child_text = ''.join(extract_text(c) for c in content)
                return f"{prefix}{child_text}\n\n"

            elif node_type in ('bulletList', 'orderedList'):
                items = []
                for i, item in enumerate(content):
                    item_text = ''.join(extract_text(c) for c in item.get('content', []))
                    prefix = f"{i+1}. " if node_type == 'orderedList' else "- "
                    items.append(f"{prefix}{item_text.strip()}")
                return '\n'.join(items) + '\n\n'

            elif node_type == 'listItem':
                return ''.join(extract_text(c) for c in content)

            elif node_type == 'codeBlock':
                language = node.get('attrs', {}).get('language', '')
                code = ''.join(extract_text(c) for c in content)
                return f"\n```{language}\n{code}\n```\n\n"

            elif node_type == 'panel':
                panel_type = node.get('attrs', {}).get('panelType', 'note')
                panel_text = ''.join(extract_text(c) for c in content)
                return f"\n> **{panel_type.upper()}**: {panel_text}\n\n"

            elif node_type == 'hardBreak':
                return '\n'

            elif node_type == 'doc':
                return ''.join(extract_text(c) for c in content)

            # Fallback: recursively extract text from content
            if content:
                return ''.join(extract_text(c) for c in content)

            return ""

        return extract_text(adf).strip()

    def _extract_acceptance_criteria(self, description_text: str) -> str:
        """
        Extract acceptance criteria from description text.
        Looks for common headers and patterns.
        """
        patterns = [
            r'(?i)##?\s*acceptance criteria\s*\n(.*?)(?=\n##?\s|\Z)',
            r'(?i)##?\s*ac\s*\n(.*?)(?=\n##?\s|\Z)',
            r'(?i)acceptance criteria[:\-]\s*(.*?)(?=\n\n|\n##?\s|\Z)',
            r'(?i)ac[:\-]\s*(.*?)(?=\n\n|\n##?\s|\Z)',
        ]

        for pattern in patterns:
            match = re.search(pattern, description_text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # If no explicit AC section, return the whole description (will be parsed later)
        return description_text

    def add_comment(self, issue_key: str, comment_text: str) -> dict:
        """
        Add a comment to a Jira issue.
        Comment must be in ADF format for Jira Cloud.
        """
        adf_comment = self._text_to_adf(comment_text)
        payload = {"body": adf_comment}

        response = self._request('POST', f'/issue/{issue_key}/comment', json=payload)
        return response.json()

    def _text_to_adf(self, text: str) -> dict:
        """Convert plain text/markdown to basic ADF format."""
        # Simple conversion: split by double newlines for paragraphs
        paragraphs = text.split('\n\n')
        content = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check for headings
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', para)
            if heading_match:
                level = len(heading_match.group(1))
                content.append({
                    "type": "heading",
                    "attrs": {"level": level},
                    "content": [{"type": "text", "text": heading_match.group(2)}]
                })
                continue

            # Check for bullet points
            if para.startswith('- ') or para.startswith('* '):
                items = []
                for line in para.split('\n'):
                    line = line.strip()
                    if line.startswith('- ') or line.startswith('* '):
                        items.append({
                            "type": "listItem",
                            "content": [{
                                "type": "paragraph",
                                "content": [{"type": "text", "text": line[2:]}]
                            }]
                        })
                if items:
                    content.append({"type": "bulletList", "content": items})
                continue

            # Regular paragraph
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": para}]
            })

        return {
            "type": "doc",
            "version": 1,
            "content": content
        }

    def test_connection(self) -> bool:
        """Test Jira connection by getting current user."""
        try:
            response = self._request('GET', '/myself')
            user = response.json()
            logger.info(f"Connected as: {user.get('displayName', user.get('emailAddress', 'Unknown'))}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False