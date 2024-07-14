import requests, html, json, sys, io, time, re, math, os, traceback, base64, hashlib, atexit
from datetime import datetime
from urllib.parse import unquote
from colors import *
import print_image
#import cookies.account_xan as account2

# make frontend use unix ts and calc date with os timezone

TERM_SUPPORTS_24BIT_COLORS = True

def sha(s):
	return hashlib.sha256(s).hexdigest()

def set_windows_title(s):
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(s)
    except:
        pass
        
class ParseException(Exception):
    pass

#fuck windows
sys.stdout = io.open(sys.stdout.fileno(), 'w', encoding='utf-8')

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
	unescaped = html.unescape(remove_tags("\n".join(newtext))).strip()
	unescaped = replace_last(unescaped, "Odtwórz film", "").strip()
	unescaped = replace_last(unescaped, "Zobacz tłumaczenie", "").strip()
	return unescaped

def url_filename(url):
	url_ = url.split("?")[0] if "?" in url else url
	return url_.split("/")[-1]

def time_sleep(s):
	a = s
	delay = 0.1
	while a > 0:
		print_last("Sleeping for "+color("{:.1f}s".format(max(0, a)), colors.GRAY))
		a -= delay
		time.sleep(delay)

def save_url(url, prefix):
	filename = url_filename(url)
	path = prefix+filename
	photo = False
	if ".jpg" in filename or ".gif" in filename or ".bmp" in filename or ".png" in filename:
		photo = True
	if not os.path.exists(path):
		content = session.get(url).content
		if len(content) > 0:
			with open(path, "wb") as f:
				f.write(content)
			print_ok("Saved "+filename)
		else:
			print_warning("Photo weights 0 bytes")
			os_exit(0)
	else:
		print_info("Media already saved. "+filename)
	
	if photo and os.path.exists(path):
		with open(path, "rb") as f:
			b = f.read()
			print()
			try:
				print_image.print_bytes(b, scale=0.7, margin=7, truecolor=TERM_SUPPORTS_24BIT_COLORS)
			except KeyboardInterrupt:
				os_exit(0)
			except:
				traceback.print_exc()
				print_warning("Image corrupted")
	return filename

def save_photo(photo):
	print_debug("Saving photo "+photo)
	#time_sleep(10+random.randint(1,100)/10)
	url = "https://mbasic.facebook.com/photo/view_full_size/?fbid="+photo
	rsp = requests.get(url, cookies=cookies, headers=headers, allow_redirects=False)
	content = rsp.content.decode()
	if "Możliwość korzystania przez Ciebie z tej funkcji została tymczasowo zablokowana." in content:
		print_fatal(color("save_photo rate limit", colors.RED))
		time_sleep(600)
		os_exit(0)
	try:
		print_debug(url)
		print_debug(content)
		if "<title>Ten wątek jest pusty</title>" in content:
			print_warning("Photo deleted / you don't have access")
			return None
		photo_url = content.split('meta http-equiv="refresh" content="0;url=')[1].split('"')[0]
		photo_url = html.unescape(photo_url)
		return save_url(photo_url, DIRECTORY+"medias/")
	except KeyboardInterrupt:
		raise KeyboardInterrupt
	except:
		traceback.print_exc()
		os_exit(0)
		return None

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
		reactions_count = int(fixed.split(" reakcji, w tym")[0].split('aria-label="')[-1])
	except KeyboardInterrupt:
		os_exit(0)
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

saved_pfps = {}

def download_pfp(profile_id_int):
	profile_id = str(profile_id_int)
	if profile_id not in saved_pfps:
		content = requests.get("https://mbasic.facebook.com/profile/picture/view/?profile_id="+profile_id, cookies=cookies, headers=headers).content.decode()
		if "Możliwość korzystania przez Ciebie z tej funkcji została tymczasowo zablokowana." in content:
			print_fatal(color("download_pfp rate limit", colors.RED))
			time_sleep(600)
			os_exit(0)
		#print(content)
		src = None
		
		try:
			if 'src="https://scontent' in content:
				src = "https://scontent"+unquote(content.split('src="https://scontent')[1].split('"')[0]).replace('&amp;', "&")
		except KeyboardInterrupt:
			os_exit(0)
		except:
			print_warning("Pfp fallback!")
			try:
				if 'width="320" height="320"' in content:
					for imgs in content.split('<img'):
						if 'width="320" height="320"' in imgs:
							src = unquote(imgs.split('src="')[1].split('"')[0]).replace('&amp;', "&")
			except KeyboardInterrupt:
				os_exit(0)
			except:
				src = None
				
		if src != None:
			print_debug("Downloading pfp "+src)
			content_pfp = session.get(src, cookies=cookies, headers=headers).content
			if len(content_pfp) < 32:
				print_error("Pfp data too short!")
				with open(DIRECTORY+"no_pfp_data.txt", "a+", encoding='utf-8') as f:
					f.write(profile_id_int+"\n") 			

				with open(DIRECTORY+"avatars/default.jpg", "rb") as f:
						print()
						print_image.print_bytes(f.read(), scale=0.3, margin=17, truecolor=TERM_SUPPORTS_24BIT_COLORS)							
			else:
				pfp_sha = sha(content_pfp)
				filename_pfp = profile_id+"_"+sha(content_pfp)+".jpg"
				path = DIRECTORY+"avatars/"+filename_pfp
				saved_pfps[profile_id] = filename_pfp
				if os.path.exists(path):
					with open(path, "rb") as f:
						print()
						print_image.print_bytes(f.read(), scale=0.3, margin=17, truecolor=TERM_SUPPORTS_24BIT_COLORS)					
					print_info(color("Pfp was already downloaded. ", colors.DARK_GRAY)+color(profile_id, colors.LIGHT_GRAY))
				else:
					with open(path, "wb+") as f:
						f.write(content_pfp)
						print_ok(color("New pfp downloaded! "+profile_id, colors.GREEN))
						print()
						print_image.print_bytes(content_pfp, scale=0.3, margin=17, truecolor=TERM_SUPPORTS_24BIT_COLORS)
				return filename_pfp
		else:
			print_error("No pfp data! ‏"+color(profile_id, colors.RED))
			userids = []
			if os.path.exists(DIRECTORY+"no_pfp_data.txt"):
				with open(DIRECTORY+"no_pfp_data.txt", "r", encoding='utf-8') as f:
					userids = f.read().splitlines() 
					
			userids.append(str(profile_id_int))
			cpy = set(userids)
			userids = list(cpy)
			
			with open(DIRECTORY+"no_pfp_data.txt", "w+", encoding='utf-8') as f:
				f.write("\n".join(userids)) 
				
			with open(DIRECTORY+"avatars/default.jpg", "rb") as f:
				print()
				print_image.print_bytes(f.read(), scale=0.3, margin=17, truecolor=TERM_SUPPORTS_24BIT_COLORS)
	
			#os_exit(0)
	else:
		if ".jpg" in saved_pfps[profile_id]:
			with open(DIRECTORY+"avatars/"+saved_pfps[profile_id], "rb") as f:
				print()
				print_image.print_bytes(f.read(), scale=0.3, margin=17, truecolor=TERM_SUPPORTS_24BIT_COLORS)
		else:
			with open(DIRECTORY+"avatars/default.jpg", "rb") as f:
				print()
				print_image.print_bytes(f.read(), scale=0.3, margin=17, truecolor=TERM_SUPPORTS_24BIT_COLORS)
		print_info(color("Pfp was already downloaded. ", colors.DARK_GRAY)+color(profile_id, colors.LIGHT_GRAY))
		return saved_pfps[profile_id]
	return ""

cached_uids = {}

def parse_uid_from_profile(url):
	global cached_uids
	url_short = url.split("&")[0]
	if url_short in cached_uids:
		return cached_uids[url_short]

	if not url.startswith("https://mbasic.facebook.com/"):
		url = "https://mbasic.facebook.com" + url
	response = session.get(url, cookies=cookies, headers=headers)
	content = response.content.decode()
	uid = None
	try:
		if "/privacy/touch/block/confirm/?bid=" in content:
			uid = content.split("/privacy/touch/block/confirm/?bid=")[1].split("&")[0]
		elif "/profile/timeline/stream/" in content:
			uid_tmp = content.split("/profile/timeline/stream/")[1].split(">")[0]
			uid = uid_tmp.split("profile_id=")[1].split("&")[0]
		print_debug("Parsed userid: "+str(uid))

		cached_uids[url_short] = uid
	except KeyboardInterrupt:
		os_exit(0)
	except:
		traceback.print_exc()
		print_debug(content)
	if uid == None:
		print_error("Couldn't get uid for "+url)
		os_exit(0)
	return uid

def get_post_timestamp(session, post_id, nowtime):
	print_debug("Post timestamp fallback "+color(post_id, colors.GRAY))
	
	#url = 'https://www.facebook.com/story.php/?id='+GROUP_ID+'&story_fbid='+post_id
	url = "https://www.facebook.com/groups/"+GROUP_ID+"/posts/"+post_id+"/"
	
	print_debug(url)
	response = session.get(url, cookies=cookies, headers=headers)
	content = response.content.decode()
	if "Wygląda na to, że ta funkcja była przez " in content:
		print_fatal("get_post_timestamp rate limit")
		time_sleep(600)
		os_exit(0)
	if '"creation_time":' not in content:
		print_error("creation_time not found in response. Rate limit? "+str(post_id))
		print_debug(content)
		return 0
		os_exit(0)
	arr = content.split('"creation_time":')
	candidates = []
	for a in arr:
		timestamp_s = str(a.split(",")[0])
		try:
			timestamp_i = int(timestamp_s)
		except KeyboardInterrupt:
			os_exit(0)
		except:
			pass
		#1711808819
		if len(timestamp_s) == 10:
			candidates.append(timestamp_i)
		else:
			if not timestamp_s.startswith("<!DOCTYPE html"):
				print_warning("Bad timestamp: "+timestamp_s[:16])
	print_info("Post timestamp candidates: "+str(candidates))
	
	lowest_diff = 100000000000000
	ret = candidates[-1]
	
	for t in candidates:
		diff = abs(t-nowtime)
		if diff < lowest_diff:
			lowest_diff = diff
			ret = t
	
	print_info("Got post timestamp! "+color(ret, colors.GRAY))
	return str(ret)

saved_posts = []

def	parse_element(session, element, nowtime):
	global saved_posts
	
	data = json.loads(html.unescape(element.split(' data-ft="')[1].split('"')[0]))
	#print(element)
	from_id = None
	#profile_url = element.split('<strong><a href="')[1].split('"')[0]
	post_id = element.split("/permalink/")[-1].split("/")[0]

	if post_id in saved_posts:
		print_debug("Post "+post_id+" was already saved.")
		return False

	print()

	full_name = element.split("<strong>")[1].split("</strong>")[0].replace("<span>", "").replace("</span>", "").replace("<wbr />", "").replace('<span class="word_break">', "")
	full_name = full_name.split(">")[1].split("<")[0]
	if len(full_name) <= 1:
		print_warning("Full_name fallback. (1)")
		full_name = element.split("</a></strong>")[0].replace("<span>", "").replace("</span>", "").replace("<wbr />", "").replace('<span class="word_break">', "").split(">")[-1]
	if len(full_name) <= 1:
		print_warning("Full_name fallback. (2)")
		full_name = element.split("</a></strong>")[0].split(">")[-1].replace("<span>", "").replace("</span>", "").replace("<wbr />", "").replace('<span class="word_break">', "")
	
	full_name = full_name.replace("&#039;", "'")
	if len(full_name) <= 1 or "&" in full_name:
		print_debug(element)
		print_warning("Empty full_name " + full_name)
		os_exit(0)
 
	post_type = data.get("story_attachment_style", "status")

	#shared post
	shared_post = element.count("<article ") >= 2
	
	if shared_post:
		element_noheader = element.split("</header>")[-3]
	else:
		element_noheader = element.split("</header>")[-1]

	message = element_noheader.split("<footer")[0]
	message = format_text(message)
	
	if shared_post:
		element_noheader_shared = element.split("</header>")[-1]
	
		if "<p>" in element_noheader_shared:
			message_shared = element_noheader_shared.split("<p>")[1].split("</p>")[0].strip()
		elif "<span>" in element_noheader_shared:
			message_shared = element_noheader_shared.split("<span>")[1].split("</span>")[0].strip()
		else:
			message_shared = ""
		message += "\n_________________\nShared post: " + format_text(message_shared)

	link = ""
	if "https://lm.facebook.com/l.php?u=" in element:
		link = element.split('https://lm.facebook.com/l.php?u=')[1].split('"')[0]
		link = unquote(link)
		link = link.split("&eav=")[0].split("&fbclid=")[0].split("?fbclid=")[0]
		if len(link) > 0:
			message += "\n"+link
			
	if "udostępnił" in element and 'href="/story.php?' in element:
		link = "https://mbasic.facebook.com/story.php?" + element.split('href="/story.php?')[1].split('"')[0]
		link = unquote(link)
		link = link.split("&eav=")[0].split("&fbclid=")[0].split("?fbclid=")[0]

	if post_type == "native_templates":
		message += " <Shared deleted post.>"
	elif post_type == "ama_post":
		message += " <Hosted q&a session.>"
	elif post_type == "fb_note":
		message += " <fb_note>"
	elif post_type == "story_list":
		message += " <story_list contents not dumped>"
	
	message = message.strip()
	
	json_found = False
	json_obj = {}

	timestamp =	0
	from_id = None
	found_date = False

	if full_name == "Anonimowy członek grupy":
		from_id = "99999"
	else:
		if from_id == None:
			#from_id = parse_uid_from_profile(profile_url)
			from_id = element.split("story_id=S%3A_I")[1].split("%")[0] #better method
	
	for file, old_obj in SAVED_POSTS_OBJ.items():
		if old_obj["id"] == post_id and old_obj["from"].get("id", "99999") == from_id:
			print_info(color("Found json match! "+file, colors.GRAY))
			timestamp = old_obj["timestamp"]
			found_date = True
			break
		
	if post_id == None or len(post_id) < 4:
		print_error("Bad post_id: "+str(post_id))
		os_exit(0)
	if from_id == None or len(from_id) < 4:
		print_error("Bad from_id: "+str(from_id))
		os_exit(0)

	print_debug(from_id+", "+post_id)

	reactions = reconstruct_reactions(element)
	reactions_count = 0
	for k, v in reactions.items():
		reactions_count += v

	comments_count = 0
	if ">1 komentarz" in element:
		comments_count = 1
	if ">Liczba komentarzy: " in element:
		comments_count = int(element.split(">Liczba komentarzy: ")[1].split("<")[0])

	wrong_name = False
	old_full_name = None

	if found_date == False:
		timestamp = get_post_timestamp(session, post_id, nowtime)
		if timestamp != 0:
			found_date = True

	ts = datetime.utcfromtimestamp(int(timestamp))
	timestamp_clean = ts.strftime("%Y-%m-%d %H:%M:%S")
	date_clean = ts.strftime("%Y-%m-%d")
	set_windows_title(group_name + " / " + account_name + " / " + timestamp_clean)

	json_path = DIRECTORY+"json/"+date_clean+"/"+post_id+".json"
	json_path_2 = DIRECTORY+"json/"+date_clean+"/"+GROUP_ID+"_"+post_id+".json"

	if os.path.exists(json_path):
		f = open(json_path, "r")
		json_obj = json.loads(f.read())
		json_found = True
	elif os.path.exists(json_path_2):
		f = open(json_path_2, "r")
		json_obj = json.loads(f.read())
		json_found = True

	medias_exists_flag = False
	no_medias = False

	medias = []
	skip_post = True
	old_avatar = ""

	if json_found:
		if "comments_count" in json_obj:
			old_full_name = json_obj["from"]["name"]
			old_medias = json_obj["medias"]
			medias = old_medias
			old_timestamp = datetime.utcfromtimestamp(int(json_obj["timestamp"]))
			old_date = old_timestamp.strftime("%Y-%m-%d %H:%M:%S")
			old_reactions = json_obj["reactions"]
			old_avatar = json_obj["from"]["avatar"]
			medias_exists_flag = True
			for old_media in old_medias:
				if not os.path.exists(DIRECTORY+"medias/"+old_media):
					medias_exists_flag = False
				else:
					with open(DIRECTORY+"medias/"+old_media, "rb") as f:
						if len(f.read()) == 0:
							print_info("Photo "+old_media+" weights 0 bytes")
							medias_exists_flag = False
			if len(old_medias) == 0:
				no_medias = True
			old_total_reactions = 0
			for k, v in old_reactions.items():
				old_total_reactions += v
			old_comments_count = json_obj["comments_count"]
			if "avatar" not in json_obj["from"] or ".jpg" not in json_obj["from"]["avatar"] or not os.path.exists(DIRECTORY+"avatars/"+json_obj["from"]["avatar"]):
				saved_posts.append(post_id)
				if skip_post: print()
				skip_post = False
				print_info(color("User "+old_full_name+" has no pfp data in json.", colors.BLUE))
			if not medias_exists_flag:
				saved_posts.append(post_id)
				if skip_post: print()
				skip_post = False
				print_info(color("Post "+post_id+" ("+old_full_name+") is saved, but not all medias are saved.", colors.BLUE))
			if len(old_full_name.strip()) == 0 or "<" in old_full_name or ">" in old_full_name or "&" in old_full_name:
				saved_posts.append(post_id)
				if skip_post: print()
				skip_post = False
				wrong_name = True
				print_info(color("Post "+post_id+" ("+old_full_name+") is saved but has wrong user data. Resaving.", colors.BLUE))
			"""if total == 0 or old_comments == 0:
				saved_posts.append(post_id)
				if skip_post: print()
				skip_post = False
				print_info(color("Post "+post_id+" is saved but has no reactions ("+str(total)+") or comments ("+str(old_comments)+"). Resaving.", colors.BLUE))
			el"""
			if reactions_count > old_total_reactions:			
				saved_posts.append(post_id)
				if skip_post: print()
				skip_post = False
				print_info(color("Post "+post_id+" reactions mismatch. Reactions: "+str(reactions_count)+"/"+str(old_total_reactions)+". Resaving.", colors.BLUE))
			else:
				reactions = old_reactions
			
			if comments_count > old_comments_count:			
				saved_posts.append(post_id)
				if skip_post: print()
				skip_post = False
				print_info(color("Post "+post_id+" comments mismatch. Comments "+str(comments_count)+"/"+str(old_comments_count)+". Resaving.", colors.BLUE))
			else:
				comments_count = old_comments_count
			
			if skip_post and not no_medias:
				saved_posts.append(post_id)
				print_info(color("Post "+post_id+" (", colors.LIGHT_GRAY)+color(old_full_name+", "+old_date, colors.WHITE)+color(") was already saved and contains all data.", colors.LIGHT_GRAY))
				return False
	else:
		#print()
		print_ok(color("New post found!", colors.GREEN))

	print_info(color(full_name + " " + timestamp_clean, colors.YELLOW)+color(" (" + post_id + ") ", colors.LIGHT_GRAY)+color(post_type, colors.PURPLE))

	# dirty fix
	post_type = "unknown"
	
	#save medias
	if not medias_exists_flag or no_medias:
		print_info("Resaving medias")
		els = element.split('href="')
		
		for e in els:
			url = e.split('"')[0]
			if 'href="/photos/' in url:
				photoid = url.split('/')[4].replace("?", "").replace("&", "")
				result = save_photo(photoid)
				if result != None:
					medias.append(result)
			if '/photo.php?fbid=' in url:
				photoid = url.split('/photo.php?fbid=')[1].split("&")[0]
				result = save_photo(photoid)
				if result != None:
					medias.append(result)
			if '/video_redirect/' in url:
				video_real = unquote(url.split('/video_redirect/?src=')[1].split('"')[0])
				print_debug(video_real)
				result = save_video(video_real)
				if result != None:
					medias.append(result)
			if 'https://mbasic.facebook.com/' in url and "permalink" in url and "permalink/"+post_id not in url:
				print_debug(url)
				c = session.get(url, cookies=cookies, headers=headers).content.decode()
				if 'href="/video_redirect/' in c:
					video_real = unquote(c.split('href="/video_redirect/?src=')[1].split('"')[0])
					print_debug(video_real)
					result = save_video(video_real)
					if result != None:
						medias.append(result)
				else:
					print_error("No video url")
					#if not shared_post:
					#	os_exit(0)

	for l in message.splitlines():
		print(color("    "+l, colors.WHITE))
	#print(post_type)
    
	#print_info(reactions)
		
	if full_name == "Anonimowy członek grupy":
		pfp_name = "anon.jpg"
	else:
		if skip_post and json_found and len(old_avatar) > 0:
			pfp_name = old_avatar
		else:
			pfp_name = download_pfp(from_id)
		
	print_info(color("Comments: ", colors.LIGHT_GRAY) + color(str(comments_count), colors.GREEN)+color(", Reactions: ", colors.LIGHT_GRAY)+color(str(reactions_count), colors.GREEN))

	if not wrong_name and old_full_name != None:
		full_name = old_full_name

	dumped_at = int(time.time())

	obj = {
		"dumped_at": str(dumped_at),
		"timestamp": str(timestamp),
		"id": post_id,
		"message": message,
		"from": {
			"name": full_name,
			"id": str(from_id),
			"avatar": pfp_name
		},
		"type": post_type,
		"link": link,
		"medias": medias,
		"reactions": reactions,
		"comments_count": comments_count,
	}

	print_debug(json.dumps(obj))
	#print()

	os.makedirs(DIRECTORY+"json/"+date_clean, exist_ok=True)
	if date_clean not in dates_list:
		dates_list.append(date_clean)
		sorted_dates = "\n".join(sorted(dates_list, reverse=True))
		with open(DIRECTORY+"json/dates.txt", "w+", encoding='utf-8') as f:
			f.write(sorted_dates)

	with open(json_path, "w+", encoding='utf-8') as f:
		f.write(json.dumps(obj, indent=4))

	with open(cached_account_path, "w+", encoding="utf-8") as f:
		f.write(account_name)

	if post_id not in saved_posts:
		posts_list_path = DIRECTORY+"json/"+date_clean+"/posts.txt"
		posts_list = ""
		if os.path.exists(posts_list_path):
			with open(posts_list_path, "r", encoding='utf-8') as f:
				posts_list = f.read()
				if not posts_list.endswith("\n"):
					posts_list = posts_list + "\n"
		posts_list = posts_list + post_id + "," + full_name + "," + str(timestamp) + "\n"
		posts_list_arr = sorted(list(set(posts_list.splitlines())))
		posts_list = "\n".join(posts_list_arr)
		with open(posts_list_path, "w+", encoding='utf-8') as f:
			f.write(posts_list)

	saved_posts.append(post_id)
	return obj

def parse(session, content, nowtime):
	arr = content.split("</footer></article>")
	if "Strona nie może być wyświetlona w tej chwili. Mogą to być przejściowe problemy, uszkodzony lub wygasły odnośnik lub brak zezwolenia na dostęp." in content:
		print_fatal(color("Group is banned or you are not member of this group.", colors.RED))
		print_debug(content)
		os_exit(0)	
	if "Administratorzy tej grupy chcą zadać Ci kilka pytań, zanim zatwierdzą Twoją prośb" in content:
		print_error(color("Reply to group invite questions.", colors.RED))
		print_debug(content)
		os_exit(0)
	if "Administratorzy otrzymali Twoje odpowiedzi. Otrzymasz powiadomienie, gdy Twoja prośba o dołączenie zostanie zatwierdzona." in content:
		print_error(color("Wait to be accepted by group administrator.", colors.RED))
		print_debug(content)
		os_exit(0)	
	if "Wygląda na to, że ta funkcja była przez Ciebie wykorzystywana w zbyt szybki, niewłaściwy sposób. Możliwość korzystania z niej została w Twoim przypadku tymczasowo zablokowana." in content:
		print_fatal(color("Rate limit!", colors.RED))
		print_debug(content)
		time_sleep(300)
		os_exit(0)
	if len(arr) <= 2:
		print_error("No posts in response. End of posts?")
		print_debug(content)
		os_exit(0)
	all_skipped = True
	for a in arr:
		if "<article " in a:
			#element = a.split("<article ")[1]
			element = a
			ret = parse_element(session, element, nowtime)
			if ret != False:
				all_skipped = False
	
	bacr = None
	
	if "?bacr=" in content:
		bacr = int(content.split("?bacr=")[-1].split("%")[0])
		if bacr > nowtime:
			bacr = None
			
	print_debug("Bacr: "+str(bacr))
	
	return all_skipped, bacr

# https://stackoverflow.com/a/59082116
def replace_last(s, old, new):
    return new.join(s.rsplit(old, 1))

def write_avatar_defaults():
	anon_b64 = r"/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wgARCAC0ALQDAREAAhEBAxEB/8QAGwABAAMBAQEBAAAAAAAAAAAAAAEFBgMEAgf/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAD8YAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOZ8HcAAAAAAAAA5mVKs+TuaYtwAAAAAAADJFQAD6Nqe0AAAAAAA5GBIAAL004AAAAAAB4DFAAAszYgAAAAAAHiMQAAC1NeAAAAAAAQYM4AAGoLwAAAAAAAFOZQgA9xtD6AAAAAAAAKooTkWJozoAAAAAAAAAAAAAAAAAACmKQ8R8AAk7lmaA9IAAAAPkyJVgAAAA+zWloAAAAZgowSQAAASQfZtj1AAAHnMQQASQASQASQXJpwAACnM2AACASAADqbcAAAoyiAAAAAAANyAAAUpRkggkAgEggkEm0AAAPEZkAAAAAAHtNMAD/xAA4EAABBAEBBAcECAcAAAAAAAABAAIDEQQFBiAhcRMwMUBBUVIiM2GREBQjMkKBosFEUGBygpLh/9oACAEBAAE/AP69fNFF7yRjP7jSbmYxNDIhPJ4QIIsGx3PJnjxoHSzOpoWfrWRkuIicYYvJvaeZRJJsmz9GNlTYzrglczkeHyWkaw3LIhnpk3gfB3ctoc05OW6Jp+yiNcz4nda4tILTRHEFaRl/XMJsjvvj2X8+4ZcvQYs0voaSiSTZ3tlJayZofB7b/Mdw141pORyA/UN/Z01q0PxDh+k9w1lhk0vJaPTfy47+zTC7VGu9DSf27g9oexzXCwRRWZA7FypIXdrD8xvbLYpZBJkO7ZODeQ7jr+mnKj6aEXMwcR6hu6XgvzsgNFiMffd5BRRtijbGwU1ooDuWp6NFll0kZ6KY9p8DzU+j5sJ9yXjzZxTNOzHGhjTfm0hYWz8zzeU4Rs9I4uWNjxY0IihaGtH8mJABJNALO16GG2Yw6Z/q/CsjVs2cm5iweTPZTpHvNve53M7oJCizMiH3U8jeTlia/PGayA2VvmODlg50Gay4X2R2tPaOrlkZFG58jg1rRZJWrarJmvLGEsgHY3z59XDK+GQPicWPHYQtG1Ruazo5abOB/t8R1W0eeZpjjRn7Nh9r4n/ipUqVKlSAVKlSpUoXvhlbJGae02CtNy25mI2UcD2OHkeo1DI+q4UsviB7PPwRskkmyVSpUqVKlSpUqVKlS2ZyDFlmEn2ZRw5jqNpn1iRs9T7+SpUqVKlSpUqVKlSpUsN/RZUMnpeD1G0/8N/l+ypUqVKlSpUqVKlSpUh1G0jSWQO8ASFSpUqVKlSpUqVKlSpMYXODR2k11Grsa/AlLvw0Qq3KVfTW5SpaOxr8+MOF1Z3f/8QAFBEBAAAAAAAAAAAAAAAAAAAAkP/aAAgBAgEBPwAEf//EABQRAQAAAAAAAAAAAAAAAAAAAJD/2gAIAQMBAT8ABH//2Q=="
	default_b64 = r"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"
	if not os.path.exists(DIRECTORY+"avatars/anon.jpg"):
		with open(DIRECTORY+"avatars/anon.jpg", "wb+") as f:
			f.write(base64.b64decode(anon_b64))
	if not os.path.exists(DIRECTORY+"avatars/default.jpg"):
		with open(DIRECTORY+"avatars/default.jpg", "wb+") as f:
			f.write(base64.b64decode(default_b64))

def get_group_creation_timestamp():
	#todo
	return 0

def cleanup():
	print_ok("Bye")

def os_exit(a):
	cleanup()
	os._exit(a)

SAVED_POSTS_OBJ = {}

if __name__ == "__main__":	
	try:
		GROUP_ID = sys.argv[1]
		DIRECTORY = sys.argv[3]
		if not DIRECTORY.endswith("/"):
			DIRECTORY += "/"

		cached_account_path = DIRECTORY+"cached_account.txt"

		try:
			account_name = sys.argv[2].replace(".py", "")

			if account_name.lower() in ["unknown", "?", "guess", "idk"]:
				try:
					with open(cached_account_path) as f:
						account_name = f.read().strip()
				except KeyboardInterrupt:
					os_exit(0)
				except:
					print_error("No saved account name. Please specify in command line args.")
					os_exit(0)

			account = __import__(account_name, globals(), locals(), ['headers', 'cookies'], 0)

			headers = account.headers
			cookies = account.cookies
		except SystemExit:
			os_exit(0)
		except:
			traceback.print_exc()
			raise ValueError()
	except KeyboardInterrupt:
		os_exit(0)
	except:
		print()
		print_info("Usage: python3 "+sys.argv[0]+" <group id> <account> <save to> [reset/fast]")
		print_info("Example: python3 "+sys.argv[0]+" 6351613231561 account.py dump_fav_group")
		print_info("Optional args: reset/fast. Reset - resets dumping, fast - faster algo, but may miss posts")
		print()
		os_exit(0)

	print()

	atexit.register(cleanup)

	os.makedirs(DIRECTORY+"json", exist_ok=True)
	os.makedirs(DIRECTORY+"medias", exist_ok=True)
	os.makedirs(DIRECTORY+"avatars", exist_ok=True)
	
	write_avatar_defaults()

	if os.path.exists(DIRECTORY+"json/dates.txt"):
		with open(DIRECTORY+"json/dates.txt") as f:
			dates_list = f.read().strip().splitlines()

	nowtime = int(time.time())
	nowts_formatted = datetime.utcfromtimestamp(nowtime).strftime("%Y-%m-%d %H:%M:%S")
	print_ok("Started at "+color(nowts_formatted, colors.YELLOW))
    
	group_name = DIRECTORY
	if group_name.endswith("/"):
		group_name = group_name[:-1]
		group_name = group_name.split("/")[-1]

	set_windows_title(group_name + " / " + account_name + " / " + nowts_formatted)

	saved_timestamp_path = DIRECTORY+"stopped_at.txt"
	saved_group_id_path = DIRECTORY+"group_id.txt"

	if GROUP_ID.lower() in ["unknown", "?", "guess", "idk"]:
		try:
			with open(saved_group_id_path) as f:
				GROUP_ID = f.read().strip()
		except KeyboardInterrupt:
			os_exit(0)
		except:
			print_error("No saved group id. Please specify in command line args.")
			os_exit(0)
	
	if os.path.exists(saved_group_id_path):
		with open(saved_group_id_path) as f:
			saved_group_id = f.read().strip()
			if saved_group_id != GROUP_ID.strip():
				print_error("Group id mismatch! "+color(GROUP_ID + " =/= " + saved_group_id, colors.RED))
				os_exit(0)

	with open(saved_group_id_path, "w+") as f:
		f.write(GROUP_ID)

	fast_mode = False

	if len(sys.argv) > 4 and "fast" in sys.argv[4]:
		fast_mode = True
	
	if not (len(sys.argv) > 4 and "reset" in sys.argv[4]):
		if os.path.exists(saved_timestamp_path):
			with open(saved_timestamp_path) as f:
				nowtime = int(f.read().strip())

	print_ok("Dumping group "+color(GROUP_ID, colors.YELLOW)+" using "+color(account_name, colors.YELLOW))
	print()

	group_creation_timestamp = get_group_creation_timestamp()

	for dir in os.listdir(DIRECTORY+"json"):
		if not os.path.isdir(DIRECTORY+"json/"+dir): continue
		print_last("Caching "+color(dir, colors.GRAY))
		for json_filename in os.listdir(DIRECTORY+"json/"+dir):
			json_path = DIRECTORY+"json/"+dir+"/"+json_filename
			if not json_path.endswith(".json"): continue
			if json_path.endswith("_comments.json"): continue
			
			json_obj = {}
			with open(json_path, "r", encoding="utf-8") as f:
				json_obj = json.loads(f.read())			
				SAVED_POSTS_OBJ[json_path] = json_obj

	print_info(str(len(SAVED_POSTS_OBJ))+" posts already dumped.")

	session = requests.Session()

	try:
		while True:
			fromts = str(nowtime)
			formatted_ts = datetime.utcfromtimestamp(nowtime).strftime("%Y-%m-%d %H:%M:%S") 
			#fromts = "1598950034"
			#time.sleep(0.5)
			#print()
			print_info(color("Dumping posts from ", colors.GREEN)+color(formatted_ts, colors.YELLOW)+color(", "+fromts, colors.DARK_GRAY))
			set_windows_title(group_name + " / " + account_name + " / " + formatted_ts)
			while True:
				try:
					url = ('https://mbasic.facebook.com/groups/'+GROUP_ID+'?bacr='+str(nowtime)+'%3A951077175399046%3A951077175399046%2C0%2C3%3A7%3AQWE9PSs%3D')
					print_debug(url)
					response = session.get('https://mbasic.facebook.com/groups/'+GROUP_ID+'?bacr='+str(nowtime)+'%3A951077175399046%3A951077175399046%2C0%2C3%3A7%3AQWE9PSs%3D', cookies=cookies, headers=headers)
					all_skipped, bacr = parse(session, response.content.decode(), nowtime)
					break
				except KeyboardInterrupt:
					print_info("ctrl+c pressed\n")
					os_exit(0)
				except ParseException as e:
					nowtime += 180
					print_error("Parse exception, retry. Sleeping for 10 secs.")
					time.sleep(10)
			if bacr and fast_mode:
				nowtime = bacr
			else:
				if all_skipped:
					nowtime -= 15 * 60;
				else:
					nowtime -= 5 * 60;
			with open(saved_timestamp_path, "w+", encoding="utf-8") as f:
				f.write(str(nowtime))
	except KeyboardInterrupt:
		print_info("ctrl+c pressed\n")
		os_exit(0)
