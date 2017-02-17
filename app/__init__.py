import os

from flask import Flask, make_response, jsonify, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, prompt_pass, prompt, prompt_bool
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, output_json
from flask_mail import Mail
from threading import Thread
import logging

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)

mail = Mail(app)

manager = Manager(app)
manager.add_command("db", MigrateCommand)

auth = HTTPBasicAuth()

app_errors = {
    'NotFound': {
        'message': 'The object you are looking for was not found.',
    },
    'UnexpectedError': {
        'message': 'Something unexpected happened.',
    },
    'Unauthorized': {
        'message': 'You are not authorized to access this area.',
    }
}

def log__(http_code,user=None):
    try:
        if user is None:
            app.logger.info(request.environ.get("REMOTE_ADDR") + "\t| " + "Guest" + "\t| "+
                            str(request.path) + " - " + str(request.method) + " - " + str(http_code))
        else:
            app.logger.info(request.environ.get("REMOTE_ADDR") + "\t| " + str(user.id) + " - " + user.name + "\t| "+
                            str(request.path) + " - " + str(request.method) + " - " + str(http_code))
        return http_code
    except Exception as error:
        print(error)
        return http_code

class UnicodeApi(Api):
    def __init__(self, *args, **kwargs):
        super(UnicodeApi, self).__init__(*args, **kwargs)
        self.app.config['RESTFUL_JSON'] = {
        'ensure_ascii': False
        }
        self.representations = {
        'application/json; charset=utf-8': output_json,
        }
app.config['JSON_AS_ASCII'] = False
api = UnicodeApi(app, errors=app_errors)

from app.models import tables
from app.controllers import users, books, notification


@manager.command
def admin():
    adm = tables.User.query.filter_by(admin=2).first()
    if adm is None:
        while(True):
            name = prompt("Please enter the administrator's name")
            if name == None:
                print("You must enter a name!!!")
            else:
                if prompt_bool("Correct name?",default=True):
                    break
        while(True):
            email = prompt("Enter admin email")
            if email == None:
                print("You must enter an email!!!")
            else:
                if prompt_bool("Email Correct?",default=True):
                    break
        while(True):
            password = prompt_pass("Enter the administrator password")
            password_v = prompt_pass("Re-enter password")
            if password == None or password_v==None or password != password_v:
                print("You must enter a valid password!!!")
            else:
                if prompt_bool("Password correct?",default=True):
                    break
        adm = tables.User(name=name,password=password,email=email,admin=2)
        adm.hash_password(password)
        db.session.add(adm)
        db.session.commit()
        print("Admin created!")
    else:
        print("Admin already exists!")

@manager.command
def notify():
    # Starts a thread for daily notification about one-day
    # deadlines and three days for returning books
    notification_ = Thread(target=notification.email)

    # When it is necessary to make a migrate or an upgrade comment this line
    notification_.start()
