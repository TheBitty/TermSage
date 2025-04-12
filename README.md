# TermSage

<p align="center">
  <img src="https://via.placeholder.com/150?text=TermSage" alt="TermSage Logo" width="150" height="150">
</p>

<p align="center">
  <strong>The intelligent terminal interface for Ollama language models</strong>
</p>

<p align="center">
  <a href="#key-features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#troubleshooting">Troubleshooting</a>
</p>

---

## Overview

TermSage is a powerful command-line interface that lets you interact with Ollama language models directly from your terminal. With intelligent auto-completion, a rich user experience, and seamless model management, TermSage makes AI accessible right where you work.

![TermSage Demo](https://via.placeholder.com/800x450?text=TermSage+Demo)

## Key Features

- 💻 **Clean Terminal Interface** - Modern CLI with command history and intelligent auto-completion
- 🤖 **Multiple Model Support** - Use any Ollama model installed on your system
- 💬 **Interactive Chat** - Natural conversational interface for AI interactions
- ✍️ **Text Generation** - Generate content from simple prompts
- 🔧 **Customizable** - Adjust temperature, system prompts, and more
- 🚀 **Seamless Experience** - Auto-starts Ollama service when needed

## Installation

### Prerequisites

- Python 3.7 or higher
- [Ollama](https://ollama.ai/) installed on your system

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/TermSage.git
   cd TermSage
   ```

2. Create a virtual environment:
   ```bash
   # On macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate
   
   # On Windows:
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting TermSage

**Easiest Method:**
```bash
# From the root directory (with virtual environment activated):
python3 run_termsage.py  # On macOS/Linux
python run_termsage.py   # On Windows
```

Or make it executable (on macOS/Linux):
```bash
chmod +x run_termsage.py
./run_termsage.py
```

**Alternative Method:**
```bash
# Make sure you're in the root TermSage directory (not inside src)
# Make sure the virtual environment is activated (venv)

# On macOS/Linux:
python3 -m src.main

# On Windows:
python -m src.main
```

> **Important:** Always run TermSage from the root project directory, not from inside the src folder.

On first launch, TermSage will:
- Check if Ollama is running (starting it automatically by default)
- Detect available models
- Prompt you to select a model if none is configured

### Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `help` | List available commands | `help` |
| `list` | Show available models | `list` |
| `model` | Select a model to use | `model llama3` |
| `chat` | Start interactive chat session | `chat` |
| `generate` | Generate text from a prompt | `generate Write a haiku about code` |
| `temperature` | Set temperature (0.0-1.0) | `temperature 0.7` |
| `exit` or `quit` | Exit TermSage | `exit` |
| `clear` | Clear the screen | `clear` |
| `settings` | Configure settings | `settings` |

### Examples

#### Selecting a Model

```
TermSage > list
Available models (3):
  1. llama3:8b (4.1GB) *
  2. codellama:7b (4.7GB)
  3. mistral:7b (4.1GB)

TermSage > model codellama
Active model set to codellama:7b
```

#### Chat Mode

```
TermSage [codellama:7b] > chat
Starting chat with codellama:7b...
Type 'exit' to end the chat session.

You: How can I read a file in Python?
Assistant: You can read a file in Python using the built-in `open()` function. Here's a simple example:

```python
# Read the entire file as a string
with open('filename.txt', 'r') as file:
    content = file.read()
    print(content)

# Read file line by line
with open('filename.txt', 'r') as file:
    for line in file:
        print(line.strip())
```

The `with` statement is recommended as it automatically closes the file when you're done with it.

You: exit
Ending chat session
```

#### Text Generation

```
TermSage [llama3:8b] > generate Write a haiku about programming

Generated text:
----------------------------------------
Fingers on keyboard
Code blooms like spring flowers bloom
Bugs hide in shadows
----------------------------------------
```

## Configuration

### Settings Menu

Access the settings menu with the `settings` command:

```
TermSage > settings

Settings:
  1. Active Model: llama3:8b
  2. Temperature: 0.7
  3. System Prompt: You are a helpful AI assistant...
  4. Auto-start Ollama: True
  0. Back to main menu

Enter your choice (0-4):
```

### Auto-Completion

TermSage provides context-aware auto-completion:

- Press `Tab` to see available commands
- When using the `model` command, it suggests available models
- When using the `temperature` command, it suggests common values

Command history is also available using the up/down arrow keys.

### Configuration File

TermSage stores your preferences in `~/.termsage/config.json`. Advanced users can edit this file directly:

```json
{
  "active_model": "llama3:8b",
  "temperature": 0.7,
  "system_prompt": "You are a helpful AI assistant. Answer the user's questions concisely and accurately.",
  "theme": {
    "prompt": "ansigreen bold",
    "model_info": "ansiyellow",
    "chat_prompt": "ansimagenta bold",
    "error": "ansired"
  },
  "history_limit": 100,
  "auto_start_ollama": true
}
```

## Understanding Parameters

### Temperature

The temperature parameter controls response randomness:

- **Low (0.0-0.3)**: More deterministic, focused, consistent responses
- **Medium (0.4-0.7)**: Balanced creativity and coherence
- **High (0.8-1.0)**: More creative, diverse, and sometimes surprising outputs

## Troubleshooting

### Common Issues

#### Python Command Not Found

If you see `zsh: command not found: python`, this means Python isn't in your PATH. This is common on macOS.

**Solution**: Use `python3` instead of `python`:

```bash
# Instead of:
python -m venv venv

# Use:
python3 -m venv venv
```

#### Module Not Found Error

If you see `ModuleNotFoundError: No module named 'src'` when running `python -m src.main`:

**Cause**: You might be running the command from inside the `src` directory.

**Solution**: 
1. Make sure you're in the root project directory (TermSage folder)
2. Run the command from there:
```bash
cd ~/path/to/TermSage  # Go to root directory
source venv/bin/activate  # Activate virtual environment
python3 -m src.main  # Run the application
```

#### Ollama Not Running
```
Ollama service is not running.
Auto-starting Ollama...
```

TermSage will automatically start Ollama if configured to do so. If this fails:
1. Try starting Ollama manually: `ollama serve`
2. Make sure Ollama is properly installed
3. Check if another instance is already running

#### No Models Available
```
No models found. Install models with 'ollama pull <model_name>'
```

Install at least one model with:
```bash
ollama pull llama3
# or
ollama pull mistral
```

#### Slow Response Times

First-time model loading can be slow. Consider:
- Using smaller models for faster responses
- Keeping the same model active to avoid reloading

### Alternative Ways to Run TermSage

If you're having issues, try the simplest method:

```bash
# From the root TermSage directory with virtual env activated:
python3 run_termsage.py  # On macOS/Linux
python run_termsage.py   # On Windows
```

Or you can run the main.py file directly:

```bash
# From the root TermSage directory:
cd src
python3 main.py  # On macOS/Linux
python main.py   # On Windows
```

## Advanced Usage

### Custom System Prompts

Set custom instructions for the AI model:

```
TermSage > settings
Enter your choice (0-4): 3

Current system prompt: You are a helpful AI assistant...
Enter new system prompt: You are a coding assistant specializing in Python. Provide concise code examples and explain key concepts clearly.

System prompt updated
```

### Running Tests

For developers, run the test suite with:

```bash
./run_tests.py
```

For just the lint checks:
```bash
./run_tests.py --lint-only
```

For a quick integration test:
```bash
python integration_test.py
```

## For Developers

### Project Structure

```
TermSage/
├── src/               # Source code
│   ├── main.py        # Entry point and CLI interface
│   ├── ollama.py      # Ollama service interaction
│   ├── config.py      # Configuration management
│   ├── autocomplete.py # Auto-completion system
│   └── __init__.py
├── tests/             # Test files
├── requirements.txt   # Project dependencies
└── README.md          # Project overview
```

### Key Components

- **TermSageCLI**: Main CLI interface and command handler
- **Config**: Configuration management and persistence
- **OllamaClient**: Interacts with local Ollama service
- **TermSageCompleter**: Context-aware command completion

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run the tests (`./run_tests.py`) to ensure everything works
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

Please make sure your code passes all lint checks and tests before submitting a PR.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Ollama](https://ollama.ai/) for making local LLMs accessible
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) for the interactive CLI components

---

<p align="center">
  Made with ❤️ for terminal enthusiasts and AI explorers
</p> 