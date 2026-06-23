"""Research agents for Octane Capital Lab."""

from octane_capital.agents.auditor import (
    create_audit_task,
    create_auditor_agent,
    parse_audit_output,
)
from octane_capital.agents.manager import create_cio_agent
from octane_capital.agents.scout import (
    create_scout_agent,
    create_scout_task,
    parse_scout_output,
)

__all__ = [
    "create_scout_agent",
    "create_scout_task",
    "parse_scout_output",
    "create_auditor_agent",
    "create_audit_task",
    "parse_audit_output",
    "create_cio_agent",
]
