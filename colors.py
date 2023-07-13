####################################################
# ENVVARS
#
# debug=yes/no  - prints debug messages
# caller=yes/no - prints caller filename
# colors=yes/no - enables colors
#
####################################################

import os
import inspect

class colors:
	RED = '\033[38;5;196m'
	DARK_RED = '\033[38;5;124m'
	PINK = '\033[38;5;198m'
	
	DARK_GREEN = '\033[38;5;34m'
	GREEN = '\033[38;5;107m'
	LIME = '\033[38;5;149m'
	
	YELLOW = '\033[38;5;190m'
	LIGHT_YELLOW = '\033[38;5;229m'
	
	DARK_BLUE = '\033[38;5;21m'
	BLUE = '\033[38;5;135m'
	LIGHT_BLUE = '\033[38;5;147m'

	DARK_PURPLE = '\033[38;5;90m'
	PURPLE = '\033[38;5;163m'
	LIGHT_PURPLE = '\033[38;5;200m'

	DARK_ORANGE = '\033[38;5;64m'
	ORANGE = '\033[38;5;172m'
	LIGHT_ORANGE = '\033[38;5;208m'
	
	MAGENTA = '\033[38;5;213m'
	
	BLACK = '\033[38;5;238m'
	DARK_GRAY = '\033[38;5;242m'
	GRAY = '\033[38;5;245m'
	LIGHT_GRAY = '\033[38;5;250m'
	WHITE = '\033[38;5;15m'
	
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
	ENDC = '\033[0m'

def test_colors():
	for k, v in vars(colors).items():
		if type(v) == type(""):
			print(v+k)

def print_debug(str_):
	if _env_bool("debug"):
		_print(color(str(str_), colors.PURPLE), prefix=color("[d]", colors.MAGENTA))

def color(s, color):
	if _env("colors", default="yes") != "yes" and _env("colors", default="yes") != "y" and _env("colors", default="yes") != "t" and _env("colors", default="yes") != "true" and _env("colors", default="yes") != "":
		return str(s)
	else:
		return color + str(s) + colors.ENDC
			
def print_info(str):	
	_print(str, prefix=color("[i]", colors.BLUE))

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
