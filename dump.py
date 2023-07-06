import requests, html, json, sys, io, time, re, math, os, traceback
from datetime import datetime
from urllib.parse import unquote
from colors import *

#todo check groupid mismatch and accept finding out of groupid

def set_windows_title(s):
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(s)
    except:
        pass
        
class ParseException(Exception):
    pass

try:
	GROUP_ID = sys.argv[1]
	DIRECTORY = sys.argv[3]+"/"

	try:
		account_name = sys.argv[2].replace(".py", "")
		account = __import__(account_name, globals(), locals(), ['headers', 'cookies'], 0)

		headers = account.headers
		cookies = account.cookies
	except:
		traceback.print_exc()
		raise ValueError()
except:
	print()
	print_info("Usage: python3 "+sys.argv[0]+" <group id> <account> <save to>")
	print_info("Example: python3 "+sys.argv[0]+" 6351613231561 account.py dump_fav_group")
	print()
	exit()

#fuck windows
sys.stdout = io.open(sys.stdout.fileno(), 'w', encoding='utf8')

TAG_RE = re.compile(r'<[^>]+>')
dates_list = []

def remove_tags(text):
    return TAG_RE.sub('', text)

def format_text(text):
	newtext = []
	text = text.replace("<br />", "\n").replace("<br>", "\n").replace("<br/>", "\n").replace("<br >", "\n")
	for line in text.split("\n"):
		line = line.strip()
		newtext.append(line)
	return html.unescape(remove_tags("\n".join(newtext)))

def url_filename(url):
	url_ = url.split("?")[0] if "?" in url else url
	return url_.split("/")[-1]

def save_url(url, prefix):
	filename = url_filename(url)
	path = prefix+filename
	if not os.path.exists(path):
		with open(path, "wb") as f:
			f.write(requests.get(url).content)
		print_ok("Saved "+filename)
	return filename

def save_photo(photo):
	print_debug("Saving photo "+photo)
	url = "https://mbasic.facebook.com/photo/view_full_size/?fbid="+photo
	rsp = requests.get(url, cookies=cookies, headers=headers, allow_redirects=False)
	content = rsp.content.decode()
	if "Możliwość korzystania przez Ciebie z tej funkcji została tymczasowo zablokowana." in content:
		print_error("Photo save rate limit")
		exit()
	try:
		#print(url)
		#print(content)
		photo_url = content.split('meta http-equiv="refresh" content="0;url=')[1].split('"')[0]
		photo_url = html.unescape(photo_url)
		return save_url(photo_url, DIRECTORY+"medias/")
	except KeyboardInterrupt:
		raise KeyboardInterrupt
	except:
		traceback.print_exc()
		with open(DIRECTORY+"not_dumped_videos.txt", "a+", encoding='utf-8') as f:
			f.write(photo+"\n") 
		return photo+".mp4"

def save_video(video_url):
	print_debug("Saving video "+video_url[:200])
	return save_url(video_url, DIRECTORY+"medias/")

def reconstruct_reactions(element):
	#aria-label="2 reakcje, w tym Lubię to!"
	#18 reakcji, w tym Przykro mi, Trzymaj się i Lubię to!
	#4 reakcje, w tym Trzymaj się, Lubię to! i Super
	#1 reakcja, w tym Wow
	fixed = element.replace("reakcje", "reakcji").replace("reakcja", "reakcji")
    
	try:
		reactions_count = int(fixed.split(" reakcji, w tym")[0].split('aria-label="')[1])
	except:
		return {"like": 0, "love": 0, "wow": 0, "haha": 0, "sad": 0, "anger": 0, "care": 0}
	
	print_debug("Reactions count "+str(reactions_count))
	reactions_list_polish = html.unescape(fixed.split("reakcji, w tym ")[1].split('"')[0].replace(" i ", ", ")).split(", ")
	print_debug(reactions_list_polish)

	reactions_list = []
	for reaction in reactions_list_polish:
		if reaction.startswith("Lubię to"):
			reactions_list.append("like")
		elif reaction.startswith("Super"):
			reactions_list.append("love")
		elif reaction.startswith("Wow"):
			reactions_list.append("wow")
		elif reaction.startswith("Ha ha"):
			reactions_list.append("haha")
		elif reaction.startswith("Przykro mi"):
			reactions_list.append("sad")
		elif reaction.startswith("Wrr"):
			reactions_list.append("anger")
		elif reaction.startswith("Trzymaj się"):
			reactions_list.append("care")

	print_debug(reactions_list)	

	ret = {"like": 0, "love": 0, "wow": 0, "haha": 0, "sad": 0, "anger": 0, "care": 0}
    
	if len(reactions_list) == 1:
		ret[reactions_list[0]] = reactions_count 
	if len(reactions_list) == 2:
		ret[reactions_list[0]] = math.floor(reactions_count*0.75)
		ret[reactions_list[1]] = math.ceil(reactions_count*0.25)
	if len(reactions_list) == 3:
		ret[reactions_list[0]] = math.floor(reactions_count*0.65)
		ret[reactions_list[1]] = math.ceil(reactions_count*0.25)
		ret[reactions_list[2]] = math.ceil(reactions_count*0.10)
	
	while True:
		total_reactions = 0
		for k, v in ret.items():
			total_reactions += v
		if total_reactions == reactions_count:
			break
		elif total_reactions < reactions_count:
			ret[reactions_list[0]] += 1
		elif total_reactions > reactions_count:
			ret[reactions_list[0]] -= 1

	return ret

saved_posts = []

def	parse_element(element, nowtime):
	global saved_posts
	data = json.loads(html.unescape(element.split(' data-ft="')[1].split('"')[0]))
	#print(element)
	from_id = data["actrs"]
	post_id = data["top_level_post_id"]
	real_date = False
	if "page_insights" in data:	
		timestamp = data["page_insights"][GROUP_ID]["post_context"]["publish_time"]
		real_date = True
	else:
		timestamp = 0

	ts = datetime.fromtimestamp(int(timestamp))
	date_clean = ts.strftime("%Y-%m-%d")
	timestamp_clean = ts.strftime("%Y-%m-%d %H:%M:%S")

	json_path = DIRECTORY+"json/"+date_clean+"/"+post_id+".json"
	json_path_2 = DIRECTORY+"json/"+date_clean+"/"+GROUP_ID+"_"+post_id+".json"
	
	if post_id in saved_posts:
		print_debug("Post "+post_id+" was already saved.")
		return False

	if os.path.exists(json_path) or os.path.exists(json_path_2) or post_id in saved_posts:
		json_obj = {}
		if os.path.exists(json_path):
			f = open(json_path, "r")
			json_obj = json.loads(f.read())
		if os.path.exists(json_path_2):
			f = open(json_path, "r")
			json_obj = json.loads(f.read())

		if "comments_count" in json_obj:
			old_full_name = json_obj["from"]["name"]
			total = 0
			for k, v in json_obj["reactions"].items():
				total += v
			comments = json_obj["comments_count"]
			if (total == 0 and comments == 0) or len(old_full_name.strip()) == 0:
				print()
				print_warning(color("Post "+post_id+" is saved but has no reaction or user data. Resaving.", colors.YELLOW))
			else:
				saved_posts.append(post_id)
				print_info("Post "+post_id+" ("+old_full_name+") was already saved and contains all data.")
				return False

	if not real_date:
		print_error("Mo page insights in data, "+post_id)
		if not (len(sys.argv) > 4 and sys.argv[4] == "skip"):
			raise ParseException()

	full_name = element.split("<strong>")[1].split("</strong>")[0].replace("<span>", "").replace("</span>", "").replace("<wbr />", "").replace('<span class="word_break">', "")
	full_name = full_name.split(">")[1].split("<")[0]
	full_name = full_name.replace("&#039;", "'")
	if len(full_name) <= 1:
		print_debug(element)
		print_error("Empty full_name " + full_name)
		exit()
	print()
	print_info(color(full_name + " " + timestamp_clean, colors.YELLOW) + " (" + post_id + ")")

	element_noheader = element.split("</header>")[-1]
	if "<p>" in element_noheader:
		message = element_noheader.split("<p>")[1].split("</p>")[0].strip()
	elif "<span>" in element_noheader:
		message = element_noheader.split("<span>")[1].split("</span>")[0].strip()
	else:
		message = ""
	message = format_text(message)
	#print(data)

	post_type = data.get("story_attachment_style", "status")
	
	link = ""
	if "udostępnił" in element and 'href="/story.php?' in element:
		link = "https://mbasic.facebook.com/story.php?" + element.split('href="/story.php?')[1].split('">')[0]
		link = html.unescape(link)
		link = link.split("&eav=")[0]

	medias = []

	if post_type == "photo":
		result = save_photo(data["photo_id"])
		if result != None:
			medias.append(result)
	elif post_type in ["album", "new_album"]:
		arr = []
		if "photo_attachments_list" in data:
			arr = data["photo_attachments_list"]
		else:
			dirty_arr = element.split("/photo.php?fbid=")[1:]
			for dirty_photoid in dirty_arr:
				arr.append(dirty_photoid.split("&")[0])
			print_debug("Parsed photoids: "+str(arr))
		for photo in arr:
			result = save_photo(photo)
			if result != None:
				medias.append(result)
	elif post_type in [post_type == "video", "video_inline", "animated_image_video"]:
		#print(data)
		video_url = element.split('href="/video_redirect/?src=')[1].split('"')[0]
		video_url = html.unescape(video_url)
		video_url = unquote(video_url)
		result = save_video(video_url)
		if result != None:
			medias.append(result)
	elif post_type in ["looking_for_players", "commerce_product_item", "status", "fun_fact_stack", "minutiae_event", "image_share", "group_sell_product_item", "fundraiser_person_to_charity", "group_welcome_post", "meet_up_event"]:
		pass
	elif post_type in ["event", "file_upload", "pages_share", "share", "avatar", "messenger_generic_template", "music_aggregation", "map", "animated_image_share"]:
		print_info("Shared link: "+link+" ("+post_type+")")
	elif post_type == "native_templates":
		message += " <Shared deleted post.>"
	elif post_type == "ama_post":
		message += " <Hosted q&a session.>"
	elif post_type == "fb_note":
		message += " <fb_note>"
	elif post_type == "story_list":
		message += " <story_list contents not dumped>"
	else:
		print_error("UNKNOWN POST TYPE: "+post_type)
		print_error(post_id)
		exit()

	if post_type == "file_upload":
		print_warning("File upload dumping is not implemented yet.")
		with open(DIRECTORY+"not_dumped_files.txt", "a+", encoding='utf-8') as f:
			f.write(post_id+"\n") 
	
	comments_count = 0
	if ">1 komentarz" in element:
		comments_count = 1
	if ">Liczba komentarzy: " in element:
		comments_count = int(element.split(">Liczba komentarzy: ")[1].split("<")[0])

	#"2021-01-08T11:46:46+0000"
	created_time = ts.strftime("%Y-%m-%dT%H:%M:%S")+"+0100" 

	for l in message.splitlines():
		print("    "+l)
	#print(post_type)

	reactions = reconstruct_reactions(element)

	obj = {
		"timestamp": str(timestamp),
		"created_time": created_time,
		"id": post_id,
		"message": message,
		"from": {
			"name": full_name,
			"id": str(from_id)
		},
		"type": post_type,
		"link:": link,
		"medias": medias,
		"reactions": reactions,
		"comments_count": comments_count,
	}
    
	print_info(reactions)
	print_debug(json.dumps(obj))

	os.makedirs(DIRECTORY+"json/"+date_clean, exist_ok=True)
	if date_clean not in dates_list:
		dates_list.append(date_clean)
		sorted_dates = "\n".join(sorted(dates_list, reverse=True))
		with open(DIRECTORY+"json/dates.txt", "w+", encoding='utf-8') as f:
			f.write(sorted_dates)

	with open(json_path, "w+", encoding='utf-8') as f:
		f.write(json.dumps(obj))

	posts_list_path = DIRECTORY+"json/"+date_clean+"/posts.txt"
	with open(posts_list_path, "a+", encoding='utf-8') as f:
		line = post_id+","+full_name+","+created_time+"\n"
		#print(line)
		f.write(line)

	saved_posts.append(post_id)

	return obj

def parse(content, nowtime):
	arr = content.split("</article>")
	if len(arr) <= 2:
		print_error("No posts in response")
		exit()
	all_skipped = True
	for a in arr:
		if "<article " in a:
			element = a.split("<article ")[1]
			ret = parse_element(element, nowtime)
			if ret != False:
				all_skipped = False
	return all_skipped

if __name__ == "__main__":
	os.makedirs(DIRECTORY+"json", exist_ok=True)
	os.makedirs(DIRECTORY+"medias", exist_ok=True)

	if os.path.exists(DIRECTORY+"json/dates.txt"):
		with open(DIRECTORY+"json/dates.txt") as f:
			dates_list = f.read().strip().splitlines()

	nowtime = int(time.time())
	nowts_formatted = datetime.fromtimestamp(nowtime).strftime("%Y-%m-%d %H:%M:%S") 
	print_ok("Started at "+nowts_formatted)
    
	group_name = DIRECTORY
	if group_name.endswith("/"):
		group_name = group_name[:-1]
		group_name = group_name.split("/")[-1]

	set_windows_title("Dumping group " + group_name + ", account " + account_name + ", started at " + nowts_formatted)

	saved_timestamp_path = DIRECTORY+"stopped_at.txt"
	saved_group_id_path = DIRECTORY+"group_id.txt"

	with open(saved_group_id_path, "w+") as f:
		f.write(GROUP_ID)

	if os.path.exists(saved_timestamp_path):
		with open(saved_timestamp_path) as f:
			nowtime = int(f.read().strip())

	try:
		while True:
			fromts = str(nowtime)
			formatted_ts = datetime.fromtimestamp(nowtime).strftime("%Y-%m-%d %H:%M:%S") 
			#fromts = "1598950034"
			#time.sleep(0.5)
			print()
			print_info(color("Dumping posts from "+formatted_ts, colors.GREEN)+", "+fromts)
			while True:
				try:
					url = ('https://mbasic.facebook.com/groups/'+GROUP_ID+'?bacr='+str(nowtime)+'%3A951077175399046%3A951077175399046%2C0%2C3%3A7%3AQWE9PSs%3D')
#					print(url)
					response = requests.get('https://mbasic.facebook.com/groups/'+GROUP_ID+'?bacr='+str(nowtime)+'%3A951077175399046%3A951077175399046%2C0%2C3%3A7%3AQWE9PSs%3D', cookies=cookies, headers=headers)
					all_skipped = parse(response.content.decode(), nowtime)
					break
				except ParseException as e:
					nowtime += 180
					print_error("Parse exception, retry")
					time.sleep(10)
			if all_skipped:
				nowtime -= 15 * 60;
			else:
				nowtime -= 5 * 60;
			with open(saved_timestamp_path, "w+") as f:
				f.write(str(nowtime))
	except KeyboardInterrupt:
		print_info("ctrl+c pressed\n")
		exit()
