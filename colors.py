####################################################
# ENVVARS
#
# debug=yes/no - prints debug messages
# caller=yes/no - prints caller filename
#
####################################################

import os
import inspect

class colors:
	RED = '\033[91m'
	GREEN = '\033[92m'
	YELLOW = '\033[93m'
	BLUE = '\033[94m'
	MAGENTA = '\033[95m'
	PURPLE = '\033[38;5;105m'
	PINK = '\033[95m'
	BLACK = '\033[90m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
	ENDC = '\033[0m'

def print_debug(str_):
	if _env_bool("debug"):
		_print(color(str(str_), colors.BLUE), prefix=color("[d]", colors.MAGENTA))

def color(s, color):
	return color + str(s) + colors.ENDC

def print_info(str):	
	_print(str, prefix=color("[i]", colors.PURPLE))

def print_ok(str):
	_print(str, prefix=color("[+]", colors.GREEN))

def print_error(str):
	_print(str, prefix=color("[-]", colors.RED))

def print_warning(str):
	_print(str, prefix=color("[!]", colors.YELLOW))
	
#prints on the last line of terminal
def print_last(str):
	print(color("[?]", colors.BLUE), str+"\r", end="", flush=True)

def black(str):
	return colors.BLACK + str + colors.ENDC

def bold(str):
	return colors.BOLD + str + colors.ENDC

#################################
# prviate functions

def _env(name, default=""):
	return os.environ.get(name.upper(), os.environ.get(name.lower(), default)).lower()

def _env_bool(name):
	env = _env(name)
	return env == "yes" or env == "true" or env == "y" or env == "1"

def _get_caller_prefix():
	if not _env_bool("caller"):
		return ""
	caller_name = inspect.stack()[3].filename
	if "/" in caller_name:
		while caller_name.endswith("/"):
			caller_name = caller_name[:-1]
		caller_name = caller_name.split("/")[-1]
	caller = " ["+color(caller_name, colors.PURPLE)+"]"
	return caller

def _print(str, prefix=""):
	caller = _get_caller_prefix()
	print(prefix+caller, str)
