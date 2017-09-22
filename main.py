import os
from flask import Flask
from flask_apscheduler import APScheduler


class Config(object):
    JOBS = [
        {
            'id': 'generate-page',
            'func': 'func:scrap',
            'args': (1, 2),
            'trigger': 'interval',
            'minues': 15
        }
    ]

    SCHEDULER_API_ENABLED = True

app = Flask(__name__)

@app.route('/')
def main():
	return "Bot is running"

port = os.getenv('VCAP_APP_PORT', '5000')
if __name__ == "__main__":
	app.config.from_object(Config())

    scheduler = APScheduler()
    # it is also possible to enable the API directly
    # scheduler.api_enabled = True
    scheduler.init_app(app)
    scheduler.start()
    
	app.run(host='0.0.0.0', port=int(port))