import redis
import scrapy
import json
import base64
from scrapy.crawler import CrawlerProcess


REDIS_HOST = "sl-aus-syd-1-portal.3.dblayer.com"
REDIS_PORT = 17556
REDIS_PASSWORD = "BWJPNBCYZAZCAVPD"

category_list = ['invest', 'accident-disability', 'critical-illness',
 'hospitalisation', 'life', 'waiver-of-premium']

def login_redis():
	return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

r = login_redis()

class FwdSpider(scrapy.Spider):
		# Your spider definition
	name = "fwd"
	start_urls=[
		"https://www.fwd.co.id/id/invest/",
		"https://www.fwd.co.id/id/protect/accident-disability/",
		"https://www.fwd.co.id/id/protect/critical-illness/",
		"https://www.fwd.co.id/id/protect/hospitalisation/",
		"https://www.fwd.co.id/id/protect/life/",
		"https://www.fwd.co.id/id/protect/waiver-of-premium/"
		"https://www.fwd.co.id/id/protect/package/"
	]

	def parse(self, response):
		if response.url == "https://www.fwd.co.id/id/protect/package/":
			links = response.css(".invest-reason a.btn")
		else:
			links = response.css(".product-filter-pane .click-here a.btn")
			
		jenis = response.url.split('/')[-2]
		for a in links.css("a::attr(href)"):
			self._save_list(jenis, a.get().split('/')[-1])
			yield response.follow(a, callback=self.parse_page)

	def parse_page(self, response):
		links = "https://www.fwd.co.id"
		title = response.css(".bread li.active::text").extract_first()

		link = response.url
		name = link.split("/")[-2]
		description = response.css(".table-cell > p::text").extract_first()

		features = []
		feature = response.css(".tell-me-more .content")
		feature = feature.css("p::text").extract_first()
		if (feature is not None):
			features += [feature]
		features += response.css(".tell-me-more .content ul li::text").extract()

		new_features = []
		for i in range(len(features)):
			features[i] = features[i].strip()
			if features[i] != '':
				features[i] = features[i].replace("\xa0", "")
				new_features += [features[i]]
		features = new_features

		advantages = response.css(".product-feature p::text").extract()
		advantages += response.css(".product-feature li::text").extract()
		for i in range(len(advantages)):
			advantages[i] = advantages[i].strip()

		brosur = response.css(".panel-download option::attr(value)").extract()
		brosur_link = None
		if len(brosur) != 0:
			brosur_link = links + brosur[-1]

		data = {"name" : name,
				"data": {
					"title" : title,
					"link" : link,
					"description" : description,
					"features" : features,
					"advantages" : advantages,
					"brosur_link" : brosur_link
				}}
		self._save_packet(name, data)

	def _save_list(self, jenis, name):
		global r
		r.rpush(jenis, name)

	def _save_packet(self, name, data):
		global r
		r.set(name, json.dumps(data))

def api(name):
	global r
	if name is None or name == '' or name == 'all':
		return json.dumps(category_list)

	if name in category_list:
		lst = r.lrange(name, 0, -1)
		for i in range(len(lst)):
			lst[i] = lst[i].decode('utf-8')
		return json.dumps(lst)

	if r.get(name) is None:
		return "API Invalid"
	else :
		return r.get(name).decode("utf-8")

def add_user(request):
	user_id = r.get(request.data["id"]) 
	if (user_id is not None):
		return "User has been registered"

	info = {}

	for key,value in request.data:
		if (key == "id"):
			continue
		info[key] = value

	for key,value in request.files:
		info[key] = base64.b64encode(value.read())

	info = json.dumps(info)

	r.set(user_id, info)

	return "success"

def get_user(user_id):
	data = r.get(user_id)
	if (data is None):
		return "User not found"

	return data.decode("utf-8")

def update_user(request):
	data = r.get(request.data['id'])
	if (data is None):
		return "User not found"
	data = json.loads(data)

	for key,value in request.data:
		if (key == "id"):
			continue
		data[key] = value

	for key,value in request.files:
		data[key] = base64.b64encode(value.read())

	return "success"

def _scrap():
	r.flushall()
	process = CrawlerProcess({
		'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
	})	

	process.crawl(FwdSpider)
	process.start() # the script will block here until the crawling is finished
	# process.join()
	process.stop()