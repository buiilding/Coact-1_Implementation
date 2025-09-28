#!/usr/bin/env python3
"""
Standalone OCR Screenshot Script

This script takes a screenshot and performs OCR analysis using RapidOCR,
returning UI elements in the same format as the original codebase.
It also saves a debug image with OCR bounding boxes overlaid.

Requirements:
- pip install rapidocr pillow pyautogui screeninfo

Usage:
    python ocr_screenshot.py
"""

import io
import pyautogui
import screeninfo
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, List, Dict, Any


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


def draw_ocr_debug_image(image: Image.Image, text_list: List[str], bbox_list: List[Tuple[int, int, int, int]], output_path: str = "ocr_debug.png"):
    """
    Draw OCR bounding boxes and text on the image and save as debug image.

    Args:
        image: PIL Image to draw on
        text_list: List of detected text strings
        bbox_list: List of bounding boxes (x1, y1, x2, y2)
        output_path: Path to save the debug image
    """
    try:
        # Create a copy of the image to draw on
        debug_image = image.copy()
        draw = ImageDraw.Draw(debug_image)

        # Try to use a better font, fallback to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()

        # Draw bounding boxes and text
        for text, bbox in zip(text_list, bbox_list):
            x1, y1, x2, y2 = bbox

            # Draw bounding box
            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)

            # Draw text background for readability
            text_bbox = draw.textbbox((x1, y1-20), text, font=font)
            draw.rectangle(text_bbox, fill="white")

            # Draw text
            draw.text((x1, y1-20), text, fill="red", font=font)

        # Save the debug image
        debug_image.save(output_path)
        print(f"🖼️ OCR debug image saved to: {output_path}")

    except Exception as e:
        print(f"⚠️ Failed to create OCR debug image: {e}")


def capture_screen() -> Tuple[Image.Image | None, Dict | None]:
    """
    Captures the primary monitor's screen.

    Returns:
        A tuple containing:
        - A PIL Image object of the screen capture, or None on error.
        - A dictionary with monitor details ('x', 'y', 'width', 'height'), or None on error.
    """
    try:
        monitors = screeninfo.get_monitors()
        if not monitors:
            print("⚠️ No monitors detected by screeninfo, capturing full screen.")
            screenshot = pyautogui.screenshot()
            monitor_info = {'x': 0, 'y': 0, 'width': screenshot.width, 'height': screenshot.height}
        else:
            monitor = monitors[0]
            print(f"📸 Capturing screen of monitor {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})")
            screenshot = pyautogui.screenshot(region=(monitor.x, monitor.y, monitor.width, monitor.height))
            monitor_info = {'x': monitor.x, 'y': monitor.y, 'width': monitor.width, 'height': monitor.height}

        return screenshot, monitor_info
    except Exception as e:
        print(f"🔴 Error capturing screen: {e}")
        return None, None


def analyze_screen_ocr_only(image: Image.Image, monitor_info: Dict, rapid_ocr_engine) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Analyzes a screenshot with OCR only to identify text elements.

    Args:
        image: The raw PIL Image of the screen.
        monitor_info: A dictionary with the screen's geometry.
        rapid_ocr_engine: The OCR engine instance.

    Returns:
        A tuple containing:
        - A list of dictionaries for the detected text elements (nodes).
        - An empty list for edges (not generated for OCR-only mode).
    """
    print("🔍 Analyzing screen with OCR only...")

    try:
        # Convert image to RGB and prepare for OCR
        image_rgb = image.convert('RGB')
        buffer = io.BytesIO()
        image_rgb.save(buffer, format='PNG')
        image_rgb_bytes = buffer.getvalue()

        # Perform OCR
        if rapid_ocr_engine:
            result = rapid_ocr_engine(image_rgb_bytes)
            text_list, ocr_bbox = check_ocr_result(result)
        else:
            text_list, ocr_bbox = [], []

        # Create OCR debug image
        if text_list and ocr_bbox:
            draw_ocr_debug_image(image, text_list, ocr_bbox, "ocr_debug.png")

        # Convert OCR results to node format
        nodes = []
        for i, (content, bbox) in enumerate(zip(text_list, ocr_bbox)):
            x1, y1, x2, y2 = bbox

            # Convert to absolute screen coordinates
            abs_x1 = x1 + monitor_info['x']
            abs_y1 = y1 + monitor_info['y']
            abs_x2 = x2 + monitor_info['x']
            abs_y2 = y2 + monitor_info['y']

            new_node = {
                "id": i,
                "content": content,
                "type": "text",
                "interactivity": False,  # OCR text is not interactive
                "x": abs_x1,
                "y": abs_y1,
                "width": abs_x2 - abs_x1,
                "height": abs_y2 - abs_y1
            }
            nodes.append(new_node)

        # Return empty edges list since we're not generating relationships
        edges = []

        print(f"✅ OCR analysis succeeded. Found {len(nodes)} text elements.")
        return nodes, edges

    except Exception as e:
        print(f"🔴 Error during OCR analysis: {e}")
        return [], []


def main():
    """
    Main function to demonstrate OCR screenshot analysis.
    """
    print("🚀 Starting OCR Screenshot Analysis...")

    # Initialize OCR engine (using CPU by default for compatibility)
    print("⚙️ Initializing RapidOCR engine...")
    try:
        ocr_engine = get_rapid_ocr_engine(device="cpu")
        print("✅ RapidOCR engine initialized successfully.")
    except Exception as e:
        print(f"🔴 Failed to initialize OCR engine: {e}")
        return

    # Capture screenshot
    print("📸 Capturing screenshot...")
    screenshot, monitor_info = capture_screen()

    if not screenshot or not monitor_info:
        print("🔴 Failed to capture screenshot.")
        return

    # Analyze with OCR only
    nodes, edges = analyze_screen_ocr_only(screenshot, monitor_info, ocr_engine)

    # Print results
    print(f"\n📊 Analysis Results:")
    print(f"Found {len(nodes)} text elements")
    print(f"Found {len(edges)} edges (relationships)")
    print("OCR debug image saved as 'ocr_debug.png'")

    print("\n📝 Text Elements Found:")
    for node in nodes[:10]:  # Show first 10 elements
        print(f"ID {node['id']}: '{node['content']}' at ({node['x']}, {node['y']}) {node['width']}x{node['height']}")

    if len(nodes) > 10:
        print(f"... and {len(nodes) - 10} more elements")

    # Return the data (in a real usage, you'd return this to another function)
    return nodes, edges


if __name__ == "__main__":
    result = main()
    if result:
        nodes, edges = result
        print(f"\n✅ Script completed successfully with {len(nodes)} text elements detected.")
