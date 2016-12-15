<<<<<<< HEAD
from flask import jsonify
from flask_mail import Message
from flask_restful import Resource, reqparse
from app import app, db, auth, mail
from app.models.tables import Book_loan, Book_return
from flask import current_app,render_template
from datetime import timedelta,date




    class ReturnApi(Resource):
        def __init__(self):

            self.reqparse = reqparse.RequestParser()
            self.reqparse.add_argument("book_id", type=int, required=True,
                                       location='json')
            self.reqparse.add_argument("user_id", type=int, required=True,
                                       location='json')
            self.reqparse.add_argument("owner_id", type=int, required=True,
                                       location='json')
            self.reqparse.add_argument("confirmed_by", type=str,
                                       location='json')
            super(ReturnApi, self).__init__()


        def post(self):
            args = self.reqparse.parse_args()
            loan_record = Book_loan.query.filter_by(book_id=args['book_id'],
                                                      owner_id=args['owner_id'],
                                                      user_id= args['user_id']).
                                                      first()
            return_record = Book_return.query.filter_by(book_loan_id =
                                                        loan_record.id).first()
            if not (return_record):
                return_record = Book_return(book_loan_id = loan_record.id,
                                            returned_date = datetime.now())
                db.session.add(Book_return)

            if(args['confirmed_by']=='owner'):
                return_record.owner_confirmation=True
            else if(args['confirmed_by']=='user'):
                return_record.user_confirmation=True
            else:
                abort(400)
            db.session.commit()
=======
from flask import g, jsonify, json
from flask_restful import Resource, reqparse
from app import app, db, auth, api
from app.models.tables import Book, Book_loan, Book_return, owned_books,User
from app.models.decorators import is_user, is_manager
from sqlalchemy.sql import and_, or_
from isbnlib import *
from isbnlib.registry import bibformatters
from datetime import date, timedelta
from app.controllers import notification

class BooksApi(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("title", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("isbn", type=str, location = 'json')
        self.reqparse.add_argument("synopsis", type=str, location='json')
        self.reqparse.add_argument("author", type=str, location='json')
        self.reqparse.add_argument("author2", type=str, location='json')
        self.reqparse.add_argument("author3", type=str, location='json')
        self.reqparse.add_argument("publisher", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("edition", type=int, location='json')
        self.reqparse.add_argument("year", type=int)
        self.reqparse.add_argument("language", type=str, location='json')
        self.reqparse.add_argument("genre", type=str, location='json')
        super(BooksApi, self).__init__()

    def get(self):
        # This parameters are specific to the GET method
        # because they are not mandatory
        search_reqparse = reqparse.RequestParser()
        search_reqparse.add_argument("title", type=str, location='json')
        search_reqparse.add_argument("isbn", type=str, location='json')
        search_reqparse.add_argument("author", type=str, location='json')
        search_reqparse.add_argument("author2", type=str, location='json')
        search_reqparse.add_argument("author3", type=str, location='json')
        search_reqparse.add_argument("publisher", type=str, location='json')
        search_reqparse.add_argument("genre", type=str, location='json')

        # retrieving the values
        args = search_reqparse.parse_args()

        filters_list = []

        if args['title']:
            filters_list.append(
                Book.title.ilike("%{0}%".format(args['title']))
            )

        if args['isbn'] :
            print(args['isbn'])
            filters_list.append(
                Book.isbn.ilike("%{0}%".format(args['isbn']))
            )

        if args['author']:
            filters_list.append(
                Book.author.ilike("%{0}%".format(args['author']))
            )

        if args['author2']:
            filters_list.append(
                Book.author2.ilike("%{0}%".format(args['author2']))
            )

        if args['author3']:
            filters_list.append(
                Book.author3.ilike("%{0}%".format(args['author3']))
            )

        if args['publisher']:
            filters_list.append(
                Book.publisher.ilike("%{0}%".format(args['publisher']))
            )

        if args['genre']:
            filters_list.append(
                Book.genre == args['genre']
            )

        filtering = and_(*filters_list)

        books = Book.query.filter(filtering).all()

        return {'data': [book.serialize for book in books]}, 200

    def post(self):
        args = self.reqparse.parse_args()
        book = Book(**args)

        #Generate the isbn code with title like a parameter
        code_isbn = isbn_from_words(book.title)
        book.isbn = code_isbn

        #set the format to json
        bibtex = bibformatters['json']
        consult = meta(code_isbn)

        if not consult:
            return 300

        consult = bibtex(consult)
        aux = json.loads(consult)

        book.author = aux['author'][0]['name']

        tam = 0
        for i in aux['author']:
            tam += 1

        if tam >= 3:
            book.author2 = aux['author'][1]['name']
            book.author3 = aux['author'][2]['name']
        elif tam == 2:
            book.author2 = aux['author'][1]['name']

        if aux['year']:
            book.year = aux['year']
        else:
            book.year = 0

        db.session.add(book)
        db.session.commit()
        return {'data': book.serialize}, 200


class ModifyBooksApi(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("title", type=str, location='json')
        self.reqparse.add_argument("synopsis", type=str, location='json')
        self.reqparse.add_argument("publisher", type=str, location='json')
        self.reqparse.add_argument("edition", type=int, location='json')
        self.reqparse.add_argument("language", type=str, location='json')
        self.reqparse.add_argument("genre", type=str, location='json')
        super(ModifyBooksApi, self).__init__()
>>>>>>> 3679bb818f3d15eac947a1b37a7c79182c02b90f

    def get(self, id):
        book = Book.query.get_or_404(id)
        return {'data': book.serialize}, 200

    def put(self, id):
        book = Book.query.get_or_404(id)
        args = self.reqparse.parse_args()

        for key, value in args.items():
            if value is not None:
                setattr(book, key, value)

        code_isbn = isbn_from_words(book.title)
        book.isbn = code_isbn

        bibtex = bibformatters['json']
        consult = meta(code_isbn)

        if not consult:
            return 300

        consult = bibtex(consult)
        aux = json.loads(consult)

        book.author = aux['author'][0]['name']

        tam = 0
        for i in aux['author']:
            tam += 1

        if tam >= 3:
            book.author2 = aux['author'][1]['name']
            book.author3 = aux['author'][2]['name']
        elif tam == 2:
            book.author2 = aux['author'][1]['name']

        if aux['year']:
            book.year = aux['year']
        else:
            book.year = 0

        db.session.commit()
        return {'data': book.serialize}, 200

    def delete(self, id):
        book = Book.query.get_or_404(id)
        db.session.delete(book)
        db.session.commit()
        return 204

class BooksAvailabilityApi(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("book_id", type=int, required=True,
                                   location='json')
        self.reqparse.add_argument("user_id", type=int, required=True,
                                   location='json')
        super(BooksAvailabilityApi, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        book = owned_books.query.filter_by(book_id=args['book_id'],
                                            owner_id=args['user_id']).first()

        if(book): # Book found
            book_loans = Book_loan.query.filter_by(book_id=book.book_id).all()
            if(book_loans): # If any book loan
                for loan in book_loans: # Search for all loans
                    book_return = Book_return.query.filter_by(book_loan_id=loan.id).first()
                    if(book_return):
                        if(not book_return.user_confirmation or not book_return.owner_confirmation):
                            return {'data': {'status': 'unavaiable'}}, 200
                    else: # Book not returned yet
                        return {'data': {'status': 'unavaiable'}}, 200
                return {'data': {'status': 'available'}}, 200 # All loans returned and confirmed
            else: # Book not loaned yet
                return {'data': {'status': 'available'}}, 200
        else: # Book not found
            return 500

class LoanRequestApi(Resource):
    decorators = [auth.login_required]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("book_id", type=int, required=True,
                                    location='json')
        self.reqparse.add_argument("user_id", type=int, required=True,
                                    location='json')
        self.reqparse.add_argument("owner_id", type=int, required=True,
                                    location='json')
        self.reqparse.add_argument("loan_status", type=str, default='requested',location='json')
        super(LoanRequestApi,self).__init__()

    @is_user
    def post(self):
        args = self.reqparse.parse_args()
        if args['loan_status'] == 'requested':
            try:
                loan = Book_loan(**args)
                owner = User.query.get_or_404(loan.owner_id)
                book = Book.query.get_or_404(loan.book_id)
                notification.Send([owner],"loanrequest.html","Loan Request",book)

                db.session.add(loan)
                db.session.commit()

                return 204
            except Exception as error:
                print(error)
                return { 'data': { 'message': 'Unexpected Error' } }, 500
        return 500

class LoanReplyApi(Resource):
    decorators = [auth.login_required]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("loan_status", type=str, required=True,
                                    location='json')
        super(LoanReplyApi,self).__init__()

    @is_user
    def get(self,id):
        try:
            loan = Book_loan.get_or_404(id)
            return { 'data': loan.serialize }, 200
        except Exception as error:
            print(error)
            return { 'data': {'mesage': 'Unexpected Error'} }, 500

    @is_user
    def post(self,id):
        args = self.reqparse.parse_args()
        loan =  Book_loan.query.get_or_404(id)
        if args['loan_status'] == None:
            return { 'data ' : {'mesage': 'Empty Status'}}, 500
        if loan.loan_status != args['loan_status']:
            user = User.query.get_or_404(loan.user_id)
            book = Book.query.get_or_404(loan.book_id)
            loan.loan_status = args['loan_status']

            if loan.loan_status == 'accepted':
                loan.loan_date = date.today()
                return_day = date.today() + timedelta(days=10)

                if return_day.strftime('%A') == 'Sunday':
                    return_day += timedelta(days=1)
                elif return_day.strftime('%A') == 'Saturday':
                    return_day += timedelta(days=2)
                loan.return_date = return_day

                user.points_update(5)

                notification.Send([user],"accepted.html","Loan Reply",book,loan.return_date)
            elif loan.loan_status == 'refused':
                notification.Send([user],"refused.html","Loan Reply",book,loan.return_date)
            elif loan.loan_status == 'queue':
                notification.Send([user],"queue.html","Loan Reply",book,loan.return_date)

            db.session.commit()
            return 204
        return { 'data ' : {'mesage': 'Request already answered'}}, 409

class ReturnApi(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("book_id", type=int, required=True,
                                   location='json')
        self.reqparse.add_argument("user_id", type=int, required=True,
                                   location='json')
        self.reqparse.add_argument("owner_id", type=int, required=True,
                                   location='json')
        self.reqparse.add_argument("confirmed_by", type=str,
                                   location='json')
        super(ReturnApi, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        loan_record = Book_loan.query.filter_by(book_id=args['book_id'],
                                                  owner_id=args['owner_id'],
                                                  user_id= args['user_id']).first()
        return_record = Book_return.query.filter_by(book_loan_id =
                                                    loan_record.id).first()
        if not (return_record):
            return_record = Book_return(book_loan_id = loan_record.id,
                                        returned_date = datetime.now())
            db.session.add(book_return)

        if(args['confirmed_by']=='owner'):
            return_record.owner_confirmation=True
        elif(args['confirmed_by']=='user'):
            return_record.user_confirmation=True
        else:
            abort(400)
        db.session.commit()

        return 204

    def get(self):
        args = self.reqparse.parse_args()
        loan_record_search = Book_loan.query.filter_by(book_id=args['book_id'],
                                                  owner_id=args['owner_id'],
                                                  user_id= args['user_id']).first()
        return_record_search = Book_return.query.filter_by(book_loan_id =
                                                    loan_record.id).first()

        return {'data': [return_record_search.serialize]}, 200

<<<<<<< HEAD
    api.add_resource(ReturnApi, '/api/v1/books/return', endpoint='return')


        class DelayApi(Resorce):
            def __init__(self):

                self.reqparse = reqparse.RequestParser()
                self.reqparse.add_argument("book_id", type=int, required=True,
                                           location='json')
                self.reqparse.add_argument("user_id", type=int, required=True,
                                           location='json')
                self.reqparse.add_argument("owner_id", type=int, required=True,
                                           location='json')
                self.reqparse.add_argument("status", type=Enum("waiting",
                                            "accepted", "refused",
                                           name="delayed_return_status"),
                                            required=True,location='json') )

                super(DelayApi, self).__init__()


            def post(self):
                args = self.reqparse.parse_args()
                loan_delay = Book_loan.query.filter_by(book_id=args['book_id'],
                                                          owner_id=args['owner_id'],
                                                          user_id= args['user_id']).
                                                          first()
                delay_record= Delayed_return.query.filter_by(book_loan_id =
                                                            loan_delay.id).first()

                if not (delay_record):
                    delay_record = Delayed_return(book_loan_id = loan_delay.id,
                                                    requested_date = loan_delay.returned_date()+timedelta(days=7))
                    db.session.add(Delayed_return)

                if(args['status']=='waiting'):
                    delay_record.status='waiting'
                else if(args['status']=='accepted'):
                    delay_record.status='accepted'
                else if(args['status']=='refused'):
                    delay_record.status='refused'
                else:
                    abort(400)
                db.session.commit()

                users_mail = User.query.filter_by(user_id=args['user_id']).first()
                book_mail = Book.query.filter_by(book_id=args['book_id']).first()

                users_email = []
                users_email += [users_mail.email]


                Send(users_email, "email.html",delay_record.status,
                     book_mail.title,delay_record.requested_date)

                return 204


                def get(self):
                    args = self.reqparse.parse_args()
                    loan_delay_search = Book_loan.query.filter_by(book_id=args['book_id'],
                                                              owner_id=args['owner_id'],
                                                              user_id= args['user_id']).
                                                              first()
                    delay_record_search= Delayed_return.query.filter_by(book_loan_id =
                                                                loan_delay.id).first()

                    return {'data': [delay_record_search.serialize]}, 200

api.add_resource(DelayApi, '/api/v1/books/delay', endpoint='delay')
api.add_resource(BooksApi, '/api/v1/books', endpoint='books')
api.add_resource(ModifyBooksApi, '/api/v1/books/<int:id>', endpoint='modify_books')
api.add_resource(LoanRequestApi, '/api/v1/books/borrow', endpoint='loan_request')
api.add_resource(LoanReplyApi, '/api/v1/books/borrow/<int:id>', endpoint='loan_reply')
api.add_resource(BooksAvailabilityApi, '/api/v1/books/availability', endpoint='books_availability')
api.add_resource(ReturnApi, '/api/v1/books/return', endpoint='return')
