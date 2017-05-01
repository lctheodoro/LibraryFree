from app import app, mail
from flask_mail import Message
from flask import current_app, render_template
from app.models.tables import Book_loan, User
from time import sleep
from datetime import timedelta, date
from sqlalchemy.sql import and_
import requests
import json


def push_notification(email,book,msg):

	header = {"Content-Type": "application/json; charset=utf-8",
          		"Authorization": "Basic ZWU2Yjk3MDEtMDRkMi00ODE1LTgxMzMtNGYwYjA4YjI2YjJj"}
	payload = {"app_id": "e7c650f3-617b-493d-8c75-796cc21243ea",
           	"filters": [
			  		{"field": "email", "value": email}
				],
				"contents": {"en": msg}}

	req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))

	print(req.status_code, req.reason)


# Takes a list of users, the name of the html of the message, a subject
# and if necessary is taken a book and a date, passing all these variables
# to the email, that is, you can create variables within the email
def send_notify(loans, message):
	day = date.today()
	for u in loans:
		if u.return_date > day:
			msg = "O empréstimo do livro do livro "+ u.book.title +" acaba no dia " + u.return_date.strftime('%d/%m')
		else:
			msg = "O empréstimo do livro "+ u.book.title +" acabou!"
		push_notification(u.user.email,u.book.title,msg)
		msg = Message("Empréstimo Biblioteca dos Talentos", sender=app.config['MAIL_USERNAME'], recipients=[u.user.email])
		with app.app_context():
			msg.html = render_template(message, user=u.user, book=u.book, loan_date=u.return_date)
			#mail.send(msg)

def expired():
	users = []
	day = date.today() + timedelta(days=3)
	filtering = [Book_loan.return_date <= day,Book_loan.loan_status!='done']
	books = Book_loan.query.filter(and_(*filtering)).all()
	for book in books:
		users += [book.user]
	return users,books

# Daily Verification
def email():
	countdown = 86400
	while(True):
		u,b = expired()
		send_notify(b, "email.html")
		sleep(countdown)
