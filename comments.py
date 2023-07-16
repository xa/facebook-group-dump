import requests, html, json, sys, io, time, re, math, os, traceback
import fix_html
from datetime import datetime
from urllib.parse import unquote
from colors import *
import traceback
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

class ParseException(Exception):
	pass

try:
	GROUP_ID = sys.argv[1]
	DIRECTORY = sys.argv[3]
	if not DIRECTORY.endswith("/"):
		DIRECTORY += "/"

	saved_group_id_path = DIRECTORY+"group_id.txt"
	if GROUP_ID == "unknown" or GROUP_ID == "?" or GROUP_ID == "guess" or GROUP_ID == "idk":
		try:
			with open(saved_group_id_path) as f:
				GROUP_ID = f.read().strip()
				print(GROUP_ID)
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
		account = __import__(sys.argv[2].replace(".py", ""), globals(), locals(), ['headers', 'cookies'], 0)

		headers = account.headers
		cookies = account.cookies
	except:
		traceback.print_exc()
		raise ValueError()
except:
	print()
	print_info("Usage: python3 "+sys.argv[0]+" <group id> <account> <save to>")
	print_info("Example: python3 "+sys.argv[0]+" 4633413245961 account.py dump_fav_group")
	print()
	exit()

#fuck windows
sys.stdout = io.open(sys.stdout.fileno(), 'w', encoding='utf8')
from selenium.webdriver.chrome.options import Options

#print_ok(f"Dumping comments from {GRO‏UP‏_ID‏}")
print_ok(bold(color("Dumping comments from "+GROUP_ID+"...‏", colors.GREEN)))

from selenium import webdriver
from PIL import Image

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

def dump_date(date, id): 
	#driver = webdriver.Chrome()
	#chrome_options = Options()
	#chrome_options.add_argument('--user-agent=')
	path = DIRECTORY+"json/"+date+"/"+id+"_comments/"

	try:
		os.mkdir(path)
	except:
		if not os.path.exists(path+"index_dirty.html") and os.path.exists(path+"index.html"):
			flag = True
			# open json of post and check if index.html contains text post
			with open(path+"index.html", encoding="utf8") as f:
				if "Wygląda na to, że ta funkcja była przez Ciebie wykorzystywana w zbyt szybki, niewłaściwy sposób. Możliwość korzystania z niej została w Twoim przypadku tymczasowo zablokowana." in f.read():
					print_error("Rate limited "+path)
					flag = False
			if os.path.exists(path+"media") and flag:
				files = os.listdir(path+"media")
				if len(files) > 0:
					print_warning(path+" exists!")
					return False

	print()
	print_ok(color("Dumping "+file+", "+post_id, colors.GREEN))
	print()
						
	opts = webdriver.FirefoxOptions()
	opts.add_argument("--width=800")
	opts.add_argument("--height=1000")
	opts.set_preference("general.useragent.override", "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/.1")
	driver = webdriver.Firefox(options=opts)
	driver.minimize_window()
	driver.set_window_size(800, 1000)
	driver.set_window_position(9999, 1000)
	driver.get("http://m.facebook.com")

	cookies2 = {}
	for k, v in cookies.items():
		driver.add_cookie({"name": k, "value": v, "domain": "m.facebook.com"})

	#https://m.facebook.com/groups/80###########77?view=permalink&id=10#########36&comment_option=recent_activity
	driver.get("https://m.facebook.com/groups/"+GROUP_ID+"?view=permalink&id="+id+"&comment_option=recent_activity")
	
	element = driver.find_element(By.ID, "viewport")
	#time.sleep(100)
	
	while True:
		time.sleep(1)
		el1 = driver.find_elements("xpath", "//*[contains(text(), 'Pokaż wcześniejsze komentarze')]");
		el2 = driver.find_elements("xpath", '//a[contains(@href,"/comment/replies/")]');
		el3 = driver.find_elements("xpath", "//*[contains(text(), 'Zobacz wcześniejsze odpowiedzi')]")
		el4 = driver.find_elements("xpath", "//*[contains(text(), 'Zobacz więcej komentarzy')]")
		el = el1+el2+el3+el4
		print_info(str(len(el))+" elements to click")
		if len(el) > 0:
			el[0].click()
		else:
			break

	time.sleep(1)
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
		os._exit(0)
		
	with open(path+'/index_dirty.html', 'w+', encoding="utf-8") as fp:
		fp.write("<!DOCTYPE html>\n"+content)

	el = driver.find_elements("xpath", "//*[@href or @src]")
	bigcss = "‏‏html, body, form, fieldset, table, tr, td, img { font-family: Arial !important; }\n\n"
	downloaded_css = []
	for e in el:
		link = e.get_attribute('href')
		if link and ".css" in link:
			#print(link)
			while True:
				try:
					if link in downloaded_css:
						print_info("Css cached‏ " + link)
					print_info("Downloading css‏ " + link)
					con = requests.get(link, headers=headers, cookies=cookies)
					css = con.content.decode()
					downloaded_css.append(link)
					if "{" in css:
						bigcss += css.replace("font-family", "font-gowno") + "\n\n"
						break
				except KeyboardInterrupt:
					os._exit(0)
				except:
					traceback.print_exc()
					print("error_retry")
	
	bigcss = bigcss.replace("f5f6f7", "ffffff").replace("cursor:pointer", "cursor:default").replace("cursor: pointer", "cursor: default")
	bigcss += "\n\nhtml, body {cursor: default !important;}"
	bigcss += "\n\nbody {padding-top: 25px; padding-right: 20px; padding-left: 5px;}"
	bigcss += "\n\n._2b04 {margin-top: 17px;}"
	#bigcss += "\n\nimg {max-width: 100%; height: auto;}"
	#bigcss += "\n\nvideo {max-width: 100%; height: auto;}"
	
	with open(path+"/style.css", "w+", encoding="utf-8") as f:
		f.write(bigcss)
		
	#for e in el:
	#	print(e.get_attribute("src"))
	driver.close()

	try:
		fix_html.fix(path, id, headers, cookies)
	except KeyboardInterrupt:
		print_warning("Wait for fix_html to finish its job")
		pass
		
	print_ok("Done.")
		
	return True

#GROUP_ID = "xxxxxxxxxx"
#dump_date("2023-05-23", "xxxxxxxxxx")
#exit()	
	
for file in reversed(os.listdir(DIRECTORY+"json")):
	if file != "dates.txt":
		for js in os.listdir(DIRECTORY+"json/"+file):
			if js != "posts.txt" and ".json" in js:
				while True:
					try:
						post_id = js.replace(".json", "")
						sleep = dump_date(file, post_id)
						try:
							if sleep:
								time.sleep(2)
						except KeyboardInterrupt:
							os._exit(0)
						break
					except KeyboardInterrupt:
						 os._exit(0)
					except:
						traceback.print_exc()
		
