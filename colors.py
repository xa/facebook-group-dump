import os, re, shutil, threading, inspect, time, random

##################################################################
# AUTHOR
#  kcx
#  @xa on github
#
##################################################################

##################################################################
# USAGE
#  refer to _test_msgs function, it covers most of the usercases
#
##################################################################

##################################################################
# ENVVARS
#	
#  defaults to yes
#   log_fatal=yes/no  - prints fatal errors 
#   log_success=yes/no  - prints success messages 
#   log_error=yes/no  - prints error messages 
#   log_warn=yes/no  - prints error messages 
#   log_info=yes/no  - prints debug messages 
#   log_last=yes/no  - prints last line messages
#
#  defaults to no:
#   log_debug=yes/no  - prints debug messages
#   log_temp=yes/no  - prints temp messages
#   log_spam=yes/no  - prints spam messages
#
#    --- misc ---
#
#  defaults to no:
#   caller=yes/no - prints caller filename
#
#  defaults to yes:
#   colors=yes/no - enables colors
#
##################################################################

##################################################################
# ENV API
_env_dbg = False
def _env(name, default=""):
	return os.environ.get(name.upper(), os.environ.get(name.lower(), default)).lower()
def _env_bool(name, default=False):
	global _env_dbg
	if _env_dbg == True: return True
	env = _env(name, default="yes" if default == True else "no")
	return env == "yes" or env == "true" or env == "y" or env == "1"
#
##################################################################

class aligns:
	LEFT = 0
	CENTER = 1
	RIGHT =  2

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

COLOR_CHARS = []

for k, v in vars(colors).items():
	if type(v) == type("") and type(k) == type("") and not k.startswith("__"):
		COLOR_CHARS.append(v)

colors.SEP = colors.ENDC + colors.GRAY + colors.BOLD + "  ::  " + colors.ENDC

def color(s, color):
	if color == None:
		return str(s)
	if _env("colors", default="yes") != "yes" and _env("colors", default="yes") != "y" and _env("colors", default="yes") != "t" and _env("colors", default="yes") != "true" and _env("colors", default="yes") != "":
		return str(s)
	else:
		return color + str(s) + colors.ENDC

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
def decolorize(s):
	return ansi_escape.sub("", s)

class prefixes:
	FATAL   = color("[O]", colors.DARK_RED)
	SUCCESS = color("[+]", colors.GREEN)
	ERROR   = color("[-]", colors.RED)
	WARN    = color("[!]", colors.YELLOW)
	INFO    = color("[i]", colors.BLUE)
	DEBUG   = color("[d]", colors.MAGENTA)
	TEMP    = color("[@]", colors.GRAY)
	SPAM    = color("[x]", colors.DARK_GRAY)

	LAST    = color("[?]", colors.BLUE)

printed_last = False
printed_last_lock = threading.Lock()

def print_fatal(s, align=aligns.LEFT, autocolor=None, print_caller=False):
	if _env_bool("log_fatal", True):
		_print(s, prefix=prefixes.FATAL, align=align, autocolor=autocolor, print_caller=print_caller)

def print_success(s, align=aligns.LEFT, autocolor=None, print_caller=False):
	if _env_bool("log_success", True):
		_print(s, prefix=prefixes.SUCCESS, align=align, autocolor=autocolor, print_caller=print_caller)

print_ok = print_success #backwards comp

def print_error(s, align=aligns.LEFT, autocolor=None, print_caller=False):
	if _env_bool("log_error", True):
		_print(s, prefix=prefixes.ERROR, align=align, autocolor=autocolor, print_caller=print_caller)

print_err = print_error #backwards comp

def print_warn(s, align=aligns.LEFT, autocolor=None, print_caller=False):
	if _env_bool("log_warn", True):
		_print(s, prefix=prefixes.WARN, align=align, autocolor=autocolor, print_caller=print_caller)

print_warning = print_warn #backwards comp

def print_info(s, align=aligns.LEFT, autocolor=None, print_caller=False):	
	if _env_bool("log_info", True):
		_print(s, prefix=prefixes.INFO, align=align, autocolor=autocolor, print_caller=print_caller)

def print_debug(s, align=aligns.LEFT, autocolor=None, print_caller=False):
	if _env_bool("log_debug", False):
		_print(s, prefix=prefixes.DEBUG, align=align, autocolor=autocolor, print_caller=print_caller)

def print_temp(s, align=aligns.LEFT, autocolor=None, print_caller=False):
	if _env_bool("log_temp", False):
		_print(s, prefix=prefixes.TEMP, align=align, autocolor=autocolor, print_caller=print_caller)

def print_spam(s, align=aligns.LEFT, autocolor=None, print_caller=False):
	if _env_bool("log_spam", False):
		_print(s, prefix=prefixes.SPAM, align=align, autocolor=autocolor, print_caller=print_caller)
	
#prints on the last line of terminal
def print_last(s, align=aligns.LEFT, autocolor=None, print_caller=False):
	global printed_last, printed_last_lock
	if _env_bool("log_last", True):
		#with printed_last_lock:
		_print(s, prefix=prefixes.LAST, end="\r", flush=True, align=align, print_caller=print_caller)
		printed_last = True
	
def black(str):
	return colors.BLACK + str + colors.ENDC

def bold(str):
	return colors.BOLD + str + colors.ENDC

#################################
# private functions

def _get_caller_prefix(force=False):
	if not _env_bool("caller") and not force:
		return ""
	caller_name = inspect.stack()[3].filename
	if "/" in caller_name:
		while caller_name.endswith("/"):
			caller_name = caller_name[:-1]
		caller_name = caller_name.split("/")[-1]
	caller = "["+color(caller_name, colors.PURPLE)+"]"
	return caller

def _print(s, prefix="#", end="\r\n", flush=True, last_print=True, align=aligns.LEFT, autocolor=None, print_caller=False):
	global printed_last
	caller = _get_caller_prefix(force=print_caller)
	columns, rows = shutil.get_terminal_size()
	if len(caller) == 0:
		s_prefixed = " "+prefix+" "+color(s, autocolor)
	else:
		s_prefixed = " "+prefix+" "+caller+" "+color(s, autocolor)
	repeat = 0
	s_nocolor = decolorize(s_prefixed)
	if align == aligns.CENTER:
		repeat = int(columns/2-len(s_nocolor)/2)
	if align == aligns.RIGHT:
		repeat = int(columns)-len(s_nocolor)-1
	align_str = " " * repeat
	s_aligned = align_str+s_prefixed
	with printed_last_lock:		
		if printed_last or prefix == prefixes.LAST:
			printed_last = False
			clear_rest = " "*(columns-len(s_aligned))
			print(s_aligned+clear_rest, end=end, flush=flush)
		else:
			print(s_aligned, end=end, flush=flush)

	if last_print:
		print("\r", end="", flush=True)

def _test_colors():
	print_info("Colors list: ")
	s = ""
	for k, v in vars(colors).items():
		if type(v) == type("") and type(k) == type("") and not k.startswith("__"):
			s += v+k+colors.ENDC+"  "
	print_info("  "+s.strip())

def _test_msgs():
	# log all
	global _env_dbg
	_env_dbg = True
	
	#build debug str
	s = ""
	for k, v in vars(colors).items():
		if type(v) == type("") and type(k) == type("") and not k.startswith("__"):
			s += v+random.choice([":D", "xD", ":)", ":P", ":3"]) + colors.ENDC + " "
			
	#print all levels	
	print()
	print_fatal(s)
	print_success(s)
	print_ok(s)
	print_error(s)
	print_err(s)
	print_warn(s)
	print_warning(s)
	print_info(s)
	print_debug(s)
	print_temp(s)
	print_spam(s)

	_env_dbg = False
	print()
	
	#align
	for _ in range(2):
		print_ok("left align", align=aligns.LEFT)
	for _ in range(2):
		print_ok("center align", align=aligns.CENTER)
	for _ in range(2):
		print_ok("right align", align=aligns.RIGHT)

	print()
	print_ok(color("Multi", colors.RED)+color(" color support.", colors.YELLOW), align=aligns.CENTER)
	print_ok(bold(color("Bold text", colors.GRAY)), align=aligns.CENTER)
	print_info(123456789, align=aligns.CENTER) # auto conversion to strings

	#print on last line
	for i in range(250):
		print_last("Example of printing to last line: "+str(i), align=aligns.CENTER)
		time.sleep(0.01)

	for i in range(10):
		print_last("~"*(10-i), align=aligns.CENTER)
		time.sleep(0.05)

	#easy coloring
	print_ok("autocolor green", autocolor=colors.GREEN)
	print_ok("autocolor red", autocolor=colors.RED)
	print_ok("Print caller.", print_caller=True)

#run tests
if __name__ == "__main__":
	print()
	_test_colors()
	_test_msgs()
	print()