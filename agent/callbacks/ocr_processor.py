"""
OCR Processor callback for GUI Operator.

Performs OCR on screenshots before LLM processing and provides text element detection
for efficient GUI interaction.
"""

import base64
import io
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image

from .base import AsyncCallbackHandler


def get_rapid_ocr_engine(device: str = "cpu"):
    """
    Initialize RapidOCR engine.

    Args:
        device: Device to use ("cpu" or "cuda")

    Returns:
        RapidOCR engine instance
    """
    params = {
        "EngineConfig.onnxruntime.use_cuda": device == "cuda",
    }
    from rapidocr import RapidOCR
    engine = RapidOCR(params=params)
    return engine


def check_ocr_result(result, text_threshold=0.9):
    """
    Process OCR results from RapidOCR.

    Args:
        result: OCR result from RapidOCR
        text_threshold: Minimum confidence score for text detection

    Returns:
        Tuple of (text_list, bbox_list) where bbox is (x1, y1, x2, y2)
    """
    if result is None:
        return [], []

    text = []
    bb = []

    if hasattr(result, 'txts') and result.txts is not None:
        for txt, score, box in zip(result.txts, result.scores, result.boxes):
            if score > text_threshold:
                text.append(txt)

                x_coords = [p[0] for p in box]
                y_coords = [p[1] for p in box]
                x1 = int(min(x_coords))
                y1 = int(min(y_coords))
                x2 = int(max(x_coords))
                y2 = int(max(y_coords))

                bb.append((x1, y1, x2, y2))

    return text, bb


class OCRProcessorCallback(AsyncCallbackHandler):
    """
    Callback that performs OCR on screenshots and provides text element detection
    for GUI interaction.

    Stores OCR results mapping IDs to bounding box coordinates for efficient
    text element clicking.
    """

    def __init__(self, device: str = "cpu"):
        """
        Initialize OCR processor callback.

        Args:
            device: Device for OCR engine ("cpu" or "cuda")
        """
        self.device = device
        self.ocr_engine = None
        self.ocr_results = {}  # Map OCR ID -> (content, bbox)

    async def _initialize_ocr_engine(self):
        """Lazy initialization of OCR engine."""
        if self.ocr_engine is None:
            self.ocr_engine = get_rapid_ocr_engine(device=self.device)

    def _extract_latest_screenshot(self, messages: List[Dict[str, Any]]) -> Optional[Image.Image]:
        """
        Extract the latest screenshot from messages.

        Args:
            messages: List of message dictionaries

        Returns:
            PIL Image of the latest screenshot, or None if not found
        """
        for message in reversed(messages):
            # Check user messages with content lists
            if message.get("role") == "user" and isinstance(message.get("content"), list):
                for content_item in reversed(message["content"]):
                    if content_item.get("type") == "image_url":
                        image_url = content_item.get("image_url", {}).get("url", "")
                        if image_url.startswith("data:image/png;base64,"):
                            base64_data = image_url.split(",", 1)[1]
                            try:
                                image_bytes = base64.b64decode(base64_data)
                                return Image.open(io.BytesIO(image_bytes))
                            except Exception:
                                continue

            # Check computer call outputs
            elif message.get("type") == "computer_call_output" and isinstance(message.get("output"), dict):
                output = message["output"]
                if output.get("type") == "input_image":
                    image_url = output.get("image_url", "")
                    if image_url.startswith("data:image/png;base64,"):
                        base64_data = image_url.split(",", 1)[1]
                        try:
                            image_bytes = base64.b64decode(base64_data)
                            return Image.open(io.BytesIO(image_bytes))
                        except Exception:
                            continue

        return None

    async def _perform_ocr(self, image: Image.Image) -> Dict[int, Tuple[str, Tuple[int, int, int, int]]]:
        """
        Perform OCR on an image and return results.

        Args:
            image: PIL Image to process

        Returns:
            Dict mapping ID to (content, bbox) tuples
        """
        await self._initialize_ocr_engine()

        # Convert image to RGB and prepare for OCR
        image_rgb = image.convert('RGB')
        buffer = io.BytesIO()
        image_rgb.save(buffer, format='PNG')
        image_rgb_bytes = buffer.getvalue()

        # Perform OCR
        try:
            result = self.ocr_engine(image_rgb_bytes)
            text_list, bbox_list = check_ocr_result(result)

            # Create ID -> (content, bbox) mapping
            ocr_results = {}
            for i, (content, bbox) in enumerate(zip(text_list, bbox_list)):
                ocr_results[i] = (content, bbox)

            return ocr_results

        except Exception as e:
            print(f"⚠️ OCR processing failed: {e}")
            return {}

    def _format_ocr_text(self) -> str:
        """
        Format OCR results for inclusion in LLM prompt.

        Returns:
            Formatted string of OCR text elements
        """
        if not self.ocr_results:
            return "OCR-DETECTED TEXT ELEMENTS: None found"

        lines = ["OCR-DETECTED TEXT ELEMENTS:"]
        for ocr_id, (content, _) in self.ocr_results.items():
            lines.append(f"ID {ocr_id}: \"{content}\"")

        return "\n".join(lines)

    def _inject_ocr_into_messages(self, messages: List[Dict[str, Any]], ocr_text: str) -> List[Dict[str, Any]]:
        """
        Inject OCR text into the first user message, placing it after the latest image.

        Args:
            messages: Original messages
            ocr_text: Formatted OCR text to inject

        Returns:
            Modified messages with OCR text injected
        """
        modified_messages = []

        for message in messages:
            if message.get("role") == "user" and isinstance(message.get("content"), list):
                # Count total images in the message
                total_images = sum(1 for item in message["content"] if item.get("type") == "image_url")

                new_content = []
                ocr_injected = False
                images_seen = 0

                # Process content items, injecting OCR after the last image
                for content_item in message["content"]:
                    new_content.append(content_item)

                    if content_item.get("type") == "image_url":
                        images_seen += 1

                        # If this is the last image and we haven't injected OCR yet, inject it after
                        if images_seen == total_images and not ocr_injected:
                            new_content.append({
                                "type": "text",
                                "text": f"\n{ocr_text}\n"
                            })
                            ocr_injected = True

                # If no images found, inject at the beginning (fallback for initial messages)
                if not ocr_injected:
                    # Find first text item and prepend OCR
                    for i, content_item in enumerate(new_content):
                        if content_item.get("type") == "text":
                            new_content[i] = {
                                "type": "text",
                                "text": f"{ocr_text}\n\n{content_item['text']}"
                            }
                            ocr_injected = True
                            break

                modified_message = message.copy()
                modified_message["content"] = new_content
                modified_messages.append(modified_message)
            else:
                modified_messages.append(message)

        return modified_messages

    async def on_llm_start(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform OCR on the latest screenshot and inject results into messages.

        Args:
            messages: List of message dictionaries to preprocess

        Returns:
            List of preprocessed message dictionaries with OCR results
        """
        # Extract latest screenshot
        screenshot = self._extract_latest_screenshot(messages)
        if screenshot is None:
            print("⚠️ No screenshot found for OCR processing")
            return messages

        # Perform OCR
        print("🔍 Performing OCR on screenshot...")
        self.ocr_results = await self._perform_ocr(screenshot)
        print(f"✅ OCR completed: found {len(self.ocr_results)} text elements")

        # Format OCR results for LLM
        ocr_text = self._format_ocr_text()

        # Inject OCR text into messages
        modified_messages = self._inject_ocr_into_messages(messages, ocr_text)

        return modified_messages

    def get_ocr_bbox(self, ocr_id: int) -> Optional[Tuple[int, int, int, int]]:
        """
        Get bounding box for an OCR ID.

        Args:
            ocr_id: OCR element ID

        Returns:
            Tuple (x1, y1, x2, y2) or None if not found
        """
        if ocr_id in self.ocr_results:
            return self.ocr_results[ocr_id][1]
        return None

    def get_ocr_content(self, ocr_id: int) -> Optional[str]:
        """
        Get content for an OCR ID.

        Args:
            ocr_id: OCR element ID

        Returns:
            Text content or None if not found
        """
        if ocr_id in self.ocr_results:
            return self.ocr_results[ocr_id][0]
        return None
