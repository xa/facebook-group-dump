# facebook-group-dump

Tool for dumping posts from Facebook groups

Requires Python 3.8+ with requests installed

**Usage:**

Login into mbasic.facebook.com

Change Facebook language to Polish. (required, POLSKA GUROM)

Put cookies and headers from browser into account.py (copy curl from dev tools and convert into python with curlconverter.com)

Run python3 dump.py <group id> <saved path>

** WARNING! Contains extremly scuffed code, because Facebook closed all json apis **