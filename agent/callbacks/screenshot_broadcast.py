"""
Screenshot Broadcast Callback

This callback broadcasts screenshots taken during agent execution to the UI via WebSocket.
"""

import asyncio
from typing import Union, Callable, Awaitable, Optional
from .base import AsyncCallbackHandler


class ScreenshotBroadcastCallback(AsyncCallbackHandler):
    """
    Callback that broadcasts screenshots to the UI via WebSocket during agent execution.
    """

    def __init__(self, broadcast_callback: Callable[[str, str], Awaitable[None]], agent_name: str = "SubAgent"):
        """
        Initialize the screenshot broadcast callback.

        Args:
            broadcast_callback: Async function that takes (screenshot_b64, screenshot_type) and broadcasts it
            agent_name: Name of the agent for identification in broadcasts
        """
        self.broadcast_callback = broadcast_callback
        self.agent_name = agent_name

    async def on_screenshot(self, screenshot: Union[str, bytes], name: str = "screenshot") -> None:
        """
        Called when a screenshot is taken during agent execution.

        Args:
            screenshot: The screenshot image (base64 string or bytes)
            name: The name/type of the screenshot
        """
        try:
            # Convert bytes to base64 string if needed
            if isinstance(screenshot, bytes):
                import base64
                screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
            else:
                screenshot_b64 = screenshot

            # Broadcast the screenshot with agent context
            await self.broadcast_callback(screenshot_b64, f"{self.agent_name.lower()}_realtime")

            print(f"📡 [{self.agent_name}] Broadcasted real-time screenshot ({name})")

        except Exception as e:
            print(f"⚠️ [{self.agent_name}] Failed to broadcast screenshot: {e}")
