"""
Orchestrator module for CoAct-1 Multi-Agent System

This module contains the Orchestrator agent implementation, including:
- OrchestratorTools: Toolkit for observation and planning
- Delegate functions for task delegation
- Orchestrator agent creation logic
"""

import logging
from typing import Dict, Any, Tuple
from agent import ComputerAgent
from agent.computers.cua import cuaComputerHandler


class OrchestratorTools:
    """A toolkit for the Orchestrator agent that provides observation tools."""

    def __init__(self, computer_handler: 'cuaComputerHandler'):
        self._handler = computer_handler

    async def get_environment(self) -> str:
        """Get the current environment type (e.g., 'linux', 'windows')."""
        return await self._handler.get_environment()

    async def get_dimensions(self) -> Tuple[int, int]:
        """Get screen dimensions as (width, height)."""
        return await self._handler.get_dimensions()

    async def get_current_url(self) -> str:
        """Get current URL (for browser environments)."""
        return await self._handler.get_current_url()

    async def screenshot(self) -> str:
        """Take a screenshot for task analysis and planning."""
        return await self._handler.screenshot()


# --- Orchestrator Agent Tools ---

def delegate_to_programmer(subtask: str):
    """Delegates a subtask to the programmer agent for code-based execution."""
    pass


def delegate_to_gui_operator(subtask: str):
    """Delegates a subtask to the GUI operator for visual, UI-based execution."""
    pass


def task_completed():
    """Signals that the overall task is completed."""
    pass


def create_orchestrator(orchestrator_model: str, orchestrator_tools: OrchestratorTools, function_call_broadcast_callback=None) -> ComputerAgent:
    """Creates and configures the Orchestrator agent."""
    instructions = open("agent_prompts/Orchestrator.txt", "r").read()

    # Gather all methods from the toolkit instance to pass to the agent
    orchestrator_tool_methods = [
        orchestrator_tools.get_environment,
        orchestrator_tools.get_dimensions,
        orchestrator_tools.get_current_url,
        orchestrator_tools.screenshot,
        delegate_to_programmer,
        delegate_to_gui_operator,
        task_completed
    ]

    print(f"🎯 [ORCHESTRATOR] Initializing with model: {orchestrator_model}")
    return ComputerAgent(
        model=orchestrator_model,
        tools=orchestrator_tool_methods,
        function_call_broadcast_callback=function_call_broadcast_callback,
        instructions=instructions,
        verbosity=logging.WARNING
    )
