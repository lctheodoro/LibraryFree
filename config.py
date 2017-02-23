import os.path
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = "postgres:///libraryfree"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    BUNDLE_ERRORS = True  # related to Flask-RESTful errors, see docs
    ERROR_404_HELP = False
    MAIL_SERVER = 'smtps.bol.com.br'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TSL = False
    MAIL_USERNAME = 'libraryfree@bol.com.br'
    MAIL_PASSWORD = 'Senhadolibrary'
    JSON_AS_ASCII = False

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
