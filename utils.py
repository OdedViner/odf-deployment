"""
This module contains various common utility function which are used across project
"""
import logging
import shlex
import subprocess

log = logging.getLogger(__name__)


def exec_cmd(
    cmd,
    timeout=600,
    silent=False,
    use_sudo=False,
    **kwargs,
):
    """
    Run an arbitrary command locally
    If the command is grep and matching pattern is not found, then this function
    returns "command terminated with exit code 1" in stderr.
    Args:
        cmd (str): command to run
        timeout (int): Timeout for the command, defaults to 600 seconds.
        silent (bool): If True will silent errors from the server, default false
        use_sudo (bool): If True cmd will be executed with sudo
    Raises:
        CommandFailed: In case the command execution fails
    Returns:
        (CompletedProcess) A CompletedProcess object of the command that was executed
        CompletedProcess attributes:
        returncode (str): The exit code of the process, negative for signals.
        stdout     (str): The standard output (None if not captured).
        stderr     (str): The standard error (None if not captured).
    """
    if use_sudo:
        cmd = f"sudo {cmd}"
    log.info(f"Executing command: {cmd}")
    if isinstance(cmd, str) and not kwargs.get("shell"):
        cmd = shlex.split(cmd)
    completed_process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        timeout=timeout,
        **kwargs,
    )
    if len(completed_process.stdout) > 0:
        log.info(f"Command stdout: {completed_process.stdout.decode()}")
    else:
        log.info("Command stdout is empty")

    if len(completed_process.stderr) > 0:
        if not silent:
            log.info(f"Command stderr: {completed_process.stderr.decode()}")
    else:
        log.info("Command stderr is empty")
    log.info(f"Command return code: {completed_process.returncode}")
    return completed_process
