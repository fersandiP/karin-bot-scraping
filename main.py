import os
import func
from flask import Flask
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = Flask(__name__)

@app.route('/')
def main():
	return "Bot is running"

def test_job():
	app.logger.debug('test')

scheduler = BackgroundScheduler()
scheduler.add_job(
	func=test_job,
	trigger=IntervalTrigger(seconds=5),
	id='printing_job',
	name='Print date and time every five seconds',
	replace_existing=True)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

port = os.getenv('VCAP_APP_PORT', '5000')
if __name__ == "__main__":
	# app.config.from_object(Config())
	app.run(host='0.0.0.0', port=int(port))