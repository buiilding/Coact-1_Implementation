#!/usr/bin/env python3
"""
CoAct-1 Main Runner

This script runs the full CoAct-1 multi-agent system using the CoAct1 class.
"""

import asyncio
import os
import logging
import argparse

# Import CoAct-1 components
from coact_1 import CoAct1
from computer import Computer, VMProviderType

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the CoAct-1 example."""
    print("🚀 Starting CoAct-1 Example")
    print("=" * 60)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run CoAct-1 Multi-Agent System')
    parser.add_argument('-m', '--message', type=str, required=True,
                       help='The user message/task to execute')
    args = parser.parse_args()

    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY environment variable not set.")
        return

    computer_instance = None
    try:
        print("📦 Setting up Docker computer...")
        computer_instance = Computer(
            os_type="linux",
            provider_type=VMProviderType.DOCKER,
            name="cua-coact1-demo",
            image="trycua/cua-ubuntu:latest",
            port=6091,
        )
        await computer_instance.run()

        # Define model names for each agent
        orchestrator_model_name = "gemini/gemini-2.5-flash"
        programmer_model_name = "gemini/gemini-2.5-flash"
        gui_operator_model_name = "huggingface-local/OpenGVLab/InternVL3_5-4B+gemini/gemini-2.5-flash"

        coact_system = CoAct1(
            computer=computer_instance,
            orchestrator_model=orchestrator_model_name,
            programmer_model=programmer_model_name,
            gui_operator_model=gui_operator_model_name,
            websocket_port=8765,
        )

        # Use the task from command line arguments
        task = args.message
        print(f"🎯 Task: {task}")

        await coact_system.run(task)

    except Exception as e:
        logger.error(f"❌ Error running example: {e}")
        raise
    finally:
        if computer_instance:
            await computer_instance.stop()
            print("\n🧹 Computer connection closed")

        # Clean up CoAct-1 WebSocket server
        if 'coact_system' in locals() and coact_system:
            try:
                await coact_system.stop_websocket_server()
            except Exception as e:
                print(f"⚠️ Error stopping WebSocket server: {e}")


if __name__ == "__main__":
    asyncio.run(main())
