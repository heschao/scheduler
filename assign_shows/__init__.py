from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config.from_object('assign_shows.config')
app.config.from_envvar('SHOW_SCHEDULER_APP_CONFIG')
Bootstrap(app)
db = SQLAlchemy(app)

from assign_shows import views
