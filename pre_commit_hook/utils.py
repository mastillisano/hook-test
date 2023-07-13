import uuid
import subprocess

def exec_async_command(cmd) -> str:
    """
    Executes a command and returns the output
    :param cmd The command to be executed
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate()
    return stdout


def exec_sync_command(cmd) -> str:
    """
    Executes a command and returns the output
    :param cmd The command to be executed
    """
    proc = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    return proc.decode('utf-8').strip()


def generate_uuid():
    """
    Generates a uuid v4
    """
    return uuid.uuid4()