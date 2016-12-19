from flask import json, g
from flask_restful import Resource, reqparse
from app import db, auth, api
from app.models.tables import Book, Book_loan, Book_return, User, Wishlist, Delayed_return, Organization
from datetime import timedelta, date
from sqlalchemy.sql import and_
from isbnlib import isbn_from_words,meta
from isbnlib.registry import bibformatters
from app.controllers import notification
from threading import Thread


class BooksApi(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("title", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("isbn", type=str, location = 'json')
        self.reqparse.add_argument("synopsis", type=str, location='json')
        self.reqparse.add_argument("author", type=str, location='json', required=True)
        self.reqparse.add_argument("author2", type=str, location='json')
        self.reqparse.add_argument("author3", type=str, location='json')
        self.reqparse.add_argument("publisher", type=str, location='json')
        self.reqparse.add_argument("edition", type=int, location='json')
        self.reqparse.add_argument("year", type=int)
        self.reqparse.add_argument("language", type=str, location='json')
        self.reqparse.add_argument("genre", type=str, location='json')
        self.reqparse.add_argument("user_id", type=int, location='json')
        self.reqparse.add_argument("organization_id", type=int, location='json')
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
        # Also get books owned by a user or organization
        search_reqparse.add_argument("user_id", type=int, location='json')
        search_reqparse.add_argument("organization_id", type=int, location='json')

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

        if args['user_id']:
            filters_list.append(
                Book.user_id == args['user_id']
            )

        if args['organization_id']:
            filters_list.append(
                Book.organization_id == args['organization_id']
            )

        filtering = and_(*filters_list)
        books = Book.query.filter(filtering).all()
        return {'data': [book.serialize for book in books]}, 200

    def post(self):
        try:
            args = self.reqparse.parse_args()
            book = Book(**args)

            if (args['user_id'] and args['organization_id']) or ((not args['user_id'] and not args['organization_id'])):
                return { 'data': { 'message': 'Bad Request1' } }, 400
            if args['user_id'] and (not User.query.get(args['user_id'])):
                return { 'data': { 'message': 'User not found' } }, 404
            if args['organization_id'] and (not Organization.query.get(args['organization_id'])):
                return { 'data': { 'message': 'Organization not found' } }, 404
            elif args['user_id']:
                book.is_organization = False
                user = User.query.get_or_404(args['user_id'])
                user.points_update(10)
            else:
                book.is_organization = True

            #Generate the isbn code with title like a parameter
            code_isbn = isbn_from_words(book.title)
            book.isbn = code_isbn

            #set the format to json
            bibtex = bibformatters['json']
            consult = meta(code_isbn)

            if consult:
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

                if aux['publisher']:
                    book.publisher = aux['publisher']

            db.session.add(book)
            db.session.commit()
            return { 'data': book.serialize }, 201
        except Exception as error:
            print(error)
            return { 'data': { 'message': 'Bad Request' } }, 400


class ModifyBooksApi(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("synopsis", type=str, location='json')
        self.reqparse.add_argument("publisher", type=str, location='json')
        self.reqparse.add_argument("edition", type=int, location='json')
        self.reqparse.add_argument("language", type=str, location='json')
        self.reqparse.add_argument("genre", type=str, location='json')
        super(ModifyBooksApi, self).__init__()

    def get(self, id):
        book = Book.query.get_or_404(id)
        return {'data': book.serialize}, 200

    def put(self, id):
        try:
            book = Book.query.get_or_404(id)
            args = self.reqparse.parse_args()

            for key, value in args.items():
                if value is not None:
                    setattr(book, key, value)

            db.session.commit()
            return {'data': book.serialize}, 200
        except Exception as error:
            print(error)
            return { 'data': { 'message': 'Unexpected Error' } }, 500

    def delete(self, id):
        book = Book.query.get_or_404(id)
        if book.is_organization:
            user = User.query.get_or_404(book.organization_id)
        else:
            user = User.query.get_or_404(book.user_id)
        user.points_update(-10)
        db.session.delete(book)
        db.session.commit()
        return 204


class BooksAvailabilityApi(Resource):

    def __init__(self):
        #self.reqparse = reqparse.RequestParser()
        #self.reqparse.add_argument("book_id", type=int, required=True,
        #                           location='json')
        super(BooksAvailabilityApi, self).__init__()

    def get(self, id):
        #args = self.reqparse.parse_args()
        book = Book.query.filter_by(id=id).first()

        if(book): # Book found
            book_loans = Book_loan.query.filter_by(book_id=book.id).all()
            if(book_loans): # If any book loan
                for loan in book_loans: # Search for all loans
                    book_return = Book_return.query.filter_by(book_loan_id=loan.id).first()
                    if(book_return):
                        if(not book_return.user_confirmation or not book_return.owner_confirmation):
                            return {'data': {'status': 'unavailable'}}, 200
                    else: # Book not returned yet
                        return {'data': {'status': 'unavailable'}}, 200
                return {'data': {'status': 'available'}}, 200 # All loans returned
            else: # Book not loaned yet
                return {'data': {'status': 'available'}}, 200
        else: # Book not found
            return {'data': 'Book not found'}, 404


class LoanRequestApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("book_id", type=int, required=True,
                                    location='json')
        self.reqparse.add_argument("user_id", type=int, required=True,
                                    location='json')
        self.reqparse.add_argument("loan_status", type=str, default='requested',location='json')
        super(LoanRequestApi,self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        l = Book_loan.query.filter_by(book_id=args['book_id'],
                                      user_id=args['user_id'],
                                      loan_status=args['loan_status']).first()
        if args['loan_status'] == 'requested' and l==None:
            try:
                loan = Book_loan(**args)
                loan.scored = False
                book = Book.query.get_or_404(loan.book_id)
                if book.is_organization:
                    owner = Organization.query.get_or_404(book.organization_id)
                else:
                    owner = User.query.get_or_404(book.user_id)

                Thread(target=notification.send([owner],"loanrequest.html","Loan Request",book)).start()

                db.session.add(loan)
                db.session.commit()

                return { 'data': loan.serialize }, 201
            except Exception as error:
                print(error)
                return { 'data': { 'message': 'Unexpected Error' } }, 500
        return { 'data': { 'message': 'Request already made' } }, 500


class LoanReplyApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("loan_status", type=str, required=True,
                                    location='json')
        super(LoanReplyApi,self).__init__()

    def get(self,id):
        try:
            loan =  Book_loan.query.get_or_404(id)
            book = Book.query.get_or_404(loan.book_id)
            if g.user.id != book.user_id and g.user.id!=loan.user_id:
                return { 'data' :{'message': 'You are not authorized to access this area.'}},401
            loan = Book_loan.query.get_or_404(id)
            return { 'data': loan.serialize }, 200
        except Exception as error:
            print(error)
            return { 'data': {'message': 'Unexpected Error'} }, 500

    def put(self,id):
        loan =  Book_loan.query.get_or_404(id)
        book = Book.query.get_or_404(loan.book_id)

        if g.user.id != book.user_id:
            return { 'data' :{'message': 'You are not authorized to access this area.'}},401
        args = self.reqparse.parse_args()
        if args['loan_status'] == None:
            return { 'data ' : {'message': 'Empty Status'}}, 500
        if loan.loan_status != args['loan_status']:
            try:
                user = User.query.get_or_404(loan.user_id)

                loan.loan_status = args['loan_status']

                if loan.loan_status == 'accepted':
                    loan.loan_date = date.today()
                    return_day = date.today() + timedelta(days=10)

                    if return_day.strftime('%A') == 'Sunday':
                        return_day += timedelta(days=1)
                    elif return_day.strftime('%A') == 'Saturday':
                        return_day += timedelta(days=2)
                    loan.return_date = return_day

                    if not loan.scored:
                        user.points_update(5)
                        loan.scored = True
                    db.session.commit()
                    Thread(target=notification.send([user],"accepted.html","Loan Reply",book,loan.return_date)).start()
                elif loan.loan_status == 'refused':
                    db.session.commit()
                    Thread(target=notification.send([user],"refused.html","Loan Reply",book,loan.return_date)).start()
                elif loan.loan_status == 'queue':
                    db.session.commit()
                    Thread(target=notification.send([user],"queue.html","Loan Reply",book,loan.return_date)).start()

                return { 'data': loan.serialize }, 201
            except Exception as error:
                print(error)
                return { 'data': {'mesage': 'Unexpected Error'} }, 500
        return { 'data ' : {'mesage': 'Request already answered'}}, 409


class ReturnApi(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("loan_id", type=int, required=True,
                                   location='json')
        self.reqparse.add_argument("user_id", type=int, required=True,
                                   location='json')
        self.reqparse.add_argument("confirmed_by", type=str,
                                   location='json')
        super(ReturnApi, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        loan_record_search = Book_loan.query.filter_by(id=args['loan_id']).first()
        return_record_search = Book_return.query.get_or_404(loan_record_search.id)
        print(return_record_search)

        return {'data': [return_record_search.serialize]}, 200

    def post(self):
        try:
            args = self.reqparse.parse_args()
            loan_record = Book_loan.query.filter_by(id=args['loan_id']).first()
            if not loan_record.loan_status == 'accepted':
                return { 'data': { 'message': 'Bad Request' } }, 400
            return_record = Book_return.query.filter_by(book_loan_id =
                                                        loan_record.id).first()
            if not (return_record):
                return_record = Book_return(book_loan_id = loan_record.id,
                                            returned_date = date.today())
                db.session.add(return_record)

            if(args['confirmed_by']=='owner'):
                return_record.owner_confirmation=True
            elif(args['confirmed_by']=='user'):
                return_record.user_confirmation=True
            else:
                return { 'data': { 'message': 'Bad Request' } }, 400
            if return_record.owner_confirmation and return_record.user_confirmation:
                loan_record.loan_status = 'done'
            else:
                loan_record.loan_status = 'accepted'
            db.session.commit()

            return { 'data': return_record.serialize }, 201
        except Exception as error:
            print(error)
            return { 'data': {'mesage': 'Unexpected Error'} }, 500


class DelayApi(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("loan_id",type=int,required=True,
                                    location='json')
        self.reqparse.add_argument("status", type=str,
                                    required=True,location='json')
        super(DelayApi, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        loan_delay = Delayed_return.query.filter_by(book_loan_id=args['loan_id']).first()

        return {'data': [loan_delay.serialize]}, 201

    def post(self):
        try:
            args = self.reqparse.parse_args()
            loan_delay = Book_loan.query.get_or_404(args['loan_id'])
            delay_record= Delayed_return.query.filter_by(book_loan_id =
                                                        loan_delay.id).first()

            if not delay_record:
                delay_record = Delayed_return(book_loan_id = loan_delay.id,
                                                requested_date = loan_delay.return_date+timedelta(days=7))
                db.session.add(delay_record)

            if args['status']=='waiting':
                delay_record.status='waiting'
            elif args['status']=='accepted':
                delay_record.status='accepted'
            elif args['status']=='refused':
                delay_record.status='refused'
            else:
                return { 'data': { 'message': 'Bad Request' } }, 400
            db.session.commit()
            users_mail = User.query.filter_by(id=loan_delay.user_id).first()
            book_mail = Book.query.filter_by(id=loan_delay.book_id).first()

            Thread(target=notification.send([users_mail], "email.html",
                                            delay_record.status,
                                            book_mail,delay_record.requested_date)).start()

            return { 'data': delay_record.serialize }, 201
        except Exception as error:
            print(error)
            return { 'data': {'mesage': 'Unexpected Error'} }, 500


class WishlistApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("title", type=str, location='json')
        self.reqparse.add_argument("user_id", type=int, location='json')
        super(WishlistApi, self).__init__()

    def get(self):
        self.reqparse.add_argument("title", type=str, required=True, location='json')
        self.reqparse.add_argument("user_id", type=int, required=True, location='json')

        args = self.reqparse.parse_args()

        try:
            isbn = isbn_from_words(args['title'])
            book_json = meta(isbn)
            title = book_json['Title']

            wish = Wishlist.query.filter_by(title=title, user_id=args['user_id']).first()

            if wish:
                return {'data': wish.serialize}, 200
            else:
                return {'data': 'Wishlist not found'}, 404
        except Exception:
            return {'data': 'Unexpected Error'}, 500

    def post(self):
        self.reqparse.add_argument("title", type=str, required=True, location='json')
        self.reqparse.add_argument("user_id", type=int, required=True, location='json')
        args = self.reqparse.parse_args()

        user = User.query.filter_by(id=args['user_id']).first()
        if not user:
            return {'data': 'User not found'}, 404

        try:
            isbn = isbn_from_words(args['title'])
            title = meta(isbn)['Title']

            wish = Wishlist.query.filter_by(isbn=isbn, user_id=user.id).first()

            if wish:
                return {'data': wish.serialize}, 200
            else: # If wishlist doesn't exist
                new_wish = Wishlist(isbn=isbn, title=title, user_id=user.id)
                db.session.add(new_wish)
                db.session.commit()
                return {}, 204
        except Exception:
            return {'data': 'Unexpected error'}, 500

api.add_resource(BooksApi, '/api/v1/books', endpoint='books')
api.add_resource(ModifyBooksApi, '/api/v1/books/<int:id>', endpoint='modify_books')
api.add_resource(LoanRequestApi, '/api/v1/books/borrow', endpoint='loan_request')
api.add_resource(LoanReplyApi, '/api/v1/books/borrow/<int:id>', endpoint='loan_reply')
api.add_resource(BooksAvailabilityApi, '/api/v1/books/availability/<int:id>', endpoint='books_availability')
api.add_resource(ReturnApi, '/api/v1/books/return', endpoint='return')
api.add_resource(DelayApi, '/api/v1/books/delay', endpoint='delay')
api.add_resource(WishlistApi, '/api/v1/wish', endpoint='wish')
