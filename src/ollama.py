"""
Ollama integration module for TermSage.

This module provides functions to interact with the Ollama service.
"""

import subprocess
import time
import os
from typing import List, Dict, Any, Optional, Union


def is_ollama_active() -> bool:
    """
    Check if the Ollama service is running.
    
    Returns:
        bool: True if Ollama is running, False otherwise
    """
    try:
        result = subprocess.run(["pgrep", "ollama"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def ollama_start() -> bool:
    """
    Start the Ollama service if it's not already running.
    
    Returns:
        bool: True if Ollama is running or was started successfully, False otherwise
    """
    if is_ollama_active():
        return True
    
    try:
        # Start ollama as a background process
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for ollama to start (max 10 seconds)
        for _ in range(10):
            time.sleep(1)
            if is_ollama_active():
                return True
        
        return False
    except Exception:
        return False


def get_ollama_models() -> List[Dict[str, str]]:
    """
    Get a list of available Ollama models.
    
    Returns:
        List[Dict[str, str]]: List of models, each with name, tag, and size
    """
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode != 0:
            return []
        
        models = []
        lines = result.stdout.strip().split('\n')
        if len(lines) <= 1:  # Only header or empty
            return []
            
        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 4:
                models.append({
                    "name": parts[0],
                    "tag": parts[1],
                    "id": parts[2],
                    "size": parts[3]
                })
        
        return models
    except Exception:
        return []


def generate_text(
    model: str, 
    prompt: str, 
    system_prompt: Optional[str] = None,
    temperature: float = 0.7
) -> str:
    """
    Generate text using Ollama.
    
    Args:
        model: Name of the model to use
        prompt: Text prompt for generation
        system_prompt: Optional system prompt
        temperature: Temperature for generation (0.0-1.0)
        
    Returns:
        str: Generated text response
    """
    if not is_ollama_active():
        if not ollama_start():
            return "Error: Ollama service is not running and could not be started"
    
    try:
        cmd = ["ollama", "run", model, "-p", prompt]
        
        if system_prompt:
            cmd.extend(["--system", system_prompt])
            
        cmd.extend(["--temperature", str(temperature)])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
            
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def create_chat_completer() -> Any:
    """
    Create a completer for the chat interface.
    
    Returns:
        A completer object with words property containing common commands
    """
    class SimpleCompleter:
        def __init__(self):
            self.words = [
                "exit", "quit", "help", "clear", 
                "model", "list", "temperature"
            ]
    
    return SimpleCompleter() 