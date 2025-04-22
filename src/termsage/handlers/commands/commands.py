import subprocess
import ollama 

class CommandStruct:
    def __init__(self, command=None, args=None):
        self.command = command
        self.args = args
        
    def execute_command(self):
        """Execute the stored command with its arguments"""
        if self.command:
            try:
                result = subprocess.run([self.command] + (self.args or []), 
                                        capture_output=True, text=True)
                return result.stdout
            except Exception as e:
                return f"Error executing command: {str(e)}"
        return "No command specified"
    
    def run_ollama_query(self, model="llama3", prompt=""):
        """Run a query using ollama with the specified model"""
        try:
            # Use subprocess to call ollama directly instead of using the Python API
            # as the chat method might not be available in some ollama versions
            cmd = ["ollama", "run", model, "-p", prompt]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return f"Error: {result.stderr}"
                
            return result.stdout.strip()
        except Exception as e:
            return f"Error with Ollama: {str(e)}"
    