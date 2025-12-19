# Source - https://stackoverflow.com/a
# Posted by Sergey Pleshakov, modified by community. See post 'Timeline' for change history
# Retrieved 2025-12-12, License - CC BY-SA 4.0

import logging

CONTEXT = "NOT SET"

class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format_o = "%(asctime)s - %(levelname)s - 🥺👉👈: %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format_o + reset,
        logging.CRITICAL: bold_red + format_o + reset  
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        global CONTEXT  # not even needed for reading, but makes it clear
        prefix = f"[{CONTEXT}] " if CONTEXT else ""

        return prefix + super().format(record)


import pprint
def myprint(var):
    nicevar = pprint.pformat(globals()[var], indent=1 , width=100)
    logger.debug(f"{var}:\n{nicevar}")


def myprint2(var):
    logger.debug(f"{var}:\n{globals()[var]}")

import inspect


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

ch.setFormatter(CustomFormatter())

logger.addHandler(ch)
logger.propagate = False

from rich.logging import RichHandler
logging.basicConfig(format='%(funcName)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', 
                    handlers=[RichHandler()],
                    level=logging.INFO)

def vlog(var_name: str, level=logging.INFO):
    """Log a variable with its name and value from the caller's scope"""
    # Get the caller's frame
    frame = inspect.currentframe().f_back
    
    # Try to find the variable in caller's locals first, then globals
    try:
        if var_name in frame.f_locals:
            value = frame.f_locals[var_name]
        elif var_name in frame.f_globals:
            value = frame.f_globals[var_name]
        else:
            logger.error(f"Variable '{var_name}' not found in caller's scope")
            return
        
        nicevar = pprint.pformat(repr(value), indent=1 , width=100)
        
        logging.log(level, f"{var_name}:\n{nicevar}")
    finally:
        # Clean up frame reference to avoid reference cycles
        del frame

