import asyncio
import subprocess
import os
import shutil

async def run_cci_command(command: str) -> str:
    """
    Run a CumulusCI command asynchronously.
    
    Args:
        command: The CCI command to run (without the 'cci' prefix)
        
    Returns:
        str: The command output or error message
    """
    # Check if CCI is available
    if not shutil.which("cci"):
        return "Error: CumulusCI (cci) is not installed or not in PATH"
    
    # Prepare the full command
    full_command = f"cci {command}"
    
    try:
        # Run the command asynchronously
        process = await asyncio.create_subprocess_shell(
            full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        stdout, stderr = await process.communicate()
        
        # Decode the output
        stdout_text = stdout.decode('utf-8').strip()
        stderr_text = stderr.decode('utf-8').strip()
        
        if process.returncode == 0:
            return f"Command '{full_command}' completed successfully:\n{stdout_text}"
        else:
            error_msg = f"Command '{full_command}' failed with return code {process.returncode}"
            if stderr_text:
                error_msg += f"\nError: {stderr_text}"
            if stdout_text:
                error_msg += f"\nOutput: {stdout_text}"
            return error_msg
            
    except Exception as e:
        return f"Error running command '{full_command}': {str(e)}"