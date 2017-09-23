import os
import func
from flask import Flask, request
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = Flask(__name__)

@app.route('/')
def main():
	return "Bot is running"

@app.route('/api/')
def api_default():
	return func.api("all")

@app.route('/api/<paket>')
def api(paket):
	return func.api(paket)

@app.route('/add/user', methods=['POST'])
def insert_user():
	return func.add_user(request)

@app.route('/user/<user_id>')
def get_user(user_id):
	return func.get_user(user_id)

@app.route('/user/update')
def update_user():
	return func.update_user(request)

@app.route('/json-data', methods=['POST'])
def json_data():
	# return func.import_data(request.data)
	return func.import_json(request.data)

@app.route('/data/<insurance>')
def json_insurance_data(insurance):
	app.logger.debug('insurance '+insurance)
	return func.export_insurance_data(insurance)

@app.route('/data/<insurance>/packages')
def json_insurance_packages(insurance):
	app.logger.debug('packages '+insurance)
	return func.export_packages_list(insurance)

@app.route('/data/<insurance>/<package>')
def json_insurance_package_data(insurance,package):
	return func.export_package_data(insurance,package)

def test_job():
	func._scrap()

# scheduler = BackgroundScheduler()
# scheduler.add_job(
# 	func=test_job,
# 	trigger=IntervalTrigger(minutes=15),
# 	id='printing_job',
# 	name='Print date and time every five seconds',
# 	replace_existing=True)
# scheduler.start()

# Shut down the scheduler when exiting the app
# atexit.register(lambda: scheduler.shutdown())

port = os.getenv('VCAP_APP_PORT', '5000')
if __name__ == "__main__":
	# app.config.from_object(Config())
	app.run(host='0.0.0.0', port=int(port))