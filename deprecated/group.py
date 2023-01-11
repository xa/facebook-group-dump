import requests, json, os, traceback, time, datetime, sys, random

SUFFIX = "fury_dump"; groupid = "463331507506951"

TOKENS = []

TOKENS.append(open("cookie/token.log").read().strip())
#TOKENS.append(open("cookie/token_2.log").read().strip())
#TOKENS.append(open("cookie/token_3.log").read().strip())

def hms(sc):
	seconds = int(sc)
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)

	return "{h:02d}:{m:02d}:{s:02d}".format(h=hours, m=minutes, s=seconds)

def get_token():
	return random.choice(TOKENS)

REACTIONS = "reactions.type(LIKE).limit(0).summary(total_count).as(reactions_like),reactions.type(LOVE).limit(0).summary(total_count).as(reactions_love),reactions.type(WOW).limit(0).summary(total_count).as(reactions_wow),reactions.type(HAHA).limit(0).summary(total_count).as(reactions_haha),reactions.type(SAD).limit(0).summary(total_count).as(reactions_sad),reactions.type(ANGRY).limit(0).summary(total_count).as(reactions_anger),reactions.type(CARE).limit(0).summary(total_count).as(reactions_care)"

def tojson(rsp):
	return json.loads(rsp.content.decode())

def without_keys(d, keys):
	return {x: d[x] for x in d if x not in keys}

def url_filename(url):
	url_ = url.split("?")[0] if "?" in url else url
	return url_.split("/")[-1]

def save_urls(urls, prefix):
	if type(urls) == str:
		save_urls([urls], prefix)
		return
	for url in urls:
		path = prefix+url_filename(url)
		if not os.path.exists(path):
			open(path, "wb").write(requests.get(url).content)

def uniq_urls(urls):
	dupe = []
	ret = []
	for i in urls:
		if i == None or i == "": continue
		if "." in i:
			if i not in dupe:
				dupe.append(i)
				ret.append(i)
	return ret

def find_url_media(mediaobj):
	url = ""
	if "source" in mediaobj:
		return mediaobj["source"]
	else:
		for i in mediaobj:
			obj = mediaobj[i]
			if "src" in obj:
				url = obj["src"]
	return url

def parse_medias(obj):
	data = obj["data"]
	urls = []
	for i in data:
		if "media" in i:			
			urls.append(find_url_media(i["media"]))
		if "subattachments" in i:
			for j in i["subattachments"]["data"]:
				if "media" in j:			
					urls.append(find_url_media(j["media"]))
	return urls

def get_medias(postid):
	obj = tojson(requests.get("https://graph.facebook.com/v8.0/"+postid+"/attachments?fields=&access_token="+get_token()))
	print("    "+str(obj))
	if "The action attempted has been deemed abusive or is otherwise disallowed" in str(obj):
		print("    get_medias() rate limit")
		os._exit(0)
	return uniq_urls(parse_medias(obj))

def clean_reactions(obj):
	reactions = {}
	
	for i in obj:
		if i.startswith("reactions_"):
			reactions[i.split("_")[1]] = obj[i]["summary"]["total_count"]
			
	for i in reactions:
		del obj["reactions_"+i]
		
	return reactions

def clean_medias(obj):
	clean = []
	for url in obj["medias"]: clean.append(url_filename(url))
	return clean
	
def clean_comments(obj):
	clean = []
	count = 0
	if "comments" in obj:
		if "count" in obj["comments"]:
			count = obj["comments"]["count"]
		if "data" in obj["comments"]:
			for c in obj["comments"]["data"]:
				clean.append({
					"message": c["message"],
					"from": c["from"]
				})
	return clean[:3], count
	
def get_comments(url, comments):
	obj = tojson(requests.get(url))
	
	if not "data" in obj:
		print("    Comment rate limit")
		0/0
		return comments
		
#	print(obj)
	for com in obj["data"]:
		com["reactions"] = clean_reactions(com)
		if "attachment" in com and "media" in com["attachment"]:
			com["attachment"] = find_url_media(com["attachment"]["media"])
			if "." in com["attachment"]:
				save_urls(com["attachment"], "dump"+SUFFIX+"/medias/")
			else:
				com["attachment"] = ""
		comments.append(com)
	
	print("    Got comments! "+str(len(comments)))	
	
	if "paging" in obj and "next" in obj["paging"]:
		url = obj["paging"]["next"]
		time.sleep(3)
		get_comments(url, comments)
		
	return comments

def scrape_post(postid, only_comments):
	fields = "created_time,id,message,story,attachments,from,type,link,"+REACTIONS+",comments.limit(0).summary(total_count).as(comments)"
	shret = False
	should_get_comments = True
	
	if not only_comments:
		print("    Getting post info... ")
		obj = tojson(requests.get("https://graph.facebook.com/v8.0/"+postid+"?fields="+fields+"&access_token="+get_token()))
		
		if not "created_time" in obj:
			print(obj)
			print("Rate limit (?)")
			#os._exit(0)
			return
		
		#print(obj)
		#obj["medias"] = get_medias(postid)
		if "attachments" in obj:
			obj["medias"] = uniq_urls(parse_medias(obj["attachments"]))
			save_urls(obj["medias"], "dump"+SUFFIX+"/medias/")
			obj["medias"] = clean_medias(obj)
			print("    "+str(obj["medias"]))
			del obj["attachments"]
			if len(obj["medias"]) == 0: del obj["medias"]
		obj["reactions"] = clean_reactions(obj)
		comments, count = clean_comments(obj)
		obj["comments"] = comments
		obj["comments_count"] = count
		if len(obj["comments"]) == 0: del obj["comments"]
		
		if obj["comments_count"] == 0:
			should_get_comments = False
		name = "Unknown"
		if "from" in obj:
			name = obj["from"]["name"]
		else:
			obj["from"] = {"name": name}
			
		date = obj["created_time"].split("T")[0]

		if "message" in obj:
			print("    "+name+": "+obj["message"]) 			
		print("    "+date)		
		#print(obj)
		#os._exit(0)
				
		try:
			os.makedirs("dump"+SUFFIX+"/json/"+date)
			open("dump"+SUFFIX+"/json/dates.txt", "a+").write(date+"\n")
		except:
			pass

		open("dump"+SUFFIX+"/json/"+date+"/"+postid+".json", "w+").write(json.dumps(obj))
		open("dump"+SUFFIX+"/json/"+date+"/posts.txt", "a+").write(postid+","+name+","+obj["created_time"]+"\n")
		shret = True	
	else:
		date = duplicate_posts[postid]

	if should_get_comments:
		try:
			comments = []
			get_comments("https://graph.facebook.com/v8.0/"+postid+"/comments?fields=created_time,from,message,attachment,media,id,"+REACTIONS+",parent{id}&limit=2000&access_token="+get_token(), comments)
			comments_final = []

			for com in comments:
				if not "parent" in com:
					comments_final.append(com)

			for com in comments:
				if "parent" in com:
					for parent in comments_final:
						if parent["id"] == com["parent"]["id"]:
							if not "children" in parent:
								parent["children"] = []
							parent["children"].append(without_keys(com, {"parent"}))
			open("dump"+SUFFIX+"/json/"+date+"/"+postid+"_comments.json", "w+").write(json.dumps(comments_final))
		except KeyboardInterrupt:
			os._exit(0)
		except:
			#print(traceback.format_exc())		
			print("    Error while getting comments!")
			return shret
	else:
		open("dump"+SUFFIX+"/json/"+date+"/"+postid+"_comments.json", "w+").write("")
		
	return True
				
#	print(obj)
#	print(comments_final)	

def get_post_ids(url, done):
	oldkey = url.split("access_token=")[1].split("&")[0]
	url = url.replace(oldkey, get_token())
	try:
		print(url)
		obj = tojson(requests.get(url))
		obj_ = obj
		postids = []

		if "feed" in obj:
			obj_ = obj["feed"]
	
		for i in obj_["data"]:
			postids.append(i["id"])
		
		if len(obj_["data"]) > 0:
			print("Getting posts ("+str(done)+")... "+obj_["data"][-1]["updated_time"].split("T")[0])
	
		open("dump"+SUFFIX+"/post_ids.txt", "a+").write("\n".join(postids)+"\n")

		if "paging" in obj_ and "next" in obj_["paging"]:
			url = obj_["paging"]["next"]
			#print(obj_["paging"])
			open("dump"+SUFFIX+"/stopped_at.txt", "w+").write(url)
			return url, len(postids)
		else:
			print(obj)
			if os.path.exists("dump"+SUFFIX+"/stopped_at.txt"):
				os.remove("dump"+SUFFIX+"/stopped_at.txt")
			return None, None
	except KeyboardInterrupt:
		os._exit(0)
	except:
		open("dump"+SUFFIX+"/stopped_at.txt", "w+").write(url)
		print(traceback.format_exc())
		try:
			print(obj)		
		except:
			print(traceback.format_exc())		
		os._exit(0)




# -- main --




os.makedirs("dump"+SUFFIX+"/json", exist_ok=True)
os.makedirs("dump"+SUFFIX+"/medias", exist_ok=True)

duplicate_posts = {}

if os.path.exists("dump"+SUFFIX+"/json/dates.txt"):
	for date in open("dump"+SUFFIX+"/json/dates.txt").read().splitlines():
		for post in open("dump"+SUFFIX+"/json/"+date+"/posts.txt").read().splitlines():
			duplicate_posts[post.split(",")[0]]	= date

reload_posts = False
if len(sys.argv) == 2:
	if sys.argv[1].lower() == "true":
		reload_posts = True

if reload_posts:
	url = "https://graph.facebook.com/v8.0/"+groupid+"?fields=feed.order(chronological)&limit=200&access_token="+get_token()
	if os.path.exists("dump"+SUFFIX+"/stopped_at.txt"):
		url = open("dump"+SUFFIX+"/stopped_at.txt").read().strip()
		print("Continuing...")
	else:
		if os.path.exists("dump"+SUFFIX+"/post_ids.txt"):
			print("\nThis will REMOVE all post ids\n  type 'yes' to continue\n")
			choice = input()
			if choice.lower() == "yes":
				os.remove("dump"+SUFFIX+"/post_ids.txt")
			else:
				print("Exit")
				os._exit(0)

	done = 0

	while True:
		url, ln = get_post_ids(url, done)
		time.sleep(2)
		if url == None:
			break
		else:
			done += ln

if os.path.exists("dump"+SUFFIX+"/post_ids.txt"):
	postids = open("dump"+SUFFIX+"/post_ids.txt").read().splitlines()
else:
	print("\nPost list doesn't exist.")
	print("  use python3 "+sys.argv[0]+" true\n")
	os._exit(0)

don = 0
donpr = 0
starttime = datetime.datetime.now()
postidslen = len(postids)

dont_check_comment_dupe = False
dont_check_comment_dupe = False

for postid in postids:
	donpr += 1
	try:		
		if "_" not in postid: continue
		if postid in duplicate_posts:
			comments_exists = os.path.exists("dump"+SUFFIX+"/json/"+duplicate_posts[postid]+"/"+postid+"_comments.json")		
			if comments_exists or dont_check_comment_dupe:
				print("["+str(donpr)+"/"+str(len(postids))+"] duplicate "+postid)		
				postidslen -= 1
				continue

		don += 1
			
		if postid in duplicate_posts:
			print("\n["+str(donpr)+"/"+str(len(postids))+"] comments "+postid)
		else:
			print("\n["+str(donpr)+"/"+str(len(postids))+"] scraping "+postid)
		
		slp = scrape_post(postid, postid in duplicate_posts)
		if slp: time.sleep(2)
		dur = datetime.datetime.now()-starttime
		eta = int((dur.seconds / float(don)) * float(postidslen - don))   
		print("  duration: "+hms(dur.seconds))
		print("  eta: " + hms(eta))		
	except SystemExit:
		os._exit(0)
	except KeyboardInterrupt:
		os._exit(0)
	except:
		open("dump"+SUFFIX+"/couldnt_scrape.txt", "a+").write(postid+"\n")
		print(traceback.format_exc())

print("\nDone!\n")
