import os

SQLALCHEMY_DATABASE_URI = os.environ['SCHEDULER_DB_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False
WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'


