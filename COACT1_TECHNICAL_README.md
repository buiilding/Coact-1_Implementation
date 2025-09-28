# CoAct-1 Multi-Agent System - Technical Implementation

## Overview

`coact_1_example.py` implements the CoAct-1 architecture - a hierarchical multi-agent system for computer automation. The system orchestrates three specialized AI agents to execute complex computer tasks through coordinated action.

## Architecture

### Core Components

#### 1. **Computer Infrastructure**
- **Docker-based VM**: Isolated Linux environment (`trycua/cua-ubuntu:latest`)
- **Computer Interface**: WebSocket-based communication layer
- **CUA Framework**: Computer Use Agent framework for action execution

#### 2. **Agent Hierarchy**

```
┌─────────────────┐
│   Orchestrator  │ ← High-level task decomposition & delegation
├─────────────────┤
│   Programmer    │ ← Shell command execution & file operations
│   GUI Operator  │ ← Vision-based GUI interactions
└─────────────────┘
```

## Agent Specifications

### 1. Orchestrator Agent
**Role**: Strategic task decomposition and coordination
**Model**: `gemini/gemini-2.5-flash`
**Responsibilities**:
- Analyze user tasks and current screen state
- Break complex tasks into minimal subtasks
- Delegate to appropriate specialist agents
- Evaluate progress and determine next actions

**Key Instructions**:
- Prefer Programmer agent for efficiency (shell commands)
- Use GUI Operator only for visual interactions
- Break tasks into 5-10 second executable units
- Always evaluate both text summaries and visual screenshots

### 2. Programmer Agent
**Role**: Code and system-level task execution
**Model**: `gemini/gemini-2.5-flash`
**Tools**:
- `run_command()`: Execute shell commands with output capture
- `run_command_in_background()`: Launch GUI applications asynchronously
- `list_dir()`, `read_file()`, `write_file()`: File system operations
- `venv_cmd()`: Execute commands in virtual environments

**Command Strategy**:
- `run_command`: For operations needing output (ls, cat, grep)
- `run_command_in_background`: For GUI applications (firefox, chrome)

### 3. GUI Operator Agent
**Role**: Vision-based graphical user interface interactions with OCR capabilities
**Model**: `huggingface-local/OpenGVLab/InternVL3_5-4B+gemini/gemini-2.5-flash`
**Capabilities**:
- Visual element detection and interaction
- OCR text detection and extraction
- Click-by-text functionality
- Mouse and keyboard simulation
- Screenshot analysis and prediction

**OCR Features**:
- **RapidOCR Integration**: Automatic text element detection from screenshots
- **Bounding Box Generation**: Precise coordinate mapping for text elements
- **Confidence Scoring**: Quality assessment for detected text elements
- **Text-based Interaction**: Direct clicking on detected text elements by ID

**Efficiency Principles**:
- Minimize grounding model calls (vision-based element detection)
- Prefer keyboard shortcuts over mouse clicks
- Use Enter/Tab navigation instead of clicking buttons
- Leverage OCR for precise text element interactions
- Predict screen state changes for each action

## Implementation Details

### Computer Abstraction Layer

#### GuiOperatorComputerProxy
```python
class GuiOperatorComputerProxy:
    """Restricts GUI Operator to visual-only interactions with OCR support"""
```
- Proxies the Computer object to expose only GUI-relevant methods
- Includes OCR callback for automatic text element detection
- Provides `click_ocr_text()`, `right_click_ocr_text()`, `double_click_ocr_text()` methods
- Prevents shell command execution by GUI Operator
- Ensures clean separation of concerns between agents

#### Computer Interface Methods
- **Mouse**: `left_click`, `right_click`, `double_click`, `move_cursor`, `drag`
- **Keyboard**: `type_text`, `press_key`, `hotkey`
- **Screen**: `screenshot`, `get_screen_size`
- **OCR**: `click_ocr_text`, `right_click_ocr_text`, `double_click_ocr_text`
- **System**: `run_command`, `list_dir`, `read_text`, `write_text`

### Agent Communication Protocol

#### Multimodal Message Format
```python
{
    "role": "user",
    "content": [
        {"type": "text", "text": "Navigate to amazon.com"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
    ]
}
```

#### Function Call Delegation
```python
# Orchestrator delegates to specialists
delegate_to_programmer(subtask="Open Firefox browser")
delegate_to_gui_operator(subtask="Click login button")
task_completed()  # Signal completion
```

### Execution Flow

#### Main Loop (Up to 10 iterations)
1. **Initial Setup**: Take screenshot, create multimodal prompt
2. **Orchestrator Planning**: Analyze screen + task, decide delegation
3. **Sub-agent Execution**: Specialist performs delegated subtask
4. **Result Summarization**: Generate text summary of actions
5. **Progress Evaluation**: Orchestrator reviews results + new screenshot
6. **Iteration**: Continue until `task_completed()` or max steps reached

### Vision-Language Integration

#### Screenshot Processing
- Base64 encoded PNG images
- Integrated into chat messages for multimodal reasoning
- Used by both Orchestrator (task planning) and GUI Operator (element detection)

#### OCR Processing Pipeline
- **RapidOCR Engine**: Fast text detection from screenshots
- **Text Element Extraction**: Identifies clickable text elements with confidence scores
- **Bounding Box Calculation**: Maps text positions to screen coordinates
- **LLM Integration**: OCR results injected into prompts for intelligent text interactions

#### Grounding Model Calls
- **InternVL**: Local vision model for element detection
- **Gemini**: Remote multimodal model for planning and reasoning
- **OCR Enhancement**: Text detection reduces need for expensive vision calls
- Optimized to minimize expensive model calls through OCR preprocessing

## Configuration & Models

### Model Configuration
```python
orchestrator_model = "gemini/gemini-2.5-flash"
programmer_model = "gemini/gemini-2.5-flash"
gui_operator_model = "huggingface-local/OpenGVLab/InternVL3_5-4B+gemini/gemini-2.5-flash"
```

### Environment Requirements
- **GOOGLE_API_KEY**: For Gemini API access
- **Docker**: Running containerized Linux environment
- **CUDA** (optional): For GPU-accelerated vision models
- **Python 3.12+**: With CUA framework dependencies

## Error Handling & Recovery

### GUI Operator Recovery Strategies
1. **Keyboard-first approach**: Alt+Left (back), ESC (cancel), Ctrl+Z (undo)
2. **Navigation shortcuts**: Ctrl+Home/End, F5 (refresh)
3. **Fallback to mouse clicks**: Only when keyboard methods fail

### System-level Error Handling
- Graceful degradation when models unavailable
- Docker container lifecycle management
- WebSocket connection recovery

## Performance Optimizations

### Token Efficiency
- Screenshot filtering to reduce context length
- Text-only summarization for progress reports
- Minimal multimodal message construction

### Execution Efficiency
- Background command execution for GUI apps
- Asynchronous task coordination
- Incremental progress evaluation

## API Integration

### Command Line Interface
```bash
python coact_1_example.py -m "Go to Amazon and find the cheapest laptop"
```

### Web UI Integration
- REST API endpoint for task submission
- Server-Sent Events for real-time output streaming
- Automatic browser opening for result display

## Security Considerations

### Sandboxed Execution
- All operations run within Docker container
- Isolated Linux environment prevents system modification
- Controlled API access to computer functions

### Agent Isolation
- Programmer: Shell command execution only
- GUI Operator: Visual interactions only
- Orchestrator: Planning and delegation only

## Future Extensions

### Additional Agent Types
- **Web Agent**: Specialized browser automation
- **File Agent**: Advanced document processing
- **API Agent**: External service integration

### Enhanced Capabilities
- **Multi-screen coordination**
- **Cross-application workflows**
- **Error recovery automation**
- **Performance monitoring**

## Dependencies

### Core Framework
- `cua-agent`: Computer Use Agent framework
- `cua-computer`: Docker-based computer interface
- `litellm`: Unified LLM API interface

### Vision Models
- `transformers`: Hugging Face model loading
- `torch`: PyTorch deep learning framework
- `accelerate`: Multi-GPU training/inference
- `rapidocr-onnxruntime`: Fast OCR text detection
- `Pillow`: Image processing for OCR

### System Integration
- `docker`: Container management
- `websockets`: Real-time communication
- `asyncio`: Asynchronous task coordination

## Troubleshooting

### Common Issues
1. **Docker connectivity**: Ensure Docker daemon is running
2. **Model loading**: Check CUDA availability for GPU models
3. **API keys**: Verify GOOGLE_API_KEY environment variable
4. **Port conflicts**: Check for WebSocket connection issues

### Debug Output
- Set logging level to `INFO` for detailed execution traces
- Enable screenshot saving for visual debugging
- Monitor agent conversation history for decision analysis

---

This implementation demonstrates a production-ready multi-agent system capable of executing complex computer automation tasks through intelligent agent coordination and specialized capabilities.
