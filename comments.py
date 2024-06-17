import requests, html, json, sys, io, time, re, math, os, traceback, random, atexit
import fix_html
from datetime import datetime
from urllib.parse import unquote
from colors import *
import traceback
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

class ParseException(Exception):
	pass

#fuck windows
sys.stdout = io.open(sys.stdout.fileno(), 'w', encoding='utf8')
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from PIL import Image

def set_windows_title(s):
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(s)
    except:
        pass

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
    'Accept': 'image/avif,image/webp,*/*',
    'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
    'Connection': 'keep-alive',
    'Referer': 'https://facebook.com',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

def time_sleep(s):
	a = s
	delay = 0.1
	while a > 0:
		print_last("Sleeping for "+color("{:.1f}s".format(max(0, a)), colors.GRAY))
		a -= delay
		time.sleep(delay)

def create_driver():
	opts = webdriver.FirefoxOptions()
	opts.add_argument("--width=800")
	opts.add_argument("--height=1000")
	opts.set_preference("general.useragent.override", "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/.1")
	driver = webdriver.Firefox(options=opts)
	#driver.minimize_window()
	#driver.set_window_position(9999, 1000)
	driver.set_window_size(800, 1000)
	driver.get("http://m.facebook.com")
	
	cookies2 = {}
	for k, v in cookies.items():
		driver.add_cookie({"name": k, "value": v, "domain": "m.facebook.com"})

	return driver

def dump_date(driver, date, post_id, json_obj): 
	path = DIRECTORY+"json/"+date+"/"+post_id+"_comments/"

	try:
		os.mkdir(path)
	except:
		#if not os.path.exists(path+"index_dirty.html") and os.path.exists(path+"index.html"):
		if os.path.exists(path+"index.html"):
			flag = True
			# open json of post and check if index.html contains text post
			with open(path+"index.html", encoding="utf8") as f:
				st = f.read()
				if "Wygląda na to, że ta funkcja była przez Ciebie wykorzystywana w zbyt szybki, niewłaściwy sposób. Możliwość korzystania z niej została w Twoim przypadku tymczasowo zablokowana." in st:
					print_error("Rate limited "+path)
					flag = False

			#with open(path+"index.html", "w", encoding="utf8") as f:
			#	f.write(st.replace("width:40px;height:40px; top:9px", "width:40px;height:40px;"))

			if os.path.exists(path+"media") and flag:
				files = os.listdir(path+"media")
				if len(files) > 0:
					print_warning(path+" exists!")
					return False

	print()
	print_ok(color("Dumping "+date+", "+post_id, colors.GREEN))
	print()
	
	#https://m.facebook.com/groups/80###########77?view=permalink&id=10#########36&comment_option=recent_activity
	ur = "https://m.facebook.com/groups/"+GROUP_ID+"?view=permalink&id="+post_id+"&comment_option=toplevel"
	print_info(ur)
	driver.get(ur)
	
	content = driver.page_source
	if "Zezwolić na użycie plików cookie z Facebook w tej przeglądarce?" in content:
		print_fatal("Burned session (cookies not accepted)")
		exit()
	if "Zaloguj się do konta" in content or 'value="Dołącz do grupy"' in content:
		print_fatal("Burned session (logged out)")
		exit()
	
	#element = driver.find_element(By.NAME, "comment_switcher")
	
	#time_sleep(1000)
	element = driver.find_element(By.ID, "viewport")
	#time_sleep(100)
	
	clicks = 0
	
	while True:
		time_sleep(7+random.randrange(100, 500)/100)
		el1 = driver.find_elements("xpath", "//*[contains(text(), 'Pokaż wcześniejsze komentarze')]");
		el2 = driver.find_elements("xpath", '//a[contains(@href,"/comment/replies/")]');
		el3 = driver.find_elements("xpath", "//*[contains(text(), 'Zobacz wcześniejsze odpowiedzi')]")
		el4 = driver.find_elements("xpath", "//*[contains(text(), 'Zobacz więcej komentarzy')]")
		el = el1+el2+el3+el4
		print_info(str(len(el))+" elements to click")
		if len(el) > 0:
			el[0].click()
			clicks += 1
		else:
			break

	time_sleep(1)
	location = element.location
	size = element.size
	
	# Ref: https://stackoverflow.com/a/52572919/
	#original_size = driver.get_window_size()
	#required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
	#required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
	#driver.set_window_size(required_width, required_height)
	# driver.save_screenshot(path)  # has scrollbar
	#	 driver.find_element(By.TAG_NAME, 'body').screenshot("shot.png")  # avoids scrollbar
	#driver.set_window_size(original_size['width'], original_size['height'])
	
	content = driver.page_source
	if "Wygląda na to, że ta funkcja była przez Ciebie wykorzystywana w zbyt szybki, niewłaściwy sposób." in content:
		print_error("Rate limit")
		os_exit(0)
		
	with open(path+'/index_dirty.html', 'w+', encoding="utf-8") as fp:
		fp.write("<!DOCTYPE html>\n"+content)

	el = driver.find_elements("xpath", "//*[@href or @src]")
	bigcss = "‏‏html, body, form, fieldset, table, tr, td, img { font-family: Arial !important; }\n\n"
	downloaded_css = []
	session = requests.Session()
	for e in el:
		link = e.get_attribute('href')
		if link and ".css" in link:
			#print(link)
			link = link.strip()
			while True:
				try:
					if link in downloaded_css:
						print_info("Css cached " + color(link, colors.GREEN))
					print_info("Downloading css " + color(link, colors.GREEN))
					con = session.get(link, headers=headers, cookies=cookies)
					css = con.content.decode()
					downloaded_css.append(link)
					if "{" in css:
						bigcss += css.replace("font-family", "font-gowno") + "\n\n"
						break
				except KeyboardInterrupt:
					os_exit(0)
				except:
					traceback.print_exc()
					print_error("error_retry")
	
	bigcss = bigcss.replace("f5f6f7", "ffffff").replace("cursor:pointer", "cursor:default").replace("cursor: pointer", "cursor: default")
	bigcss += "\n\nhtml, body {cursor: default !important;}"
	bigcss += "\n\nbody {padding-top: 25px; padding-right: 20px; padding-left: 5px;}"
	bigcss += "\n\n._2b04 {margin-top: 17px;}"

	with open(path+"/style.css", "w+", encoding="utf-8") as f:
		f.write(bigcss)
		
	#driver.close()

	try:
		elements_count = fix_html.fix(path, post_id, headers, cookies)
	except KeyboardInterrupt:
		print_warning("Wait for fix_html to finish its job")
		pass
		
	nowtime = int(time.time())
	
	final_json = {}

	final_json["post"] = json_obj
	final_json["comments"] = {
		"dumped_at": str(nowtime),
		"comments_count": elements_count, #this may be wrong
		"clicks": clicks #how many times comments were unrolled
	}
	
	with open(path+'/metadata.json', 'w+', encoding="utf-8") as fp:
		fp.write(json.dumps(final_json, indent=4))
		
	print_ok("Done.")
		
	return True

#GROUP_ID = "xxxxxxxxxx"
#dump_date("2023-05-23", "xxxxxxxxxx")
#exit()	

def dump_all(driver):
	#for date in reversed(os.listdir(DIRECTORY+"json")):
	for date in os.listdir(DIRECTORY+"json"):
		if date != "dates.txt":
			for js in os.listdir(DIRECTORY+"json/"+date):
				if js != "posts.txt" and ".json" in js:
					while True:
						try:
							path = DIRECTORY+"json/"+date+"/"+js

							with open(path, encoding="utf-8") as f:
								obj = json.loads(f.read())
							
							print_debug(obj)
							
							post_id = js.replace(".json", "")
							sleep = dump_date(driver, date, post_id, obj)
							try:
								if sleep:
									time_sleep(10)
							except KeyboardInterrupt:
								os_exit(0)
							break
						except KeyboardInterrupt:
							 os_exit(0)
						except:
							traceback.print_exc()
			
def cleanup_driver():
	try:
		if driver:
			driver.close()
			print_ok("Closed webdriver")
	except:
		print_error("Couldn't cleanup webdriver")
		
def os_exit(a):
	cleanup_driver()
	os._exit(a)
			
if __name__ == "__main__":
	try:
		GROUP_ID = sys.argv[1]
		DIRECTORY = sys.argv[3]
		if not DIRECTORY.endswith("/"):
			DIRECTORY += "/"

		saved_group_id_path = DIRECTORY+"group_id.txt"
		if GROUP_ID.lower() in ["unknown", "?", "guess", "idk"]:
			try:
				with open(saved_group_id_path) as f:
					GROUP_ID = f.read().strip()
					#print(GROUP_ID)
			except:
				print_error("No saved group id. Please specify in command line args.")
				exit()
				
		if os.path.exists(saved_group_id_path):
			with open(saved_group_id_path) as f:
				saved_group_id = f.read().strip()
				if saved_group_id != GROUP_ID.strip():
					print_error("Group id mismatch! "+color(GROUP_ID + " =/= " + saved_group_id, colors.RED))
					exit()
						
		try:
			account_name = sys.argv[2].replace(".py", "")

			if account_name.lower() in ["unknown", "?", "guess", "idk"]:
				try:
					with open(cached_account_path) as f:
						account_name = f.read().strip()
				except:
					print_error("No saved account name. Please specify in command line args.")
					exit()
					
			account = __import__(account_name, globals(), locals(), ['headers', 'cookies'], 0)

			headers = account.headers
			cookies = account.cookies
		except SystemExit:
			exit()
		except:
			traceback.print_exc()
			raise ValueError()
	except:
		print()
		print_info("Usage: python3 "+sys.argv[0]+" <group id> <account> <save to>")
		print_info("Example: python3 "+sys.argv[0]+" 4633413245961 account.py dump_fav_group")
		print()
		exit()

	#print_ok(f"Dumping comments from {GRO‏UP‏_ID‏}")
	print_ok(bold(color("Dumping comments from "+GROUP_ID+"...‏", colors.GREEN)))
	set_windows_title("comments.py "+DIRECTORY.split("/")[-2]+" / "+account_name)
	
	atexit.register(cleanup_driver)
	driver = create_driver()
	dump_all(driver)