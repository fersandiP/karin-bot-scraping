import redis
import scrapy
import json
from scrapy.crawler import CrawlerProcess


REDIS_HOST = "sl-aus-syd-1-portal.3.dblayer.com"
REDIS_PORT = 17556
REDIS_PASSWORD = "BWJPNBCYZAZCAVPD"

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
	]
	r = login_redis()

	def parse(self, response):
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
		feature = response.css(".content")
		feature = feature.css("p::text").extract_first()
		if (feature is not None):
			features += [feature]
		features += response.css(".content ul li::text").extract()

		new_features = []
		for i in range(len(features)):
			features[i] = features[i].strip()
			if features[i] != '':
				features[i] = features[i].replace("\xa0", "")
				new_features += [features[i]]
		features = new_features

		advantages = response.css(".product-list p::text").extract()
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

def _scrap():
	process = CrawlerProcess({
		'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
	})

	process.crawl(FwdSpider)
	process.start() # the script will block here until the crawling is finished