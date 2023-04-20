import uuid
import subprocess

def exec_command(cmd) -> str:
    """
    Executes a command and returns the output
    :param cmd The command to be executed
    """
    print(f"Ejecutando.... ", cmd)
    # proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    #stdout, stderr = proc.communicate()
    #return stdout
    print(f"Salida.... ", proc.stdout)
    return proc.stdout

def generate_uuid():
    """
    Generates a uuid v4
    """
    return uuid.uuid4()