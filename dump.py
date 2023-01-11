

import requests, html, json, sys, io, time, re, math, os, traceback
from datetime import datetime
from urllib.parse import unquote
from colors import *
from account import *
import print_image

try:
	GROUP_ID = sys.argv[1]
	DIRECTORY = sys.argv[2]+"/"
except:
	print()
	print_info("Usage: python3 "+sys.argv[0]+" <group id> <save to>")
	print_info("Example: python3 "+sys.argv[0]+" 4633413245961 dump_fav_group")	
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

def	parse_element(element):
	data = json.loads(html.unescape(element.split(' data-ft="')[1].split('"')[0]))
	from_id = data["actrs"]
	post_id = data["top_level_post_id"]
	if "page_insights" not in data:
		return
	timestamp = data["page_insights"][GROUP_ID]["post_context"]["publish_time"]
	ts = datetime.fromtimestamp(int(timestamp))
	date_clean = ts.strftime("%Y-%m-%d")
	timestamp_clean = ts.strftime("%Y-%m-%d %H:%M:%S")

	json_path = DIRECTORY+"json/"+date_clean+"/"+post_id+".json"
	if os.path.exists(json_path):
		print_info("Post "+post_id+" was already saved.")
		return False

	full_name = element.split("<strong>")[1].split("</strong>")[0]
	full_name = full_name.split(">")[1].split("<")[0]
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
	elif post_type == "album" or post_type == "new_album" or post_type == "commerce_product_item":
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
	elif post_type == "video_inline" or post_type == "animated_image_video":
		#print(data)
		video_url = element.split('href="/video_redirect/?src=')[1].split('"')[0]
		video_url = html.unescape(video_url)
		video_url = unquote(video_url)
		result = save_video(video_url)
		if result != None:
			medias.append(result)
	elif post_type == "status" or post_type == "fundraiser_for_story" or post_type == "fun_fact_stack" or post_type == "og_composer_simple" or post_type == "minutiae_event" or post_type == "image_share" or post_type == "group_sell_product_item" or post_type == "fundraiser_person_to_charity" or post_type == "group_welcome_post" or post_type == "meet_up_event":
		pass
	elif post_type == "file_upload":
		print_warning("file_upload dumping is not implemented yet")
		with open(DIRECTORY+"not_dumped_files.txt", "a+", encoding='utf-8') as f:
			f.write(post_id+"\n") 
	elif post_type == "event" or post_type == "photo_link_share" or post_type == "file_upload" or post_type == "pages_share" or post_type == "share" or post_type == "avatar" or post_type == "messenger_generic_template" or post_type == "music_aggregation" or post_type == "map" or post_type == "animated_image_share":
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

	obj = {
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
		"reactions": reconstruct_reactions(element),
		"comments_count": comments_count,
	}
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

	return obj

def parse(content):
	arr = content.split("</article>")
	if len(arr) <= 2:
		print_error("No posts in response")
		exit()
	all_skipped = True
	for a in arr:
		if "<article " in a:
			element = a.split("<article ")[1]
			ret = parse_element(element)
			if ret != False:
				all_skipped = False
	return all_skipped

if __name__ == "__main__":
	try:
		print_image.print_url("https://i.imgur.com/z9tYGsn.png", scale=2.5)
	except: pass

	os.makedirs(DIRECTORY+"json", exist_ok=True)
	os.makedirs(DIRECTORY+"medias", exist_ok=True)

	if os.path.exists(DIRECTORY+"json/dates.txt"):
		with open(DIRECTORY+"json/dates.txt") as f:
			dates_list = f.read().strip().splitlines()

	nowtime = int(time.time())
	nowts_formatted = datetime.fromtimestamp(nowtime).strftime("%Y-%m-%d %H:%M:%S") 
	print_ok("Started at "+nowts_formatted)

	saved_timestamp_path = DIRECTORY+"stopped_at.txt"

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
			response = requests.get('https://mbasic.facebook.com/groups/'+GROUP_ID+'?bacr='+fromts+'%3A951077175399046%3A951077175399046%2C0%2C3%3A7%3AQWE9PSs%3D', cookies=cookies, headers=headers)
			all_skipped = parse(response.content.decode())
			if all_skipped:
				nowtime -= 15 * 60;
			else:
				nowtime -= 5 * 60;
			with open(saved_timestamp_path, "w+") as f:
				f.write(str(nowtime))
	except KeyboardInterrupt:
		print_info("ctrl+c pressed\n")
		exit()
