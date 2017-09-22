import os
import func
from flask import Flask
from flask_apscheduler import APScheduler

app = Flask(__name__)

class Config(object):
	JOBS = [
		{
			'id': 'generate-page',
			'func': 'test_job',
			'trigger': 'interval',
			'minutes': 1
		}
	]

	SCHEDULER_API_ENABLED = True


@app.route('/')
def main():
	return "Bot is running"

@app.route('/test')
def test():
	return func.test()

def test_job():
	func.scrap()

port = os.getenv('VCAP_APP_PORT', '5000')
if __name__ == "__main__":
	app.config.from_object(Config())

	scheduler = APScheduler()
	# it is also possible to enable the API directly
	scheduler.api_enabled = True
	# scheduler.init_app(app)
	scheduler.add_job(test_job, 'interval', minutes=1)
	scheduler.start()
	
	app.run(host='0.0.0.0', port=int(port))