from app import app, mail
from flask_mail import Message
from flask import current_app, render_template
from app.models.tables import Book_loan, User
from time import sleep
from datetime import timedelta, date

# Takes a list of users, the name of the html of the message, a subject
# and if necessary is taken a book and a date, passing all these variables
# to the email, that is, you can create variables within the email
def send(loans, message, assunto, book=None, loan_date=None):
	for u in loans:
		msg = Message(assunto, sender=app.config['MAIL_USERNAME'], recipients=[u.email])
		with app.app_context():
			msg.html = render_template(message, user=u, book=book, loan_date=loan_date)
			mail.send(msg)

# Picks users who have books with a return period of three days
def threeDays():
	users = []
	day = date.today() + timedelta(days=3)
	books = Book_loan.query.filter_by(return_date=day).all()
	for book in books:
		users += [book.user]
	return users, books, day

# Picks up users who have books with a one-day return period
def tomorrow():
	users = []
	day = date.today() + timedelta(days=1)
	books = Book_loan.query.filter_by(return_date=day).all()
	for book in books:
		users += [book.user]
	return users, books, day

# Daily Verification
def email():
	countdown = 86400
	while(True):
		u, b, d = tomorrow()
		send(b, "email.html", "1 Day:", b, d)
		u, b, d = threeDays()
		send(b, "email.html", "3 Days:", b, d)
		sleep(countdown)
