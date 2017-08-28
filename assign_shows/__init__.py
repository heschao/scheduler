import os
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

__version__ = "0.1.0"

app = Flask(__name__)
app.config.from_object('assign_shows.config')

custom_config_env = 'SHOW_SCHEDULER_APP_CONFIG'
if custom_config_env in os.environ:
    app.config.from_envvar(custom_config_env)

Bootstrap(app)
db = SQLAlchemy(app)

from assign_shows import views
