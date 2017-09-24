import redis
import scrapy
import json
import base64
from scrapy.crawler import CrawlerProcess

REDIS_HOST = "sl-aus-syd-1-portal.3.dblayer.com"
REDIS_PORT = 17556
REDIS_PASSWORD = "BWJPNBCYZAZCAVPD"

category_list = ['invest', 'accident-disability', 'critical-illness',
 'hospitalisation', 'life', 'waiver-of-premium', 'package']

def login_redis():
	return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

r = login_redis()

class PaketSpider(scrapy.Spider):
		# Your spider definition
	name = "fwd"
	start_urls=[
		"https://www.fwd.co.id/id/invest/",
		"https://www.fwd.co.id/id/protect/accident-disability/",
		"https://www.fwd.co.id/id/protect/critical-illness/",
		"https://www.fwd.co.id/id/protect/hospitalisation/",
		"https://www.fwd.co.id/id/protect/life/",
		"https://www.fwd.co.id/id/protect/waiver-of-premium/",
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

		image = response.css("div.img-bg::attr(style)").extract_first()
		start = image.find("(")
		end = image.find(")")
		image = links + image[start+2:end-1]

		link = response.url
		name = link.split("/")[-2]
		description = response.css(".table-cell > p::text").extract_first().replace("\xa0", "").replace("\\u00a0", "")

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
				features[i] = features[i].replace("\xa0", "").replace("\\u00a0", "")
				new_features += [features[i]]
		features = new_features

		advantages = response.css(".product-feature p::text").extract()
		advantages += response.css(".product-feature li::text").extract()
		new_advantages = []
		for i in range(len(advantages)):
			advantages[i] = advantages[i].strip()
			if advantages[i] != '':
				new_advantages += [advantages[i].replace("\xa0", "").replace("\\u00a0", "")]
		advantages = new_advantages

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
					"brosur_link" : brosur_link,
					"image" : image
				}}
		self._save_packet(name, data)

	def _save_list(self, jenis, name):
		global r
		r.rpush(jenis, name)

	def _save_packet(self, name, data):
		global r
		r.set(name, json.dumps(data))

class PromoSpider(scrapy.Spider):
		# Your spider definition
	name = "promo-fwd"
	start_urls=[

	]

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
	data = request.form
	user_id = r.get(data["id"])
	if (user_id is not None):
		return "User has been registered"

	info = {}

	for key in data:
		if (key == "id"):
			continue
		info[key] = data[key]

	for key in request.files:
		info[key] = str(base64.b64encode(request.files[key].read()))

	info = json.dumps(info)

	r.set(str(data["id"]), info)

    return "success"

def get_user(user_id):

	data = r.get(user_id)
	if (data is None):
		return "User not found"

	return data.decode("utf-8")

def update_user(request):
	data_request = request.form
	data = r.get(data_request['id'])
	if (data is None):
		return "User not found"
	data = json.loads(data.decode('utf-8'))

	for key in data_request:
		if (key == "id"):
			continue
		data[key] = data_request[key]

	for key in request.files:
		data[key] = str(base64.b64encode(request.files[key].read()))

	data = json.dumps(data)
	r.set(str(data_request["id"]), data)

	return "success"

def suggest_package(user_id):
	user = r.get(user_id)
	if user is None:
		return "User not found"
	user = user.decode('utf-8')
	user = json.loads(user)

	suggestion = {}
    protect_package = api('family-term')['data']
    invest_package = api('sprint-link-plus')['data']
    promo_package = api('bebas-aksi')['data']
	suggestion = {
		'protect' : protect_package,
		'invest' : invest_package,
		'promo' : promo_package
		}
    if user['jobClass'] == 'pelajar' and user['<7JT']:
        suggestion['education'] = api('sprint-education')['data']
	return json.dumps(suggestion)

def _scrap():
	process = CrawlerProcess({
		'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
	})

	process.crawl(PaketSpider)
	process.start() # the script will block here until the crawling is finished
	# process.join()
	process.stop()

def import_data(json_file):
	global r
	data = json.loads(json_file)

	insurance = data['root']

	name = insurance['name']
	tagline = insurance['tagline']
	description = insurance['description']
	billing = insurance['billing']
	packages = insurance['packages']

	_billing_key = name+'__billing'
	_tagline_key = name+'__tagline'
	_description_key = name+'__description'
	_packages_key = name+'__packages'

	r.set(name, name)
	r.set(_billing_key, billing)
	r.set(_tagline_key, tagline)
	r.set(_description_key, description)
	r.set(_packages_key, packages)

	for package in packages:
		name = package['name']
		features = package['features']
		coverage = package['coverage']
		riskclass = package['risk-class']
		payment = package['payment-options']
		fees = package['fees']

		_package_name_key = _packages_key+'__'+name
		_package_features_key = _package_name_key+'__features'
		_package_coverage_key = _package_name_key+'__coverage'
		_package_riskclass_key = _package_name_key+'__risk-class'
		_package_payment_key = _package_name_key+'__payment-options'
		_package_fees_key = _package_name_key+'__fees'

		r.set(_package_features_key, features)
		r.set(_package_coverage_key, coverage)
		r.set(_package_riskclass_key, riskclass)
		r.set(_package_payment_key, payment)
		r.set(_package_fees_key, fees)

	return json.dumps(data)

def import_json(json_data):
	data = None
	try:
		data = json.loads(json_data)
	except:
		return 'data must be raw json file'

	try:
		root = data['root']

		name = root['name']
		tagline = root['tagline']
		description = root['description']
		billing = root['billing']
		packages = root['packages']

		assert type(name) == str
		assert type(tagline) == str
		assert type(description) == str
		assert type(billing) == str
		assert type(packages) == dict

		for package_key in packages:
			package = packages[package_key]

			name = package['name']
			features = package['features']
			coverage = package['coverage']
			riskclass = package['risk-class']
			payment = package['payment-options']
			fees = package['fees']

			assert type(name) == str
			assert type(features) == list
			assert type(coverage) == list
			assert type(riskclass) == list
			assert type(payment) == list
			assert type(name) == str
	except:
		return 'data structure incorrect'

	insurance = data['root']['name'].replace(' ','_')

	r.set(insurance, json.dumps(data));

	return insurance+'\n' + str(r.get(insurance))

# def get_insurance_data(insurance):
# 	_tagline_key = insurance+'__tagline'
# 	_description_key = insurance+'__description'

# 	return {
# 		'name' : insurance,
# 		'tagline' : r.get(_tagline_key),
# 		'description' : r.get(_description_key)
# 	}

def export_insurance_data(insurance):
	data = None
	try:
		data = json.loads(r.get(insurance).decode("utf-8"))
		data = data['root']
	except:
		return 'insurance has no valid data stored'

	return json.dumps({
		'name' : data['name'],
		'tagline' : data['tagline'],
		'description' : data['description'],
		'billing' : data['billing']
	})

# def get_packages_list(insurance):
# 	_packages_key = insurance+'__packages'

# 	return r.get(_packages_key)

def export_packages_list(insurance):
	data = None
	try:
		data = json.loads(r.get(insurance).decode("utf-8"))
		data = data['root']
	except:
		return 'insurance has no valid data stored'

	return json.dumps({'packages' : data['packages']})


# def get_package_data(insurance,package):
# 	_packages_key = insurance+'__packages'

# 	_package_name_key = _package_key+'__'+package
# 	_package_features_key = _package_name_key+'__features'
# 	_package_coverage_key = _package_name_key+'__coverage'
# 	_package_riskclass_key = _package_name_key+'__risk-class'
# 	_package_payment_key = _package_name_key+'__payment-options'
# 	_package_fees_key = _package_name_key+'__fees'

# 	return {
# 		'name' : package,
# 		'features' : r.get(_package_features_key),
# 		'coverage' : r.get(_package_coverage_key),
# 		'risk-class' : r.get(_package_riskclass_key),
# 		'payment-options' : r.get(_package_payment_key),
# 		'fees' : r.get(_package_fees_key)
# 	}

def export_package_data(insurance, package):
	data = None
	try:
		data = json.loads(r.get(insurance).decode("utf-8"))
		data = data['root']
	except:
		return 'insurance has no valid data stored'

	package_data = None
	try:
		package_data = data['packages'][package]
	except:
		return 'insurance has no such package'

	return json.dumps({package : package_data})
