"""
Configuration module for Jira Test Plan Generator.
Loads settings from .env file and provides typed configuration objects.
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Load .env file manually (no external dependency)
def load_env_file(env_path: Path) -> None:
    """Load environment variables from .env file."""
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# Load .env from project root
project_root = Path(__file__).parent
load_env_file(project_root / '.env')


@dataclass(frozen=True)
class JiraConfig:
    """Jira connection configuration."""
    base_url: str
    email: str
    api_token: str
    project_key: str = "SCRUM"

    @property
    def auth_header(self) -> str:
        """Generate Basic Auth header value."""
        import base64
        credentials = f"{self.email}:{self.api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    @property
    def api_base(self) -> str:
        """REST API v3 base URL."""
        return f"{self.base_url.rstrip('/')}/rest/api/3"

    @classmethod
    def from_env(cls) -> 'JiraConfig':
        """Create config from environment variables."""
        return cls(
            base_url=os.environ.get('JIRA_BASE_URL', ''),
            email=os.environ.get('JIRA_EMAIL', ''),
            api_token=os.environ.get('JIRA_API_TOKEN', ''),
            project_key=os.environ.get('JIRA_PROJECT_KEY', 'SCRUM')
        )

    def validate(self) -> list[str]:
        """Validate configuration, return list of errors."""
        errors = []
        if not self.base_url:
            errors.append("JIRA_BASE_URL not set")
        if not self.email:
            errors.append("JIRA_EMAIL not set")
        if not self.api_token:
            errors.append("JIRA_API_TOKEN not set")
        return errors


@dataclass(frozen=True)
class OutputConfig:
    """Output file configuration."""
    directory: str = "test-plans"
    filename_template: str = "TP-{key}.md"

    @classmethod
    def from_env(cls) -> 'OutputConfig':
        return cls(
            directory=os.environ.get('OUTPUT_DIR', 'test-plans'),
            filename_template=os.environ.get('FILENAME_TEMPLATE', 'TP-{key}.md')
        )


@dataclass(frozen=True)
class GenerationConfig:
    """Test plan generation configuration."""
    default_risk_mapping: dict[str, str] = None

    def __post_init__(self):
        if self.default_risk_mapping is None:
            object.__setattr__(self, 'default_risk_mapping', {
                "Highest": "High",
                "High": "High",
                "Medium": "Medium",
                "Low": "Low",
                "Lowest": "Low"
            })

    @classmethod
    def from_env(cls) -> 'GenerationConfig':
        return cls()


@dataclass(frozen=True)
class AppConfig:
    """Application configuration container."""
    jira: JiraConfig
    output: OutputConfig
    generation: GenerationConfig

    @classmethod
    def load(cls) -> 'AppConfig':
        """Load all configuration from environment."""
        return cls(
            jira=JiraConfig.from_env(),
            output=OutputConfig.from_env(),
            generation=GenerationConfig.from_env()
        )

    def validate(self) -> list[str]:
        """Validate all configuration."""
        return self.jira.validate()


# Global config instance
config = AppConfig.load()