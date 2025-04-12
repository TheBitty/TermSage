"""
Main entry point for the TermSage application.
"""
try:
    # Try local import first (when running from src directory)
    from ollama import (
        is_ollama_active,
        ollama_start,
        get_ollama_models,
        interactive_chat_session,
    )
except ImportError:
    # Fall back to absolute import (when running as module)
    from src.ollama import (
        is_ollama_active,
        ollama_start,
        get_ollama_models,
        interactive_chat_session,
    )


def select_model(models):
    """
    Display numbered models and let user select one.

    Args:
        models: List of model dictionaries

    Returns:
        model_string: String formatted as "model_name:tag"
    """
    if not models:
        msg = (
            "No models found. Install models with 'ollama pull <model_name>'"
        )
        print(msg)
        return None

    print("What model would you like to use?")
    # Display models with numbers for selection
    for i, model in enumerate(models, 1):
        print(f"{i}. {model['name']}:{model['tag']}")

    # Get user selection by number
    while True:
        try:
            selection = int(
                input("Enter the number of the model you want to use: ")
            )
            if 1 <= selection <= len(models):
                model_name = models[selection - 1]["name"]
                model_tag = models[selection - 1]["tag"]
                break
            else:
                print(f"Please enter a number between 1 and {len(models)}")
        except ValueError:
            print("Please enter a valid number")

    # Allow user to customize tag if desired
    custom_tag = input(
        "Press Enter to use the default tag, or type a custom tag: "
    )

    # Use a simple model_name:tag format (don't include ID information)
    if custom_tag:
        model_string = f"{model_name}:{custom_tag}"
    else:
        # Extract just the tag part without any ID information
        if ":" in model_tag:
            model_tag = model_tag.split(":")[0]
        model_string = f"{model_name}:{model_tag}"

    return model_string


def main():
    """Main function to run the application."""
    print("Welcome to TermSage!")
    system_prompt = (
        "You are a AI assistant. For the command line, meant to help the "
        "user execute commands in the terminal. Be specific and concise."
    )

    # Check if Ollama is active
    if is_ollama_active():
        print("Ollama service is already running.")
        # Get available models
        models = get_ollama_models()
        print(f"Available models: {len(models)}")

        # Select model
        model_string = select_model(models)
        if model_string:
            # Start interactive chat session
            print(f"Starting chat with {model_string}...")
            interactive_chat_session(
                model_string, system_prompt=system_prompt
            )
    else:
        print("Ollama service is not running.")
        # Optionally start Ollama if it's not running
        should_start = input("Would you like to start Ollama? (y/n): ").lower()
        if should_start == "y":
            if ollama_start():
                models = get_ollama_models()
                print(f"Available models: {len(models)}")

                # Select model
                model_string = select_model(models)
                if model_string:
                    # Start interactive chat session
                    print(f"Starting chat with {model_string}...")
                    interactive_chat_session(
                        model_string, system_prompt=system_prompt
                    )
            else:
                print("Failed to start Ollama. Please start it manually.")
        else:
            print("Ollama service will not be started.")
            print("Please start Ollama manually and try again.")
            return


if __name__ == "__main__":
    main()
