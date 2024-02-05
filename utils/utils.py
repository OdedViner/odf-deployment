"""
This module contains various common utility function which are used across project
"""
import logging
import shlex
import subprocess
import time

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


class TimeoutSampler(object):
    """
    Samples the function output.

    This is a generator object that at first yields the output of function
    `func`. After the yield, it either raises instance of `timeout_exc_cls` or
    sleeps `sleep` seconds.

    Yielding the output allows you to handle every value as you wish.

    Feel free to set the instance variables.


    Args:
        timeout (int): Timeout in seconds
        sleep (int): Sleep interval in seconds
        func (function): The function to sample
        func_args: Arguments for the function
        func_kwargs: Keyword arguments for the function
    """

    def __init__(self, timeout, sleep, func, *func_args, **func_kwargs):
        self.timeout = timeout
        self.sleep = sleep
        # check that given timeout and sleep values makes sense
        if self.timeout < self.sleep:
            raise ValueError("timeout should be larger than sleep time")

        self.func = func
        self.func_args = func_args
        self.func_kwargs = func_kwargs

        # Timestamps of the first and most recent samples
        self.start_time = None
        self.last_sample_time = None
        # The exception to raise
        self.timeout_exc_cls = TimeoutError
        # Arguments that will be passed to the exception
        self.timeout_exc_args = [self.timeout]
        try:
            self.timeout_exc_args.append(
                f"Timed out after {timeout}s running {self._build_call_string()}"
            )
        except Exception:
            log.exception(
                "Failed to assemble call string. Not necessarily a test failure."
            )

    def _build_call_string(self):
        def stringify(value):
            if isinstance(value, str):
                return f'"{value}"'
            return str(value)

        args = list(map(stringify, self.func_args))
        kwargs = [f"{stringify(k)}={stringify(v)}" for k, v in self.func_kwargs.items()]
        all_args_string = ", ".join(args + kwargs)
        return f"{self.func.__name__}({all_args_string})"

    def __iter__(self):
        if self.start_time is None:
            self.start_time = time.time()
        while True:
            self.last_sample_time = time.time()
            if self.timeout <= (self.last_sample_time - self.start_time):
                raise self.timeout_exc_cls(*self.timeout_exc_args)
            try:
                yield self.func(*self.func_args, **self.func_kwargs)
            except Exception as ex:
                msg = f"Exception raised during iteration: {ex}"
                log.exception(msg)
            if self.timeout <= (time.time() - self.start_time):
                raise self.timeout_exc_cls(*self.timeout_exc_args)
            log.info("Going to sleep for %d seconds before next iteration", self.sleep)
            time.sleep(self.sleep)

    def wait_for_func_value(self, value):
        """
        Implements common usecase of TimeoutSampler: waiting until func (given
        function) returns a given value.

        Args:
            value: Expected return value of func we are waiting for.
        """
        try:
            for i_value in self:
                if i_value == value:
                    break
        except self.timeout_exc_cls:
            log.error(
                "function %s failed to return expected value %s "
                "after multiple retries during %d second timeout",
                self.func.__name__,
                value,
                self.timeout,
            )
            raise

    def wait_for_func_status(self, result):
        """
        Get function and run it for given time until success or timeout.
        (using __iter__ function)

        Args:
            result (bool): Expected result from func.

        Examples::

            sample = TimeoutSampler(
                timeout=60, sleep=1, func=some_func, func_arg1="1",
                func_arg2="2"
            )
            if not sample.wait_for_func_status(result=True):
                raise Exception

        """
        try:
            self.wait_for_func_value(result)
            return True
        except self.timeout_exc_cls:
            return False
