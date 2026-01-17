"""Octane Global Trust - Agents Module"""

from .scout import create_scout_agent, create_scout_task, parse_scout_output
from .auditor import create_auditor_agent, create_audit_task, parse_audit_output
from .manager import create_cio_agent

__all__ = [
    "create_scout_agent",
    "create_scout_task", 
    "parse_scout_output",
    "create_auditor_agent",
    "create_audit_task",
    "parse_audit_output",
    "create_cio_agent"
]
