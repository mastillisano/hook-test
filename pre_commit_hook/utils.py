import os
import uuid
import subprocess

def is_check_skipped() -> bool:
    """
    Returns the value of the environmental variable skip_credentials_check
    """
    try:
        return os.environ["skip_credentials_check"] == "true"
    except KeyError:
        return False

def exec_command(cmd) -> str:
    """
    Executes a command and returns the output
    :param cmd The command to be executed
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate()
    return stdout

def generate_uuid():
    """
    Generates a uuid v4
    """
    return uuid.uuid4()