import os
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

__version__ = "0.1.0"

dirname = os.path.dirname(os.path.abspath(__file__))
template_folder = os.path.join(dirname,'templates')
static_folder = os.path.join(dirname,'static')
print('template_folder={} static_folder={}'.format(template_folder,static_folder))
app = Flask(__name__,
            template_folder=template_folder,
            static_folder=static_folder,
            static_url_path=''
            )
app.config.from_object('sorsched.config')

custom_config_env = 'SHOW_SCHEDULER_APP_CONFIG'
if custom_config_env in os.environ:
    app.config.from_envvar(custom_config_env)

Bootstrap(app)
db = SQLAlchemy(app)

from sorsched import views
