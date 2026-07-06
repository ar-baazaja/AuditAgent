from app.connectors.aws import AWSConnector
from app.connectors.github import GitHubConnector

_CONNECTORS = {
    "aws": AWSConnector(),
    "github": GitHubConnector(),
}

def get_connector(check_type: str):
    """Return the connector for a control's check_type, defaulting to AWS."""
    return _CONNECTORS.get(check_type, _CONNECTORS["aws"])
