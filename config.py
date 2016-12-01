import os.path
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = os.environ['LIBRARYFREE_DB_URI']
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    BUNDLE_ERRORS = True  # related to Flask-RESTful errors, see docs
    ERROR_404_HELP = False

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
