#!/usr/bin/env python3
"""
CUA Example: CoAct-1 Multi-Agent System

This example implements the CoAct-1 architecture, a multi-agent system
for computer automation, as described in the paper.

The system consists of three agents:
1. Orchestrator: A high-level planner that decomposes tasks and delegates.
2. Programmer: An agent that writes and executes Python or Bash scripts.
3. GUI Operator: A vision-language agent for GUI manipulation.
"""

import asyncio
import os
import sys
import logging
import json
from typing import List, Dict, Any, Optional

# Import CUA components
from agent import ComputerAgent
from computer import Computer, VMProviderType
# from agent.callbacks import AsyncCallbackHandler
# from agent.computers.base import AsyncComputerHandler
from agent.computers.cua import cuaComputerHandler

# Import agent modules
from orchestrator import OrchestratorTools, create_orchestrator
from Programmer import ProgrammerTools, create_programmer
from GUIOperator import create_gui_operator

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# --- CoAct-1 System ---

class CoAct1:
    """
    Implements the CoAct-1 multi-agent system.
    """
    def __init__(self, computer: Computer, orchestrator_model: str, programmer_model: str, gui_operator_model: str):
        self.computer = computer
        
        # Store model names
        self.orchestrator_model = orchestrator_model
        self.programmer_model = programmer_model
        self.gui_operator_model = gui_operator_model

        # The cuaComputerHandler is the component that translates agent actions
        # into calls on the computer interface. We can reuse it.
        computer_handler = cuaComputerHandler(computer)

        print("🏗️  [COACT-1] Initializing multi-agent system...")
        print(f"   🤖 Orchestrator: {orchestrator_model}")
        print(f"   👨‍💻 Programmer: {programmer_model}")
        print(f"   🎭 GUI Operator: {gui_operator_model}")

        # Create specialized toolkits for each agent
        self.orchestrator_tools = OrchestratorTools(computer_handler)
        self.programmer_tools = ProgrammerTools(computer)

        self.orchestrator = create_orchestrator(orchestrator_model, self.orchestrator_tools)
        self.programmer = create_programmer(programmer_model, self.programmer_tools)
        self.gui_operator = create_gui_operator(gui_operator_model, computer)

        print("✅ [COACT-1] All agents initialized successfully!")


    def _extract_sub_agent_final_message(self, history: List[Dict[str, Any]]) -> str:
        """Extract the final message from a sub-agent's conversation history."""
        # Look for the last assistant message that doesn't contain function calls
        for message in reversed(history):
            if message.get("role") == "assistant":
                content = message.get("content", "")
                # Check if this message contains function calls
                has_function_calls = False
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "tool_use" or item.get("type") == "function_call":
                            has_function_calls = True
                            break
                elif "function_call" in str(content) or "tool_use" in str(content):
                    has_function_calls = True

                # If no function calls, this is the final completion message
                if not has_function_calls and content:
                    return str(content)

        # Fallback: return the last message content
        return "Sub-agent completed task (no explicit completion message found)"

    async def run(self, task: str):
        """Runs the CoAct-1 agent system on a given task."""
        print(f"\n🎬 [COACT-1 RUN] Starting task: '{task}'")

        # Take initial screenshot for orchestrator context
        print("📸 Taking initial screenshot for orchestrator...")
        # Initialize the computer handler if needed
        if hasattr(self.orchestrator_tools._handler, '_initialize'):
            await self.orchestrator_tools._handler._initialize()
        # Get the screenshot from the computer handler
        initial_screenshot_b64 = await self.orchestrator_tools._handler.screenshot()
        print("   ✅ Initial screenshot taken")

        # Create initial user message with task and screenshot
        initial_content = [
            {"type": "text", "text": f"{task}\n\nHere is the current screen. What is the next subtask?"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{initial_screenshot_b64}"}}
        ]

        orchestrator_history: List[Dict[str, Any]] = [{"role": "user", "content": initial_content}]
    
        for i in range(10): # Max 10 steps
            print(f"\n--- Step {i+1} ---")

            # Take current screenshot for orchestrator context
            print("📸 Taking current screenshot for orchestrator...")
            try:
                current_screenshot_b64 = await self.orchestrator_tools._handler.screenshot()
                print("   ✅ Current screenshot taken")

                orchestrator_history.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is the next subtask based on the current progress? (or you can call task_completed)"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{current_screenshot_b64}"}}
                    ]
                })
            except Exception as e:
                print(f"   ⚠️ Failed to take screenshot: {e}")
                orchestrator_history.append({
                    "role": "user",
                    "content": "What is the next subtask based on the current progress? (or you can call task_completed)"
                })

            # 2. Call Orchestrator
            print("🤔 Orchestrator is planning...")
            delegation = None
            async for result in self.orchestrator.run(orchestrator_history):
                for item in result.get("output", []):
                    if item.get("type") == "function_call":
                        delegation = item
                        break
                if delegation:
                    break
            
            if not delegation:
                print("🛑 Orchestrator did not delegate a task. Ending.")
                break

            # Handle both direct format and nested function format
            function_info = delegation.get("function", delegation)
            tool_name = function_info.get("name")
            arguments = function_info.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            subtask = arguments.get("subtask", "")

            orchestrator_history.append(delegation) # Add delegation to history

            if tool_name == "task_completed":
                print("✅ Task completed!")
                break
            
            sub_agent = None
            if tool_name == "delegate_to_programmer":
                print(f"👨‍💻 Delegating to Programmer: {subtask}")
                sub_agent = self.programmer
            elif tool_name == "delegate_to_gui_operator":
                print(f"🖱️ Delegating to GUI Operator: {subtask}")
                sub_agent = self.gui_operator
            else:
                print(f"❓ Unknown delegation: {tool_name}")
                continue

            # 3. Run sub-agent with the task and current image context
            # Get the current screenshot from orchestrator history
            current_image_b64 = get_last_image_b64(orchestrator_history)

            # Create sub-agent history starting with the subtask
            if current_image_b64:
                # Include the image directly in the subtask message
                sub_agent_history = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{subtask}\n\nHere is the current screen state:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{current_image_b64}"}}
                    ]
                }]
                print("   🖼️ Provided image context to sub-agent")
            else:
                sub_agent_history = [{
                    "role": "user",
                    "content": subtask
                }]

            async for result in sub_agent.run(sub_agent_history):
                sub_agent_history.extend(result.get("output", []))

            # 4. Get the latest screenshot from the sub-agent's history
            final_screenshot_b64 = get_last_image_b64(sub_agent_history)

            # 5. Extract the sub-agent's final completion message
            print("📝 Extracting sub-agent completion message...")
            final_message = self._extract_sub_agent_final_message(sub_agent_history)
            print(f"Final message: {final_message}")

            # Create a message with the sub-agent's final message and the current screenshot for orchestrator evaluation
            orchestrator_result_content = [
                {"type": "text", "text": f"Sub-agent completed task.\n\nFinal Message: {final_message}\n\nHere is the current screen state. Evaluate whether the sub-task was successful and determine the next action."}
            ]

            if final_screenshot_b64:
                orchestrator_result_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{final_screenshot_b64}"}
                })

            orchestrator_history.append({
                "type": "function_call_output",
                "call_id": delegation.get("call_id", f"call_{hash(str(delegation))}"),
                "output": orchestrator_result_content,
            })

def get_last_image_b64(messages: List[Dict[str, Any]]) -> Optional[str]:
    """Get the last image from a list of messages, checking both user messages and tool outputs."""
    for message in reversed(messages):
        # Check user messages with content lists
        if message.get("role") == "user" and isinstance(message.get("content"), list):
            for content_item in reversed(message["content"]):
                if content_item.get("type") == "image_url":
                    image_url = content_item.get("image_url", {}).get("url", "")
                    if image_url.startswith("data:image/png;base64,"):
                        return image_url.split(",", 1)[1]
        
        # Check computer call outputs
        elif message.get("type") == "computer_call_output" and isinstance(message.get("output"), dict):
            output = message["output"]
            if output.get("type") == "input_image":
                image_url = output.get("image_url", "")
                if image_url.startswith("data:image/png;base64,"):
                    return image_url.split(",", 1)[1]

        # Check function call outputs (for orchestrator results with multimodal content)
        elif message.get("type") == "function_call_output" and isinstance(message.get("output"), list):
            for content_item in reversed(message["output"]):
                if content_item.get("type") == "image_url":
                    image_url = content_item.get("image_url", {}).get("url", "")
                if image_url.startswith("data:image/png;base64,"):
                    return image_url.split(",", 1)[1]
    return None