"""
Programmer module for CoAct-1 Multi-Agent System

This module contains the Programmer agent implementation, including:
- ProgrammerTools: Toolkit for code execution and system operations
- Programmer agent creation logic
"""

import logging
from typing import List, Dict, Any, Optional
from agent import ComputerAgent
from computer import Computer


class ProgrammerTools:
    """A toolkit for the Programmer agent that provides code and system-level tools."""

    def __init__(self, computer: Computer):
        self._computer = computer

    async def run_command(self, command: str) -> str:
        """
        Runs a shell command and waits for output.
        Use this for commands where you need to see the results (ls, cat, grep, etc.).

        Args:
            command (str): The shell command to execute.

        Returns:
            str: The command output.
        """
        try:
            result = await self._computer.interface.run_command(command)
            output = f"Stdout:\n{result.stdout}\n"
            if result.stderr:
                output += f"Stderr:\n{result.stderr}\n"
            return output
        except Exception as e:
            return f"Error running command '{command}': {e}"

    async def run_command_in_background(self, command: str) -> str:
        """
        Runs a shell command in the background without waiting for output.
        Use this for opening applications (firefox, chrome, xterm, etc.).

        Args:
            command (str): The shell command to execute.

        Returns:
            str: Confirmation that the command was started in background.
        """
        # Run command in background with complete detachment
        background_command = f"setsid {command} >/dev/null 2>&1 &"

        # Create a task to run the command without blocking
        async def run_background_command():
            try:
                await self._computer.interface.run_command(background_command)
            except Exception:
                # Ignore errors since we're not waiting anyway
                pass

        # Start the task but don't wait for it
        import asyncio
        asyncio.create_task(run_background_command())

        # Return immediately - no output capture, no waiting
        return f"Command '{command}' started in background."

    async def list_dir(self, path: str) -> List[str]:
        """Lists the contents of a directory."""
        return await self._computer.interface.list_dir(path)

    async def read_file(self, path: str) -> str:
        """Reads the text content of a file."""
        return await self._computer.interface.read_text(path)

    async def write_file(self, path: str, content: str):
        """Writes text content to a file."""
        await self._computer.interface.write_text(path, content)

    async def venv_cmd(self, venv_name: str, command: str) -> str:
        """
        Execute a shell command in a virtual environment.

        Args:
            venv_name: Name of the virtual environment.
            command: Shell command to execute.

        Returns:
            The stdout and stderr from the command execution.
        """
        result = await self._computer.venv_cmd(venv_name, command)
        output = f"Stdout:\n{result.stdout}\n"
        if result.stderr:
            output += f"Stderr:\n{result.stderr}\n"
        return output

    async def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        return await self._computer.interface.file_exists(path)

    async def directory_exists(self, path: str) -> bool:
        """Check if a directory exists."""
        return await self._computer.interface.directory_exists(path)

    async def read_bytes(self, path: str, offset: int = 0, length: Optional[int] = None) -> bytes:
        """Read binary content from a file."""
        return await self._computer.interface.read_bytes(path, offset, length)

    async def write_bytes(self, path: str, content: bytes) -> None:
        """Write binary content to a file."""
        await self._computer.interface.write_bytes(path, content)

    async def delete_file(self, path: str) -> None:
        """Delete a file."""
        await self._computer.interface.delete_file(path)

    async def create_dir(self, path: str) -> None:
        """Create a directory."""
        await self._computer.interface.create_dir(path)

    async def delete_dir(self, path: str) -> None:
        """Delete a directory."""
        await self._computer.interface.delete_dir(path)

    async def get_file_size(self, path: str) -> int:
        """Get the size of a file in bytes."""
        return await self._computer.interface.get_file_size(path)

    async def copy_to_clipboard(self) -> str:
        """Copy content from clipboard."""
        return await self._computer.interface.copy_to_clipboard()

    async def set_clipboard(self, text: str) -> None:
        """Set clipboard content."""
        await self._computer.interface.set_clipboard(text)

    async def get_accessibility_tree(self) -> Dict:
        """Get accessibility tree for UI elements."""
        return await self._computer.interface.get_accessibility_tree()

    async def venv_install(self, venv_name: str, requirements: List[str]) -> str:
        """
        Install packages in a virtual environment.

        Args:
            venv_name: Name of the virtual environment.
            requirements: List of package names to install.

        Returns:
            Installation output.
        """
        await self._computer.venv_install(venv_name, requirements)
        return f"Installed packages {requirements} in virtual environment '{venv_name}'"


def create_programmer(programmer_model: str, programmer_tools: ProgrammerTools) -> ComputerAgent:
    """Creates and configures the Programmer agent."""
    instructions = open("agent_prompts/Programmer.txt", "r").read()

    # Gather all methods from the toolkit instance
    programmer_tool_methods = [
        programmer_tools.run_command,
        programmer_tools.run_command_in_background,
        programmer_tools.list_dir,
        programmer_tools.read_file,
        programmer_tools.write_file,
        programmer_tools.venv_cmd,
        programmer_tools.file_exists,
        programmer_tools.directory_exists,
        programmer_tools.read_bytes,
        programmer_tools.write_bytes,
        programmer_tools.delete_file,
        programmer_tools.create_dir,
        programmer_tools.delete_dir,
        programmer_tools.get_file_size,
        programmer_tools.copy_to_clipboard,
        programmer_tools.set_clipboard,
        programmer_tools.get_accessibility_tree,
        programmer_tools.venv_install,
    ]

    print(f"👨‍💻 [PROGRAMMER] Initializing with model: {programmer_model}")
    return ComputerAgent(
        model=programmer_model,
        tools=programmer_tool_methods,
        instructions=instructions,
        verbosity=logging.WARNING
    )
