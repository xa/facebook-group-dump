#stolen from https://github.com/xHak9x/fbi/blob/master/fbi.py

import json, sys, hashlib, os, time, requests

def get(data):
	print('[*] Generate access token ')

	try:
		os.mkdir('cookie')
	except OSError:
		pass

	b = open('cookie/token.log', 'w+')
	
	try:
		r = requests.get('https://api.facebook.com/restserver.php',params=data)
		print(r.content.decode())
		a = json.loads(r.text)

		b.write(a['access_token'])
		b.close()
		print('[*] successfully generate access token')
		exit()
	except KeyError:
		print('[!] Failed to generate access token')
		os.remove('cookie/token.log')
	except requests.exceptions.ConnectionError:
		print('[!] Failed to generate access token / conn')
		os.remove('cookie/token.log')
		
def id():
	print('[*] login to your facebook account         ');
	id = input('[?] Username : ');
	pwd = input('[?] Password : ');
	API_SECRET = '62f8ce9f74b12f84c123cc23437a4a32';
	api_key = "882a8490361da98702bf97a021ddc14d"
	app_id = "748992795651511"
	
	data = {"api_key":api_key,"credentials_type":"password","email":id,"format":"JSON", "generate_machine_id":"1","generate_session_cookies":"1","locale":"en_US","method":"auth.login","password":pwd,"return_ssl_resources":"0","v":"1.0"};
	sig = 'api_key='+api_key+'credentials_type=passwordemail='+id+'format=JSONgenerate_machine_id=1generate_session_cookies=1locale=en_USmethod=auth.loginpassword='+pwd+'return_ssl_resources=0v=1.0'+API_SECRET
	sig = sig.encode('utf-8')
	x = hashlib.new('md5')
	x.update(sig)

	data.update({'sig':x.hexdigest()})
	get(data)
    
id()