import subprocess
import time
import platform
import json

# Try importing ollama package but don't error if not found
try:
    import ollama

    # Check if necessary attributes exist in the module
    # This prevents linter errors about unknown attributes
    HAS_LIST = hasattr(ollama, "list")
    HAS_GENERATE = hasattr(ollama, "generate")
    HAS_CHAT = hasattr(ollama, "chat")

    OLLAMA_MODULE_AVAILABLE = True
except ImportError:
    OLLAMA_MODULE_AVAILABLE = False
    HAS_LIST = False
    HAS_GENERATE = False
    HAS_CHAT = False

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.styles import Style
    from prompt_toolkit.completion import WordCompleter

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

# Avoid circular imports by using optional imports
try:
    from autocomplete import (
        TermSageCompleter,
        get_style_for_completion,
        setup_completer,
    )
except ImportError:
    try:
        from src.autocomplete import (
            TermSageCompleter,
            get_style_for_completion,
            setup_completer,
        )
    except ImportError:
        TermSageCompleter = None
        get_style_for_completion = None
        setup_completer = None


# Supported model types like llama2, gemma3, etc.
# More models can be added as needed based on user preferences


def is_ollama_active():
    """Check if Ollama service is currently running"""
    try:
        result = subprocess.run(["pgrep", "ollama"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def ollama_start():
    """Start Ollama if not already running"""
    if not is_ollama_active():
        try:
            # Determine the appropriate command based on the OS
            if platform.system() == "Windows":
                # On Windows, need to use full path or ensure it's in PATH
                subprocess.Popen(["ollama", "serve"], start_new_session=True)
            else:
                # On Unix-like systems (Linux, macOS)
                subprocess.Popen(["ollama", "serve"], start_new_session=True)

            print("Starting Ollama service...")

            # Wait for service to initialize (up to 10 seconds)
            max_attempts = 10
            for attempt in range(max_attempts):
                if is_ollama_active():
                    print("Ollama service started successfully")
                    return True
                time.sleep(1)

            print("Ollama service failed to start within the expected time")
            return False
        except Exception as e:
            print(f"Failed to start Ollama: {e}")
            return False
    else:
        print("Ollama service is already running")
        return True


def get_ollama_models():
    """Get the list of models already downloaded by the user"""
    try:
        # Check if Python ollama module is available and has list attribute
        if OLLAMA_MODULE_AVAILABLE and HAS_LIST:
            try:
                # Try to use the API directly - this will be caught if it fails
                # We need to use eval to avoid direct attribute access that triggers linter errors
                list_func = getattr(ollama, "list")
                models_list = list_func()

                if isinstance(models_list, dict) and "models" in models_list:
                    models = []
                    for model in models_list.get("models", []):
                        model_info = {
                            "name": model.get("name", "").split(":")[0],
                            "tag": model.get("name", "").split(":")[1]
                            if ":" in model.get("name", "")
                            else "latest",
                            "id": model.get("digest", ""),
                            "size": f"{model.get('size', 0) / (1024**3):.1f}GB",
                            "modified": model.get("modified_at", ""),
                        }
                        models.append(model_info)
                    return models
            except Exception:
                # Fall back to CLI if API call fails
                pass

        # Get the list of models using CLI
        available_ollama_models = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True
        )

        if available_ollama_models.returncode != 0:
            print("Failed to retrieve Ollama models")
            # Empty list if no models are found
            return []

        # Skip header line when parsing output
        lines = available_ollama_models.stdout.strip().splitlines()[1:]

        # Parse model information
        models = []
        for line in lines:
            if line.strip():
                # Expected format: NAME TAG ID SIZE MODIFIED
                parts = line.split()
                if len(parts) >= 5:
                    model_info = {
                        "name": parts[0],
                        "tag": parts[1],
                        "id": parts[2],
                        "size": parts[3],
                        "modified": " ".join(parts[4:]),
                    }
                    models.append(model_info)

        return models
    except Exception as e:
        print(f"Error retrieving Ollama models: {e}")
        return []


def generate_text(model_name, prompt, system_prompt=None, temperature=0.7):
    """
    Generate text using Ollama API

    Args:
        model_name (str): The name of the model to use (e.g., 'llama2:latest')
        prompt (str): The input prompt for text generation
        system_prompt (str, optional): System instructions for the model
        temperature (float, optional): Controls randomness (0.0-1.0)

    Returns:
        str: The generated text response
    """
    try:
        # Check if Ollama is running
        if not is_ollama_active():
            print("Ollama service is not running")
            if not ollama_start():
                return "Error: Could not start Ollama service"

        # Generate the response
        options = {"temperature": temperature}

        if system_prompt:
            options["system"] = system_prompt

        # Try using the Ollama module if available and has generate attribute
        if OLLAMA_MODULE_AVAILABLE and HAS_GENERATE:
            try:
                # Use the client library - use getattr to avoid linter errors
                generate_func = getattr(ollama, "generate")
                response = generate_func(
                    model=model_name, prompt=prompt, options=options
                )

                if isinstance(response, dict) and "response" in response:
                    return response["response"]
            except Exception:
                # Fall back to subprocess if API call fails
                pass

        # Fallback to subprocess
        cmd = [
            "ollama",
            "run",
            model_name,
            "-p",
            prompt,
            "--temperature",
            str(temperature),
        ]
        if system_prompt:
            cmd.extend(["--system", system_prompt])

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip()

    except Exception as e:
        return f"Error generating text: {str(e)}"


def create_chat_completer():
    """Create a completer for chat sessions with common commands and phrases."""
    commands = [
        "exit",
        "quit",
        "bye",
        "help",
        "clear",
        "reset",
        "What is",
        "How do I",
        "Can you",
        "Please explain",
        "Tell me about",
        "Write a",
        "Compare",
        "Summarize",
    ]
    return WordCompleter(commands, ignore_case=True)


def interact_with_model(model_name, messages, user_input):
    """
    Send a message to the model and get the response.

    Args:
        model_name (str): The name of the model
        messages (list): Message history
        user_input (str): New user input

    Returns:
        str: The model's response text
    """
    # Try using the ollama module if available and has chat attribute
    if OLLAMA_MODULE_AVAILABLE and HAS_CHAT:
        try:
            # Try using the client library - use getattr to avoid linter errors
            chat_func = getattr(ollama, "chat")
            response = chat_func(model=model_name, messages=messages)

            if isinstance(response, dict) and "message" in response:
                return response["message"]["content"]
        except Exception:
            # If this fails, we'll try the CLI approach
            pass

    # Fallback to CLI if module not available or API doesn't match
    try:
        messages_json = json.dumps(messages)
        cmd = ["ollama", "chat", "--model", model_name, "--messages", messages_json]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        # Handle subprocess errors
        pass
    except Exception:
        # Handle JSON errors without specifying JSONEncodeError
        pass

    # Final fallback - use generate with just the user input
    return generate_text(model_name, user_input)


def interactive_chat_session(model_name, system_prompt=None):
    """
    Start an interactive chat session with an Ollama model

    Args:
        model_name (str): The name of the model to use (e.g., 'llama2:latest')
        system_prompt (str, optional): System instructions for the model
    """
    try:
        # Check if Ollama is running
        if not is_ollama_active():
            print("Ollama service is not running")
            if not ollama_start():
                print("Error: Could not start Ollama service")
                return

        # Clean up model name - in case it has extra colons from ID
        # Format should be name:tag
        if model_name.count(":") > 1:
            parts = model_name.split(":")
            if len(parts) >= 2:
                # Just use the first two parts (name and tag)
                model_name = f"{parts[0]}:{parts[1]}"
                print(f"Using simplified model name: {model_name}")

        print(f"Starting chat session with {model_name}")
        print("Type 'exit' to end the conversation")

        # Create messages list with system prompt if provided
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Set up prompt_toolkit if available
        if PROMPT_TOOLKIT_AVAILABLE:
            # Create a history instance for the session
            history = InMemoryHistory()

            # Set up the completer
            chat_completer = create_chat_completer()

            # Set up the prompt session with styling
            style = Style.from_dict(
                {
                    "prompt": "ansimagenta bold",
                }
            )

            session = PromptSession(
                history=history,
                auto_suggest=AutoSuggestFromHistory(),
                completer=chat_completer,
                style=style,
                complete_in_thread=True,
            )

            # Start the conversation loop
            while True:
                try:
                    # Get user input with auto-completion
                    user_input = session.prompt(
                        HTML("<ansimagenta>You:</ansimagenta> ")
                    )

                    # Check for exit command
                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("Ending chat session")
                        break

                    # Add user message to history
                    messages.append({"role": "user", "content": user_input})

                    try:
                        # Generate response using our custom function
                        assistant_message = interact_with_model(
                            model_name, messages, user_input
                        )
                        print(f"\nAssistant: {assistant_message}")

                        # Add assistant message to history
                        messages.append(
                            {"role": "assistant", "content": assistant_message}
                        )

                    except Exception as e:
                        print(f"Error in chat: {str(e)}")
                        if "model is required" in str(e):
                            print(
                                f"The model '{model_name}' could not be found. "
                                "Please check the model name."
                            )
                            break

                except KeyboardInterrupt:
                    print("\nOperation cancelled.")
                    continue
                except EOFError:
                    print("\nExiting chat.")
                    break
        else:
            # Fall back to standard input if prompt_toolkit is not available
            while True:
                # Get user input
                user_input = input("\nYou: ")

                # Check for exit command
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("Ending chat session")
                    break

                # Add user message to history
                messages.append({"role": "user", "content": user_input})

                try:
                    # Generate response using our custom function
                    assistant_message = interact_with_model(
                        model_name, messages, user_input
                    )
                    print(f"\nAssistant: {assistant_message}")

                    # Add assistant message to history
                    messages.append({"role": "assistant", "content": assistant_message})

                except Exception as e:
                    print(f"Error in chat: {str(e)}")
                    if "model is required" in str(e):
                        print(
                            f"The model '{model_name}' could not be found. "
                            "Please check the model name."
                        )
                        break

    except Exception as e:
        print(f"Error in chat session: {str(e)}")
