"""
Test Plan Generator - Core logic for creating IEEE 829 compliant test plans from Jira tickets.
"""
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

from jira_client import JiraTicket
from config import config


@dataclass
class TestItem:
    """Individual test item in the test plan."""
    id: str
    name: str
    description: str
    risk_level: str  # High, Medium, Low
    references: list[str] = field(default_factory=list)


@dataclass
class TestingTask:
    """Testing task in the schedule."""
    id: str
    name: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    owner: str = "QA Team"
    effort_estimate: str = "TBD"


@dataclass
class RiskContingency:
    """Risk and contingency entry."""
    risk: str
    probability: str  # High, Medium, Low
    impact: str       # High, Medium, Low
    mitigation: str
    contingency: str


@dataclass
class Approval:
    """Approval record."""
    role: str
    name: str = ""
    signature: str = ""
    date: str = ""


@dataclass
class TestPlan:
    """Complete IEEE 829 Test Plan structure."""
    identifier: str
    references: list[str] = field(default_factory=list)
    introduction: dict = field(default_factory=dict)
    test_items: list[TestItem] = field(default_factory=list)
    features_to_test: list[str] = field(default_factory=list)
    features_not_to_test: list[str] = field(default_factory=list)
    approach: dict = field(default_factory=dict)
    pass_fail_criteria: dict = field(default_factory=dict)
    suspension_resumption: str = ""
    test_deliverables: list[str] = field(default_factory=list)
    testing_tasks: list[TestingTask] = field(default_factory=list)
    environment: dict = field(default_factory=dict)
    responsibilities: list[dict] = field(default_factory=list)
    staffing: str = ""
    schedule: dict = field(default_factory=dict)
    risks_contingencies: list[RiskContingency] = field(default_factory=list)
    approvals: list[Approval] = field(default_factory=list)

    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        result = asdict(self)
        # Convert nested dataclasses
        result['test_items'] = [asdict(item) for item in self.test_items]
        result['testing_tasks'] = [asdict(task) for task in self.testing_tasks]
        result['risks_contingencies'] = [asdict(rc) for rc in self.risks_contingencies]
        result['approvals'] = [asdict(appr) for appr in self.approvals]
        return result


class TestPlanGenerator:
    """Generates IEEE 829 test plans from Jira tickets."""

    def __init__(self, generation_config=None):
        self.gen_config = generation_config or config.generation
        self.risk_mapping = self.gen_config.default_risk_mapping

    def generate(self, ticket: JiraTicket) -> TestPlan:
        """Generate a complete test plan from a Jira ticket."""
        plan_id = f"TP-{ticket.key}"

        # Extract acceptance criteria items
        ac_items = self._parse_acceptance_criteria(ticket.acceptance_criteria)

        # Build all sections
        test_plan = TestPlan(
            identifier=plan_id,
            references=self._build_references(ticket),
            introduction=self._build_introduction(ticket),
            test_items=self._build_test_items(ticket, ac_items),
            features_to_test=self._build_features_to_test(ticket, ac_items),
            features_not_to_test=self._build_features_not_to_test(ticket),
            approach=self._build_approach(ticket),
            pass_fail_criteria=self._build_pass_fail_criteria(ticket),
            suspension_resumption=self._build_suspension_resumption(),
            test_deliverables=self._build_test_deliverables(),
            testing_tasks=self._build_testing_tasks(ticket, ac_items),
            environment=self._build_environment(ticket),
            responsibilities=self._build_responsibilities(ticket),
            staffing=self._build_staffing(),
            schedule=self._build_schedule(ticket),
            risks_contingencies=self._build_risks_contingencies(ticket),
            approvals=self._build_approvals()
        )

        return test_plan

    def _parse_acceptance_criteria(self, ac_text: str) -> list[dict]:
        """Parse acceptance criteria text into structured items."""
        items = []
        if not ac_text:
            return items

        # Split by common delimiters
        lines = ac_text.split('\n')
        current_item = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for numbered/bulleted items
            if re.match(r'^[\d\-\*\.\)]+\s+', line):
                if current_item:
                    items.append(current_item)
                # Clean the line
                clean_line = re.sub(r'^[\d\-\*\.\)]+\s+', '', line)
                current_item = {"text": clean_line, "raw": line}
            elif current_item:
                current_item["text"] += " " + line
            else:
                # First line without marker
                current_item = {"text": line, "raw": line}

        if current_item:
            items.append(current_item)

        # If no structured items found, treat whole text as one item
        if not items and ac_text.strip():
            items.append({"text": ac_text.strip(), "raw": ac_text.strip()})

        return items

    def _build_references(self, ticket: JiraTicket) -> list[str]:
        """Build references section."""
        refs = [
            f"Jira Ticket: {ticket.key} - {ticket.summary}",
            f"Jira URL: {config.jira.base_url}/browse/{ticket.key}"
        ]
        if ticket.fix_versions:
            refs.append(f"Fix Version(s): {', '.join(ticket.fix_versions)}")
        if ticket.components:
            refs.append(f"Components: {', '.join(ticket.components)}")
        return refs

    def _build_introduction(self, ticket: JiraTicket) -> dict:
        """Build introduction section."""
        return {
            "purpose": f"This test plan defines the testing approach for {ticket.key}: {ticket.summary}. "
                       f"It covers functional validation based on the acceptance criteria defined in the Jira ticket.",
            "scope": f"In Scope: {ticket.issue_type} - {ticket.summary}. "
                     f"Testing focuses on functional requirements derived from acceptance criteria. "
                     f"Out of Scope: Performance testing, security testing, usability testing (unless specified in AC).",
            "overview": f"This document follows IEEE 829 standard for software test documentation. "
                        f"The test plan is generated automatically from Jira ticket {ticket.key} "
                        f"and includes test items, approach, schedule, and risk assessment."
        }

    def _build_test_items(self, ticket: JiraTicket, ac_items: list[dict]) -> list[TestItem]:
        """Build test items from acceptance criteria."""
        items = []
        risk_level = self._map_priority_to_risk(ticket.priority)

        # Create test items from AC
        for i, ac in enumerate(ac_items, 1):
            item_id = f"TI-{ticket.key}-{i:03d}"
            items.append(TestItem(
                id=item_id,
                name=f"Verify {ac['text'][:80]}",
                description=f"Test that {ac['text']}",
                risk_level=risk_level,
                references=[ticket.key]
            ))

        # Add general test items if no AC
        if not items:
            items.append(TestItem(
                id=f"TI-{ticket.key}-001",
                name=f"Functional Test: {ticket.summary}",
                description=f"Verify the implementation of {ticket.summary} per requirements",
                risk_level=risk_level,
                references=[ticket.key]
            ))

        return items

    def _build_features_to_test(self, ticket: JiraTicket, ac_items: list[dict]) -> list[str]:
        """Build features to test list."""
        features = [ticket.summary]
        for ac in ac_items:
            features.append(ac['text'][:100])
        # Add issue type specific features
        if ticket.issue_type.lower() == 'bug':
            features.append("Regression: Verify fix does not break existing functionality")
        return features

    def _build_features_not_to_test(self, ticket: JiraTicket) -> list[str]:
        """Build features not to test list."""
        not_test = [
            "Performance/Load testing (unless specified in AC)",
            "Security penetration testing",
            "Usability/Accessibility testing (unless specified in AC)",
            "Third-party integrations not mentioned in ticket",
            "Infrastructure/DevOps changes"
        ]
        return not_test

    def _build_approach(self, ticket: JiraTicket) -> dict:
        """Build test approach section."""
        strategy = "Black-box functional testing based on acceptance criteria. "
        if ticket.issue_type.lower() == 'bug':
            strategy += "Regression testing to verify fix and ensure no regressions. "
        elif ticket.issue_type.lower() == 'story':
            strategy += "Feature testing covering happy path, edge cases, and negative scenarios. "

        return {
            "strategy": strategy.strip(),
            "techniques": [
                "Equivalence Partitioning",
                "Boundary Value Analysis",
                "Decision Table Testing",
                "State Transition Testing",
                "Error Guessing"
            ],
            "tools": [
                "Manual testing",
                "Browser DevTools",
                "API testing tools (Postman/curl)",
                "Test data generation scripts"
            ],
            "entry_criteria": [
                "Code deployed to test environment",
                "Test environment matches production configuration",
                "Test data available",
                "Smoke tests pass"
            ],
            "exit_criteria": [
                "All test items executed",
                "Critical/High defects resolved",
                "Test coverage >= 90% of acceptance criteria",
                "No blocking defects remain"
            ],
            "suspension_criteria": [
                "Critical defect blocking further testing",
                "Test environment unavailable",
                "Requirements changed significantly"
            ],
            "resumption_criteria": [
                "Blocking defect resolved and verified",
                "Test environment restored",
                "Updated requirements reviewed"
            ]
        }

    def _build_pass_fail_criteria(self, ticket: JiraTicket) -> dict:
        """Build pass/fail criteria."""
        return {
            "item_pass_criteria": "A test item passes when all its test cases execute successfully "
                                  "and the actual behavior matches expected behavior per acceptance criteria.",
            "plan_pass_criteria": "Test plan passes when: "
                                  "1) All Critical/High risk test items pass, "
                                  "2) No Critical/High severity defects open, "
                                  "3) >= 90% of Medium risk test items pass, "
                                  "4) All acceptance criteria verified"
        }

    def _build_suspension_resumption(self) -> str:
        """Build suspension/resumption criteria."""
        return ("Testing may be suspended if a Critical severity defect blocks further test execution, "
                "the test environment becomes unavailable, or requirements change significantly. "
                "Testing resumes when the blocking issue is resolved, environment is restored, "
                "or updated requirements are reviewed and test plan is updated accordingly.")

    def _build_test_deliverables(self) -> list[str]:
        """Build test deliverables list."""
        return [
            "Test Plan (this document)",
            "Test Cases / Test Scripts",
            "Test Execution Results",
            "Defect Reports",
            "Test Summary Report",
            "Traceability Matrix"
        ]

    def _build_testing_tasks(self, ticket: JiraTicket, ac_items: list[dict]) -> list[TestingTask]:
        """Build testing tasks."""
        tasks = [
            TestingTask(
                id=f"TT-{ticket.key}-001",
                name="Test Plan Review",
                description="Review and approve test plan with stakeholders",
                owner="QA Lead",
                effort_estimate="1 hour"
            ),
            TestingTask(
                id=f"TT-{ticket.key}-002",
                name="Test Case Design",
                description=f"Design detailed test cases for {len(ac_items)} acceptance criteria items",
                owner="QA Engineer",
                effort_estimate="2-4 hours"
            ),
            TestingTask(
                id=f"TT-{ticket.key}-003",
                name="Test Environment Setup",
                description="Prepare test environment, data, and tools",
                owner="DevOps/QA",
                effort_estimate="1-2 hours"
            ),
            TestingTask(
                id=f"TT-{ticket.key}-004",
                name="Test Execution",
                description="Execute test cases, log defects, perform retesting",
                owner="QA Engineer",
                effort_estimate="4-8 hours"
            ),
            TestingTask(
                id=f"TT-{ticket.key}-005",
                name="Defect Verification",
                description="Verify defect fixes and perform regression testing",
                owner="QA Engineer",
                effort_estimate="2-4 hours"
            ),
            TestingTask(
                id=f"TT-{ticket.key}-006",
                name="Test Summary Report",
                description="Compile test results and create summary report",
                owner="QA Lead",
                effort_estimate="1 hour"
            )
        ]
        return tasks

    def _build_environment(self, ticket: JiraTicket) -> dict:
        """Build environment requirements."""
        return {
            "hardware": [
                "Standard developer workstation",
                "Mobile device (if mobile features)",
                "Network access to test environment"
            ],
            "software": [
                "Supported browsers: Chrome, Firefox, Safari, Edge (latest 2 versions)",
                "Operating Systems: Windows 10/11, macOS, Linux",
                "Test environment URL",
                "API testing tools"
            ],
            "network": [
                "Access to test environment",
                "VPN access (if required)",
                "Database access for test data verification"
            ],
            "data_requirements": [
                "Test user accounts with various roles",
                "Sample data for functional scenarios",
                "Edge case data sets"
            ],
            "tools": [
                "Browser DevTools",
                "API client (Postman/Insomnia)",
                "Screen capture tool",
                "Defect tracking (Jira)"
            ]
        }

    def _build_responsibilities(self, ticket: JiraTicket) -> list[dict]:
        """Build responsibilities matrix."""
        return [
            {
                "role": "QA Lead",
                "name": ticket.assignee or "TBD",
                "responsibilities": [
                    "Test plan review and approval",
                    "Resource allocation",
                    "Risk assessment",
                    "Stakeholder communication"
                ]
            },
            {
                "role": "QA Engineer",
                "name": ticket.assignee or "TBD",
                "responsibilities": [
                    "Test case design",
                    "Test execution",
                    "Defect reporting",
                    "Retesting fixes"
                ]
            },
            {
                "role": "Developer",
                "name": ticket.assignee or "TBD",
                "responsibilities": [
                    "Unit testing",
                    "Code review",
                    "Defect fixing",
                    "Deployment to test env"
                ]
            },
            {
                "role": "Product Owner",
                "name": ticket.reporter or "TBD",
                "responsibilities": [
                    "Acceptance criteria clarification",
                    "UAT participation",
                    "Sign-off on release"
                ]
            }
        ]

    def _build_staffing(self) -> str:
        """Build staffing section."""
        return ("1 QA Lead (part-time), 1-2 QA Engineers (full-time during execution), "
                "Developers (as needed for defect fixes), Product Owner (for UAT/sign-off)")

    def _build_schedule(self, ticket: JiraTicket) -> dict:
        """Build schedule with milestones."""
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "milestones": [
                {
                    "name": "Test Plan Complete",
                    "date": today,
                    "description": "Test plan reviewed and approved"
                },
                {
                    "name": "Test Cases Ready",
                    "date": "TBD + 2 days",
                    "description": "Test cases designed and reviewed"
                },
                {
                    "name": "Test Execution Start",
                    "date": "TBD + 3 days",
                    "description": "Begin test execution in test environment"
                },
                {
                    "name": "Test Execution Complete",
                    "date": "TBD + 7 days",
                    "description": "All test cases executed, defects logged"
                },
                {
                    "name": "Test Summary Report",
                    "date": "TBD + 8 days",
                    "description": "Final report delivered, sign-off obtained"
                }
            ]
        }

    def _build_risks_contingencies(self, ticket: JiraTicket) -> list[RiskContingency]:
        """Build risks and contingencies."""
        risks = []

        # Priority-based risk
        priority_risk = self._map_priority_to_risk(ticket.priority)
        risks.append(RiskContingency(
            risk=f"High priority ticket ({ticket.priority}) - limited time for thorough testing",
            probability="Medium",
            impact=priority_risk,
            mitigation="Prioritize Critical/High risk test items; automate regression where possible",
            contingency="Extend test execution timeline; reduce scope of Low risk items"
        ))

        # General risks
        risks.extend([
            RiskContingency(
                risk="Test environment instability or unavailability",
                probability="Medium",
                impact="High",
                mitigation="Environment health checks before execution; backup environment identified",
                contingency="Escalate to DevOps; use local/staging environment as fallback"
            ),
            RiskContingency(
                risk="Incomplete or ambiguous acceptance criteria",
                probability="Medium",
                impact="Medium",
                mitigation="Clarify AC with Product Owner during test plan review",
                contingency="Document assumptions; test based on best understanding"
            ),
            RiskContingency(
                risk="Late defect fixes reducing retest time",
                probability="High",
                impact="Medium",
                mitigation="Early defect reporting; prioritize Critical/High defects",
                contingency="Risk-based retesting; focus on fixed areas only"
            ),
            RiskContingency(
                risk="Scope creep during testing",
                probability="Low",
                impact="Medium",
                mitigation="Strict change control; new requirements go to next sprint",
                contingency="Assess impact; update test plan if approved"
            )
        ])

        # Add component-specific risks
        for comp in ticket.components:
            risks.append(RiskContingency(
                risk=f"Component '{comp}' complexity may hide integration issues",
                probability="Medium",
                impact="Medium",
                mitigation="Include integration test cases; coordinate with component owners",
                contingency="Additional integration testing session"
            ))

        return risks

    def _build_approvals(self) -> list[Approval]:
        """Build approvals section."""
        return [
            Approval(role="QA Lead", name="", signature="", date=""),
            Approval(role="Development Lead", name="", signature="", date=""),
            Approval(role="Product Owner", name="", signature="", date="")
        ]

    def _map_priority_to_risk(self, priority: str) -> str:
        """Map Jira priority to risk level."""
        return self.risk_mapping.get(priority, "Medium")


import re  # For regex in _parse_acceptance_criteria