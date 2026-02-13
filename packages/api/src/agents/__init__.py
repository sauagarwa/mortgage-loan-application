"""
AI/MCP Agent framework for mortgage risk assessment.

Provides base agent class and individual dimension agents that analyze
mortgage applications using LLM-powered reasoning.
"""

from .base import BaseAgent, AgentResult

__all__ = ["BaseAgent", "AgentResult"]
