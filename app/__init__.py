import os

from flask import Flask, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command("db", MigrateCommand)

auth = HTTPBasicAuth()

app_errors = {
    'NotFound': {
        'message': 'The object you are looking for was not found.',
        'status': 404,
    },
    'UnexpectedError': {
        'message': 'Something unexpected happened.',
        'status': 500,
    }
}

api = Api(app, errors=app_errors)

from app.models import tables
from app.controllers import users
