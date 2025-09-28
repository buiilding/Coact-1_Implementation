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
import websockets
import functools
from typing import List, Dict, Any, Optional, Set, Tuple

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
    def __init__(self, computer: Computer, orchestrator_model: str, programmer_model: str, gui_operator_model: str, websocket_port: int = 8765):
        self.computer = computer

        # Store model names
        self.orchestrator_model = orchestrator_model
        self.programmer_model = programmer_model
        self.gui_operator_model = gui_operator_model

        # WebSocket server for real-time updates
        self.websocket_port = websocket_port
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.websocket_server = None

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

        self.orchestrator = create_orchestrator(orchestrator_model, self.orchestrator_tools, self.broadcast_function_call)
        self.programmer = create_programmer(programmer_model, self.programmer_tools, self.broadcast_screenshot, self.broadcast_function_call)
        self.gui_operator = create_gui_operator(
            gui_operator_model,
            computer,
            self.broadcast_ocr_results,
            self.broadcast_grounding_call,
            self.broadcast_function_call,
            self.broadcast_screenshot
        )

        print("✅ [COACT-1] All agents initialized successfully!")

        # Start WebSocket server for real-time updates
        self.start_websocket_server()

    async def websocket_handler(self, websocket):
        """Handle WebSocket connections for real-time updates."""
        print(f"📡 New WebSocket connection from {websocket.remote_address}")
        self.websocket_clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.websocket_clients.remove(websocket)
            print(f"📡 WebSocket connection closed for {websocket.remote_address}")

            # Broadcast UI reset when connection is lost
            if not self.websocket_clients:  # Only reset if no clients remain
                await self.broadcast_event("ui_reset", {
                    "reason": "websocket_disconnected",
                    "message": "Connection lost - resetting UI to initial state",
                    "timestamp": asyncio.get_event_loop().time()
                })
                print("🔄 Broadcasted UI reset due to WebSocket disconnection")

    def start_websocket_server(self):
        """Initialize the WebSocket server for real-time updates."""
        print(f"🚀 Initializing WebSocket server on port {self.websocket_port}")

        # Use functools.partial to bind the instance method
        handler = functools.partial(self.websocket_handler)

        self.websocket_server = websockets.serve(
            handler,
            "localhost",
            self.websocket_port
        )

    async def start_websocket_server_async(self):
        """Start the WebSocket server asynchronously."""
        if self.websocket_server:
            # Start the WebSocket server
            await self.websocket_server.__aenter__()
            print(f"✅ WebSocket server started on port {self.websocket_port}")

    async def stop_websocket_server(self):
        """Stop the WebSocket server."""
        if self.websocket_server:
            try:
                await self.websocket_server.__aexit__(None, None, None)
            except Exception as e:
                print(f"⚠️ Error stopping WebSocket server: {e}")

        # Broadcast UI reset before closing connections
        await self.broadcast_event("ui_reset", {
            "reason": "server_shutdown",
            "message": "Server shutting down - resetting UI to initial state",
            "timestamp": asyncio.get_event_loop().time()
        })
        print("🔄 Broadcasted UI reset due to server shutdown")

        # Close all client connections
        for client in self.websocket_clients.copy():
            try:
                await client.close()
            except Exception:
                pass

        self.websocket_clients.clear()
        print("🧹 WebSocket server stopped")

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected WebSocket clients."""
        print(f"📡 Broadcasting event: {event_type} to {len(self.websocket_clients)} clients")
        if not self.websocket_clients:
            print("⚠️ No WebSocket clients connected")
            return

        message = {
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }

        # Convert message to JSON
        json_message = json.dumps(message)

        # Send to all connected clients
        disconnected_clients = set()
        for client in self.websocket_clients:
            try:
                await client.send(json_message)
                print(f"✅ Sent to client: {client.remote_address}")
            except Exception as e:
                print(f"⚠️ Failed to send message to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            self.websocket_clients.discard(client)

    async def broadcast_screenshot(self, screenshot_b64: str, screenshot_type: str = "current"):
        """Broadcast screenshot data to UI."""
        await self.broadcast_event("screenshot_update", {
            "screenshot_type": screenshot_type,
            "screenshot_data": screenshot_b64,
            "timestamp": asyncio.get_event_loop().time()
        })

    async def broadcast_ocr_results(self, ocr_results: List[Dict[str, Any]]):
        """Broadcast OCR results to UI."""
        await self.broadcast_event("ocr_update", {
            "ocr_results": ocr_results,
            "timestamp": asyncio.get_event_loop().time()
        })

    async def broadcast_grounding_call(self, model_name: str, instruction: str, coordinates: Optional[Tuple[int, int]], confidence: float, processing_time: float):
        """Broadcast grounding model call results to UI."""
        # Set grounding model as processing when starting, idle when complete
        if coordinates is None:
            # Starting grounding
            await self.broadcast_event("agent_state", {
                "orchestrator": "idle",
                "programmer": "idle",
                "gui_operator": "idle",
                "grounding_model": "processing"
            })
        else:
            # Grounding completed, set GUI operator back to processing
            await self.broadcast_event("agent_state", {
                "orchestrator": "idle",
                "programmer": "idle",
                "gui_operator": "processing",
                "grounding_model": "idle"
            })

        await self.broadcast_event("grounding_update", {
            "model_name": model_name,
            "instruction": instruction,
            "coordinates": coordinates,
            "confidence": confidence,
            "processing_time": processing_time,
            "timestamp": asyncio.get_event_loop().time()
        })

    async def broadcast_function_call(self, agent_name: str, function_name: str, parameters: Dict[str, Any]):
        """Broadcast function call details to UI."""
        await self.broadcast_event("function_call_update", {
            "agent_name": agent_name,
            "function_name": function_name,
            "parameters": parameters,
            "timestamp": asyncio.get_event_loop().time()
        })


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

        # Start WebSocket server for real-time updates
        await self.start_websocket_server_async()

        # Wait a moment for frontend to connect
        await asyncio.sleep(2)

        # Broadcast the original user task assigned to Orchestrator
        print(f"📡 Broadcasting user_task_started: {task}")
        await self.broadcast_event("user_task_started", {
            "task": task,
            "assigned_to": "Orchestrator"
        })

        # Set orchestrator as processing
        await self.broadcast_event("agent_state", {
            "orchestrator": "processing",
            "programmer": "idle",
            "gui_operator": "idle",
            "grounding_model": "idle"
        })
        if hasattr(self.orchestrator_tools._handler, '_initialize'):
            await self.orchestrator_tools._handler._initialize()

        orchestrator_history: List[Dict[str, Any]] = []
    
        for i in range(10): # Max 10 steps
            print(f"\n--- Step {i+1} ---")

            # Take current screenshot for orchestrator context
            print("📸 Taking current screenshot for orchestrator...")
            try:
                current_screenshot_b64 = await self.orchestrator_tools._handler.screenshot()
                print("   ✅ Current screenshot taken")

                # Broadcast current screenshot to UI
                await self.broadcast_screenshot(current_screenshot_b64, "current")

                orchestrator_history.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{task}\n"},
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
                # Set all agents to idle
                await self.broadcast_event("agent_state", {
                    "orchestrator": "idle",
                    "programmer": "idle",
                    "gui_operator": "idle",
                    "grounding_model": "idle"
                })
                # Broadcast task completion event
                await self.broadcast_event("task_completed", {
                    "task": task,
                    "step": i + 1
                })
                break

            sub_agent = None
            target_agent = ""
            if tool_name == "delegate_to_programmer":
                print(f"👨‍💻 Delegating to Programmer: {subtask}")
                sub_agent = self.programmer
                target_agent = "Programmer"
                # Set programmer as processing, others idle
                await self.broadcast_event("agent_state", {
                    "orchestrator": "idle",
                    "programmer": "processing",
                    "gui_operator": "idle",
                    "grounding_model": "idle"
                })
            elif tool_name == "delegate_to_gui_operator":
                print(f"🖱️ Delegating to GUI Operator: {subtask}")
                sub_agent = self.gui_operator
                target_agent = "GUIOperator"
                # Set GUI operator as processing, others idle
                await self.broadcast_event("agent_state", {
                    "orchestrator": "idle",
                    "programmer": "idle",
                    "gui_operator": "processing",
                    "grounding_model": "idle"
                })
            else:
                print(f"❓ Unknown delegation: {tool_name}")
                continue

            # Broadcast task delegation event with the actual message sent to agent
            delegation_message = f"{target_agent}: {subtask}"
            print(f"🔄 Broadcasting task_delegated: {delegation_message} (step {i+1})")

            await self.broadcast_event("task_delegated", {
                "task_id": f"sub-{i+1}",
                "description": delegation_message,
                "assigned_to": target_agent,
                "parent_task": task,
                "step": i + 1
            })
            
        
            # Include the image directly in the subtask message
            sub_agent_history = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{subtask}\n\nHere is the current screen state:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{current_screenshot_b64}"}}
                ]
            }]
            print("   🖼️ Provided image context to sub-agent")
           

            async for result in sub_agent.run(sub_agent_history):
                sub_agent_history.extend(result.get("output", []))

            final_screenshot_b64 = await self.orchestrator_tools._handler.screenshot()

            # Broadcast final screenshot as previous screenshot for next iteration
            await self.broadcast_screenshot(final_screenshot_b64, "previous")

            # 5. Extract the sub-agent's final completion message
            print("📝 Extracting sub-agent completion message...")
            final_message = self._extract_sub_agent_final_message(sub_agent_history)
            print(f"Final message: {final_message}")

            # Set orchestrator back to processing for next iteration
            await self.broadcast_event("agent_state", {
                "orchestrator": "processing",
                "programmer": "idle",
                "gui_operator": "idle",
                "grounding_model": "idle"
            })

            # Broadcast sub-agent completion event
            await self.broadcast_event("subtask_completed", {
                "task_id": f"sub-{i+1}",
                "description": subtask,
                "assigned_to": target_agent,
                "result": final_message,
                "step": i + 1
            })

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