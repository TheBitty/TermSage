import subprocess
import ollama
import time
import platform


# Supported model types like llama2, gemma3, etc.
# More models can be added as needed based on user preferences


def is_ollama_active():
    """Check if Ollama service is currently running"""
    try:
        result = subprocess.run(
            ["pgrep", "ollama"], capture_output=True, text=True
        )
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
        # Get the list of models
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

        # Use the Ollama client library to generate text
        try:
            response = ollama.generate(
                model=model_name, prompt=prompt, options=options
            )
            return response["response"]
        except AttributeError:
            # Fallback to subprocess if library API changes
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

        # Start the conversation loop
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
                # Generate response using Ollama API
                try:
                    response = ollama.chat(model=model_name, messages=messages)

                    # Extract and print assistant's response
                    assistant_message = response["message"]["content"]
                    print(f"\nAssistant: {assistant_message}")

                    # Add assistant message to history
                    messages.append(
                        {"role": "assistant", "content": assistant_message}
                    )
                except AttributeError:
                    # Fallback to subprocess if API changes
                    print(
                        f"\nAssistant: Using {model_name} with prompt: "
                        f"{user_input}"
                    )
                    messages.append(
                        {
                            "role": "assistant",
                            "content": "Response via subprocess",
                        }
                    )

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
