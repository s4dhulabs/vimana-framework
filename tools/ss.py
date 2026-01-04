
import os
import re
import time
from time import sleep
import datetime 
from neotermcolor import colored as cl
from concurrent.futures import ThreadPoolExecutor
from res.regex.secrets import secrets as secrets_regex


class tool:
    """
    A  tool for processing exceptions metadata looking for common secret patterns.

    Args:
        handler (dict, optional): A dictionary representing the handler. Defaults to False.

    Methods:
        __init__(self, handler: dict = False): Initializes the tool object with a handler.
        process_exception(self, exception): Processes the given exception.
        run(self, _exceptions_: list = False): Runs the tool with a list of exceptions.
    """

    def __init__(self, handler: dict = False):
        self.vmnf_handler = handler

    def process_exception(self, exception):
        self.pattern_match = False
        xid = exception.exception_id
        exception = exception.exception_meta
        summary = exception['summary']
        exception_type = summary.get('Exception Type')
        app_response = exception['app_response']

        for re_type, regex in secrets_regex.items():
            status = (
                f"    + Scanning {cl(exception_type,'red')} " 
                f"({xid}) metadata for {cl(re_type, 11, 988)} patterns..."
            )
            print(status.ljust(os.get_terminal_size().columns - 1), end="\r")
            sleep(0.01)

            rgx_check = re.search(regex, app_response)

            if rgx_check:
                print(f"              {cl(rgx_check.group(), 'red')}")

    def run(self, _exceptions_: list = False):
        if not _exceptions_:
            return False

        start_time = time.time()
        self.total_exceptions = len(_exceptions_)
        with ThreadPoolExecutor() as executor:
            executor.map(self.process_exception, _exceptions_)

        runtime = time.time() - start_time
        runtime = str(datetime.timedelta(seconds=runtime))

        if not self.pattern_match:
            print()
            print(
                f"\t secretscan: {runtime} → {self.total_exceptions} exceptions processed "
                f"with {len(secrets_regex)} patterns. - No secrets found."
            )

            input()
        return True



