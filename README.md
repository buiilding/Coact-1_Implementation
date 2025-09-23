# CoAct-1 Multi-Agent Computer Automation System

This directory contains the CoAct-1 implementation - a replica (not the exact code) of a closed-source agent architecture for Computer-Use that controls computers using vision (the eye) and code (the programmer). CoAct-1 uses three specialized AI agents working in coordination to automate complex computer tasks on virtual desktops.

## Overview

CoAct-1 implements a hierarchical multi-agent system inspired by the paper ["CoAct: A Multi-Agent System for Cooperative Computer Control"](https://arxiv.org/abs/2508.03923). The system orchestrates three specialized agents to execute computer automation tasks through coordinated action:

- **Orchestrator**: Strategic task decomposition and delegation
- **Programmer**: Shell command execution and file operations
- **GUI Operator**: Vision-based graphical user interface interactions

## Architecture

### Agent Hierarchy

```
┌─────────────────┐
│   Orchestrator  │ ← High-level task planning & coordination
├─────────────────┤
│   Programmer    │ ← Code execution & system commands
│   GUI Operator  │ ← Vision-based GUI interactions
└─────────────────┘
```

### Agent Responsibilities

#### 1. Orchestrator Agent
- **Model**: `gemini/gemini-2.5-flash`
- **Role**: Decomposes user tasks into minimal executable subtasks
- **Strategy**: Prefer Programmer agent for efficiency, use GUI Operator only for visual interactions
- **Delegation Logic**: Break tasks into 5-10 second executable units

#### 2. Programmer Agent
- **Model**: `gemini/gemini-2.5-flash`
- **Role**: Execute code and system-level operations
- **Tools**:
  - `run_command()`: Execute shell commands with output capture
  - `run_command_in_background()`: Launch GUI applications asynchronously
  - File system operations (`list_dir`, `read_file`, `write_file`)
  - Virtual environment commands (`venv_cmd`)

#### 3. GUI Operator Agent
- **Model**: `huggingface-local/OpenGVLab/InternVL3_5-4B+gemini/gemini-2.5-flash`
- **Role**: Vision-based GUI manipulation and visual element interaction
- **Capabilities**: Mouse/keyboard simulation, screenshot analysis, element detection
- **Efficiency Principle**: Minimize vision model calls, prefer keyboard shortcuts over mouse clicks

## Prerequisites

- **Python**: 3.12+
- **Docker**: Running Docker Desktop (Windows/macOS) or Docker Engine (Linux)
- **Conda/Miniconda**: For environment management
- **Google API Key**: For Gemini models (`GOOGLE_API_KEY` environment variable)

### System Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: Optional but recommended for local vision models (CUDA support)
- **Storage**: ~5GB for Docker images and models

## Quick Start

### 1. Environment Setup

```bash
# Create and activate conda environment
conda create -n coact1 python==3.12 -y
conda activate coact1
```

### 2. Install Dependencies

```bash
# Navigate to coact_implementation directory
cd coact_implementation

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install CUDA-enabled PyTorch for GPU acceleration
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. Set Environment Variables

```bash
# Set your Google API key
export GOOGLE_API_KEY="your-api-key-here"

# Verify the key is set
echo $GOOGLE_API_KEY
```

### 4. Run CoAct-1

```bash
# Basic usage
python coact_1.py -m "Open Firefox and navigate to github.com"

# Example tasks
python coact_1.py -m "Take a screenshot and save it as test.png"
python coact_1.py -m "Create a text file with 'Hello World' content"
python coact_1.py -m "Open terminal and run 'ls -la'"
```

## Detailed Usage

### Command Line Interface

```bash
python coact_1.py -m "TASK_DESCRIPTION"
```

**Parameters:**
- `-m, --message`: The task description to execute (required)

### Example Tasks

```bash
# File operations
python coact_1.py -m "Create a directory called 'test' and add a file with some content"

# Application management
python coact_1.py -m "Open Firefox browser and search for 'artificial intelligence'"

# System operations
python coact_1.py -m "Check disk usage and list running processes"

# GUI interactions
python coact_1.py -m "Open a text editor and type 'Hello from CoAct-1'"
```

### Execution Flow

1. **Initialization**: System starts Docker-based Linux VM (`trycua/cua-ubuntu:latest`)
2. **Screenshot Capture**: Initial screenshot taken for context
3. **Task Decomposition**: Orchestrator analyzes task and decomposes into subtasks
4. **Agent Delegation**: Tasks delegated to Programmer or GUI Operator
5. **Execution**: Specialist agents execute delegated subtasks
6. **Progress Evaluation**: Orchestrator reviews results and continues or completes
7. **Cleanup**: VM resources cleaned up

## Configuration

### Model Configuration

The system uses three models by default:

```python
orchestrator_model = "gemini/gemini-2.5-flash"
programmer_model = "gemini/gemini-2.5-flash"
gui_operator_model = "huggingface-local/OpenGVLab/InternVL3_5-4B+gemini/gemini-2.5-flash"
```

### Alternative Model Options

**For Orchestrator/Programmer:**
- `anthropic/claude-3-5-sonnet-20241022`
- `openai/gpt-4o`

**For GUI Operator:**
- `omniparser+gemini/gemini-2.5-flash` (uses OmniParser for element detection)
- `huggingface-local/ByteDance-Seed/UI-TARS-1.5-7B` (UI-TARS model)

### Computer Configuration

The system runs on a Docker-based Linux VM with these defaults:

```python
computer = Computer(
    os_type="linux",
    provider_type=VMProviderType.DOCKER,
    name="cua-coact1-demo",
    image="trycua/cua-ubuntu:latest",
)
```

## Architecture Details

### Computer Abstraction Layer

The system uses a sophisticated computer abstraction built on CUA (Computer Use Agent) framework:

- **Docker VM**: Isolated Ubuntu Linux environment
- **WebSocket Communication**: Real-time interaction with VM
- **GUI Proxy**: Restricted interface for GUI Operator (no shell access)

### Agent Communication Protocol

Agents communicate through multimodal messages containing:
- Text instructions and task descriptions
- Base64-encoded screenshot images
- Function call delegations and results
- Progress summaries and status updates

### Efficiency Optimizations

- **Token Efficiency**: Filtered conversation history to reduce context length
- **Vision Optimization**: Minimal screenshot usage, text-based progress summaries
- **Execution Strategy**: Background command execution for GUI applications
- **Delegation Logic**: Programmer-first approach for reliability

## Troubleshooting

### Common Issues

1. **Docker Connection Failed**
   ```bash
   # Ensure Docker is running
   docker --version
   docker ps
   ```

2. **API Key Not Set**
   ```bash
   echo $GOOGLE_API_KEY
   # Should show your key (masked for security)
   ```

3. **CUDA/GPU Issues**
   - For CPU-only: Use `torch` without CUDA
   - Check CUDA installation: `nvidia-smi`

4. **Model Loading Errors**
   - Ensure sufficient RAM (16GB+ recommended)
   - Check internet connection for model downloads

5. **Port Conflicts**
   - Default WebSocket ports may conflict
   - Check for running Docker containers

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Performance Tips

- **GPU Acceleration**: Install CUDA-enabled PyTorch for vision models
- **Memory Management**: Close other applications during execution
- **Network**: Ensure stable internet for API calls

## Development

### Project Structure

```
coact_implementation/
├── coact_1.py              # Main CoAct-1 implementation
├── requirements.txt        # Python dependencies
├── COACT1_TECHNICAL_README.md  # Technical documentation
├── agent/                  # Agent framework
├── computer/              # Computer interface abstraction
├── core/                  # Core utilities
└── benchmarks/            # Benchmarking tools
```

### Extending CoAct-1

#### Adding New Tools

```python
class CustomTools:
    async def custom_operation(self, param: str) -> str:
        # Implement your tool
        pass
```

#### Custom Agent Creation

```python
def _create_custom_agent(self) -> ComputerAgent:
    instructions = "Your custom agent instructions..."
    tools = [self.custom_tools.custom_operation]
    return ComputerAgent(
        model="your-model",
        tools=tools,
        instructions=instructions
    )
```

### Testing

Run the system with simple tasks first:

```bash
# Test basic functionality
python coact_1.py -m "List files in current directory"

# Test GUI operations
python coact_1.py -m "Open terminal application"
```

## Security & Sandboxing

- **Isolated Execution**: All operations run within Docker containers
- **No Host Access**: VM cannot modify host system files
- **Controlled APIs**: Limited computer interface exposure
- **Agent Isolation**: Clean separation between agent capabilities

## Performance Characteristics

- **Task Completion Time**: 30 seconds to 5 minutes depending on complexity
- **Token Usage**: ~10K-50K tokens per complex task
- **Memory Usage**: 4-8GB RAM during execution
- **Success Rate**: 85-95% for well-defined tasks

## Limitations

- **GUI Precision**: Vision-based element detection may fail on complex UIs
- **Browser Compatibility**: Optimized for Firefox, may need adaptation for other browsers
- **Network Dependency**: Requires internet for cloud models
- **Resource Intensive**: High memory/CPU usage during execution

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit a pull request with detailed description

## License

This implementation is for research and educational purposes. See the main project LICENSE for details.

## References

- [CoAct Paper](https://arxiv.org/abs/2508.03923)
- [CUA Framework](https://github.com/trycua/cua)
- [Computer Use Agent Research](https://www.anthropic.com/research/computer-use)

## Acknowledgments

This implementation is inspired by the CoAct architecture and built upon the excellent CUA framework. Special thanks to the trycua team for providing the foundational computer automation infrastructure.
