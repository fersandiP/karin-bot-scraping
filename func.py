import redis

REDIS_HOST = "sl-aus-syd-1-portal.3.dblayer.com"
REDIS_PORT = 17556
REDIS_PASSWORD = "BWJPNBCYZAZCAVPD"

def login_redis():
	return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

def scrap():
	r = login_redis()

	val = r.get("test")
	if (val is None):
		r.set("test", 0)
	else:
		r.set("test", int(val)+1)

def test():
	r = login_redis()
	val = r.get("test")

	if val is None:
		val = "None"
	return str(val)
