"""
GUI Operator module for CoAct-1 Multi-Agent System

This module contains the GUI Operator agent implementation, including:
- GuiOperatorComputerProxy: Restricted proxy for GUI operations with OCR support
- GUI Operator agent creation logic
"""

import logging
from typing import Optional
from agent import ComputerAgent
from computer import Computer
from agent.callbacks.ocr_processor import OCRProcessorCallback


class GuiOperatorComputerProxy:
    """
    A proxy for the Computer object that exposes only GUI-related methods.
    This is necessary because the ComputerAgent has special handling for 'computer' tools,
    and we want to provide a restricted set of a computer's capabilities.
    """

    def __init__(self, computer: Computer, ocr_callback: Optional[OCRProcessorCallback] = None):
        # We need to hold a reference to the original computer object
        # and its interface to delegate the calls.
        self._computer_instance = computer
        self.interface = self._create_gui_interface_proxy(computer.interface)
        self.is_gui_proxy = True
        self.ocr_callback = ocr_callback

    def _create_gui_interface_proxy(self, real_interface):
        class GuiInterfaceProxy:
            """A proxy that exposes only the GUI-related methods of the real interface."""

            def __init__(self, interface):
                self._real_interface = interface

            # GUI Mouse Methods
            async def left_click(self, x: int, y: int, delay: Optional[float] = None): return await self._real_interface.left_click(x, y, delay)
            async def right_click(self, x: int, y: int, delay: Optional[float] = None): return await self._real_interface.right_click(x, y, delay)
            async def double_click(self, x: int, y: int, delay: Optional[float] = None): return await self._real_interface.double_click(x, y, delay)
            async def move_cursor(self, x: int, y: int, delay: Optional[float] = None): return await self._real_interface.move_cursor(x, y, delay)
            async def mouse_down(self, x: int, y: int, button: str = "left"): return await self._real_interface.mouse_down(x, y, button)
            async def mouse_up(self, x: int, y: int, button: str = "left"): return await self._real_interface.mouse_up(x, y, button)
            async def drag(self, path, button="left", duration=0.5): return await self._real_interface.drag(path, button, duration)

            # GUI Keyboard Methods
            async def type_text(self, text: str, delay: Optional[float] = None): return await self._real_interface.type_text(text, delay)
            async def press_key(self, key: str, delay: Optional[float] = None): return await self._real_interface.press_key(key, delay)
            async def hotkey(self, *keys: str, delay: Optional[float] = None): return await self._real_interface.hotkey(*keys, delay=delay)

            # GUI Screen Methods
            async def screenshot(self): return await self._real_interface.screenshot()
            async def get_screen_size(self): return await self._real_interface.get_screen_size()
            async def get_cursor_position(self): return await self._real_interface.get_cursor_position()
            async def scroll(self, x: int = 0, y: int = 0, scroll_x: int = 0, scroll_y: int = 0):
                """Handle scrolling with scroll amounts."""
                # Use scroll_down/scroll_up for vertical scrolling by amounts
                if scroll_y > 0:
                    # Scroll down by the specified amount
                    clicks = max(1, scroll_y // 100)  # Convert scroll amount to clicks
                    if hasattr(self._real_interface, 'scroll_down'):
                        return await self._real_interface.scroll_down(clicks)
                    else:
                        return await self._real_interface.scroll(x, y)
                elif scroll_y < 0:
                    # Scroll up by the specified amount
                    clicks = max(1, abs(scroll_y) // 100)  # Convert scroll amount to clicks
                    if hasattr(self._real_interface, 'scroll_up'):
                        return await self._real_interface.scroll_up(clicks)
                    else:
                        return await self._real_interface.scroll(x, y)
                else:
                    # No vertical scroll, just use coordinates
                    return await self._real_interface.scroll(x, y)
            async def scroll_down(self, clicks: int = 1, delay: Optional[float] = None): return await self._real_interface.scroll_down(clicks, delay)
            async def scroll_up(self, clicks: int = 1, delay: Optional[float] = None): return await self._real_interface.scroll_up(clicks, delay)

            # GUI Keyboard Methods (additional)
            async def key_down(self, key: str, delay: Optional[float] = None): return await self._real_interface.key_down(key, delay)
            async def key_up(self, key: str, delay: Optional[float] = None): return await self._real_interface.key_up(key, delay)

            # GUI Coordinate Methods
            async def to_screen_coordinates(self, x: float, y: float): return await self._real_interface.to_screen_coordinates(x, y)
            async def to_screenshot_coordinates(self, x: float, y: float): return await self._real_interface.to_screenshot_coordinates(x, y)

            # GUI Wait Methods
            async def wait_for_ready(self, timeout: int = 60): return await self._real_interface.wait_for_ready(timeout)

        return GuiInterfaceProxy(real_interface)

    async def click_ocr_text(self, ocr_id: int) -> str:
        """
        Click on an OCR-detected text element by ID.

        Args:
            ocr_id: The ID of the OCR text element to click

        Returns:
            Success message or error message
        """
        if not self.ocr_callback:
            return f"Error: OCR callback not available"

        bbox = self.ocr_callback.get_ocr_bbox(ocr_id)
        if bbox is None:
            return f"Error: OCR ID {ocr_id} not found"

        x1, y1, x2, y2 = bbox
        # Calculate center coordinates
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        try:
            # Perform the click at center coordinates
            await self.interface.left_click(center_x, center_y)
            content = self.ocr_callback.get_ocr_content(ocr_id) or f"ID {ocr_id}"
            return f"Successfully clicked on OCR text element: '{content}' at ({center_x}, {center_y})"
        except Exception as e:
            return f"Error clicking OCR text element {ocr_id}: {e}"

    async def right_click_ocr_text(self, ocr_id: int) -> str:
        """
        Right-click on an OCR-detected text element by ID.

        Args:
            ocr_id: The ID of the OCR text element to right-click

        Returns:
            Success message or error message
        """
        if not self.ocr_callback:
            return f"Error: OCR callback not available"

        bbox = self.ocr_callback.get_ocr_bbox(ocr_id)
        if bbox is None:
            return f"Error: OCR ID {ocr_id} not found"

        x1, y1, x2, y2 = bbox
        # Calculate center coordinates
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        try:
            # Perform the right-click at center coordinates
            await self.interface.right_click(center_x, center_y)
            content = self.ocr_callback.get_ocr_content(ocr_id) or f"ID {ocr_id}"
            return f"Successfully right-clicked on OCR text element: '{content}' at ({center_x}, {center_y})"
        except Exception as e:
            return f"Error right-clicking OCR text element {ocr_id}: {e}"

    async def double_click_ocr_text(self, ocr_id: int) -> str:
        """
        Double-click on an OCR-detected text element by ID.

        Args:
            ocr_id: The ID of the OCR text element to double-click

        Returns:
            Success message or error message
        """
        if not self.ocr_callback:
            return f"Error: OCR callback not available"

        bbox = self.ocr_callback.get_ocr_bbox(ocr_id)
        if bbox is None:
            return f"Error: OCR ID {ocr_id} not found"

        x1, y1, x2, y2 = bbox
        # Calculate center coordinates
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        try:
            # Perform the double-click at center coordinates
            await self.interface.double_click(center_x, center_y)
            content = self.ocr_callback.get_ocr_content(ocr_id) or f"ID {ocr_id}"
            return f"Successfully double-clicked on OCR text element: '{content}' at ({center_x}, {center_y})"
        except Exception as e:
            return f"Error double-clicking OCR text element {ocr_id}: {e}"

    # The ComputerAgent's handler needs to check if the computer is initialized.
    @property
    def _initialized(self):
        return self._computer_instance._initialized


def create_gui_operator(gui_operator_model: str, gui_operator_computer: Computer, ocr_broadcast_callback=None, grounding_broadcast_callback=None, function_call_broadcast_callback=None, screenshot_broadcast_callback=None) -> ComputerAgent:
    """Creates and configures the GUI Operator agent with OCR support."""
    instructions = open("agent_prompts/GUIOperator.txt", "r").read()

    # Create OCR callback for preprocessing screenshots
    ocr_callback = OCRProcessorCallback(device="cuda", broadcast_callback=ocr_broadcast_callback)

    # Create the GUI computer proxy with OCR callback
    gui_proxy = GuiOperatorComputerProxy(gui_operator_computer, ocr_callback)

    # Gather all methods from the proxy instance to pass to the agent
    gui_operator_tool_methods = [
        gui_proxy.click_ocr_text,      # OCR text clicking function
        gui_proxy.right_click_ocr_text,  # OCR text right-clicking function
        gui_proxy.double_click_ocr_text, # OCR text double-clicking function
        gui_proxy,  # The computer proxy itself for GUI operations
    ]

    # Prepare callbacks list
    callbacks = [ocr_callback]  # Always include OCR callback
    if screenshot_broadcast_callback:
        from agent.callbacks import ScreenshotBroadcastCallback
        callbacks.append(ScreenshotBroadcastCallback(screenshot_broadcast_callback, "GUIOperator"))

    print(f"🎭 [GUI OPERATOR] Initializing with model: {gui_operator_model} (with OCR support)")
    return ComputerAgent(
        model=gui_operator_model,
        tools=gui_operator_tool_methods,
        grounding_broadcast_callback=grounding_broadcast_callback,
        function_call_broadcast_callback=function_call_broadcast_callback,
        callbacks=callbacks,
        instructions=instructions,
        verbosity=logging.WARNING,
        trust_remote_code=True,
        only_n_most_recent_images=2,
        screenshot_delay=1.0,  # Wait 1 second after actions before screenshot
    )
