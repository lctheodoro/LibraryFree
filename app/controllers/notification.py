from app import app, mail
from flask_mail import Message
from flask import current_app,render_template
from app.models.tables import Book_loan
from time import sleep
from datetime import timedelta,date


def Send(users,message,assunto,book=None,loan_date=None):
	for i in users:
			msg = Message(assunto, sender=app.config['MAIL_USERNAME'], recipients=[i.email])
			with app.app_context():
				msg.html = render_template(message,user=i,book=book,loan_date=loan_date)
				mail.send(msg)

def threeDays():
	users = []
	day = date.today()+timedelta(days=3)
	books = Book_loan.query.filter_by(return_date=day).all()
	for i in books:
		users += [books.user]
	return users,books,day

def tomorrow():
	users = []
	day = date.today()+timedelta(days=1)
	books = Book_loan.query.filter_by(return_date=day).all()
	for i in books:
		users += [books.user]
	return users,books,day

# Daily Verification
def email():
	countdown = 86400
	while(True):
		u,b,d = tomorrow()
		Send(b,"email.html","1 Day:",b,d)
		u,b,d = threeDays()
		Send(b,"email.html","3 Days:",b,d)
		sleep(countdown)
