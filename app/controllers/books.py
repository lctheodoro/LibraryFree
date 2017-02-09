from flask import json, g,request
from flask_restful import Resource, reqparse
from app import db, auth, api, log__
from app.models.tables import Book, Book_loan, Book_return, User, Wishlist, \
                            Delayed_return, Organization, Topsearches, Author, \
                            Category
from app.models.decorators import is_admin_id
from datetime import timedelta, date
from sqlalchemy.sql import and_
from isbnlib import isbn_from_words,meta
#from isbnlib.registry import bibformatters
from app.controllers import notification
from threading import Thread
from sqlalchemy import desc

class BooksApi(Resource):
    decorators = [auth.login_required]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("title", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("subtitle", type=str, location='json')
        self.reqparse.add_argument("isbn10", type=str, location = 'json')
        self.reqparse.add_argument("isbn13", type=str, location = 'json')
        self.reqparse.add_argument("avatarBase64", type=str, location = 'json')
        self.reqparse.add_argument("avatarUrl", type=str, location = 'json')
        self.reqparse.add_argument("synopsis", type=str, location='json')
        self.reqparse.add_argument("publisher", type=str, location='json')
        self.reqparse.add_argument("publisherDate", type=str, location='json')
        self.reqparse.add_argument("description", type=str, location='json')
        self.reqparse.add_argument("authors", type=list, location='json')
        self.reqparse.add_argument("categories", type=list, location='json')
        self.reqparse.add_argument("edition", type=int, location='json')
        self.reqparse.add_argument("year", type=int, location='json')
        self.reqparse.add_argument("language", type=str, location='json')
        self.reqparse.add_argument("user_id", type=int, location='json')
        self.reqparse.add_argument("organization_id", type=int, location='json')
        super(BooksApi, self).__init__()

    def get(self):
        # This parameters are specific to the GET method
        # because they are not mandatory
        args = {}
        args['title'] = request.args.get("title")
        args['subtitle'] = request.args.get("subtitle")
        args['isbn10'] = request.args.get("isbn10")
        args['isbn13'] = request.args.get("isbn13")
        args['authors'] = request.args.get("authors")
        args['publisher'] = request.args.get("publisher")
        args['publisherDate'] = request.args.get("publisherDate")
        args['categories'] = request.args.get("categories")
        args['edition'] = request.args.get("edition")
        args['year'] = request.args.get("year")
        args['language'] = request.args.get("language")
        args['user_id'] = request.args.get("user_id")
        args['organization_id'] = request.args.get("organization_id")
        args['loan'] = request.args.get("loan")

        if(args['authors']):
            args['authors'] = args['authors'].split(',')
        if(args['categories']):
            args['categories'] = args['categories'].split(',')

        #search_reqparse = reqparse.RequestParser()
        #search_reqparse.add_argument("title", type=str, location='json')
        #search_reqparse.add_argument("subtitle", type=str, location='json')
        #search_reqparse.add_argument("isbn10", type=str, location = 'json')
        #search_reqparse.add_argument("isbn13", type=str, location = 'json')
        #search_reqparse.add_argument("authors", type=list, location='json')
        #search_reqparse.add_argument("publisher", type=str, location='json')
        #search_reqparse.add_argument("publisherDate", type=str, location='json')
        #search_reqparse.add_argument("categories", type=list, location='json')
        #search_reqparse.add_argument("edition", type=int, location='json')
        #search_reqparse.add_argument("year", type=int, location='json')
        #search_reqparse.add_argument("language", type=str, location='json')
        # Also get books owned by a user or organization
        #search_reqparse.add_argument("user_id", type=int, location='json')
        #search_reqparse.add_argument("organization_id", type=int, location='json')

        # retrieving the values
        #args = search_reqparse.parse_args()
        filters_list = []

        if args['title']:
            filters_list.append(
                Book.title.ilike("%{0}%".format(args['title']))
            )

        if args['subtitle']:
            filters_list.append(
                Book.subtitle.ilike("%{0}%".format(args['subtitle']))
            )

        if args['isbn10'] :
            filters_list.append(
                Book.isbn10.ilike("%{0}%".format(args['isbn10']))
            )
        if args['isbn13'] :
            filters_list.append(
                Book.isbn13.ilike("%{0}%".format(args['isbn13']))
            )

        if args['authors']:
            for a in args['authors']:
                filters_list.append(
                    Book.authors.any(Author.name.ilike("%{0}%".format(a)))  #args['authors']))
                )

        if args['publisher']:
            filters_list.append(
                Book.publisher.ilike("%{0}%".format(args['publisher']))
            )

        if args['publisherDate']:
            filters_list.append(
                Book.publisherDate.ilike("%{0}%".format(args['publisherDate']))
            )

        if args['categories']:
            for a in args['categories']:
                filters_list.append(
                    Book.categories.any(Category.name.ilike("%{0}%".format(a)))  #args['categories']))
                )

        if args['edition']:
            filters_list.append(
                Book.edition == args['edition']
            )

        if args['year']:
            filters_list.append(
                Book.year == args['year']
            )

        if args['language']:
            filters_list.append(
                Book.language.ilike("%{0}%".format(args['language']))
            )

        if args['user_id']:
            filters_list.append(
                Book.user_id == args['user_id']
            )

        if args['organization_id']:
            filters_list.append(
                Book.organization_id == args['organization_id']
            )
        if args['loan']:
            filters_list.append(
                Book.loan_user != None
            )
        if filters_list == []:
            books = []
        else:
            filtering = and_(*filters_list)
            books = Book.query.filter(filtering).all()
        return {'data': [book.serialize for book in books]}, log__(200,g.user)

    def post(self):
        try:
            args = self.reqparse.parse_args()
            category = args['categories']
            author = args['authors']
            del args['categories']
            del args['authors']

            book = Book(**args)

            if author:
                for a in author:
                    authors = Author.query.filter_by(name=a).first()
                    if authors is None:
                        authors = Author(name=a)
                        db.session.add(authors)
                        db.session.commit()
                    authors.qtd += 1
                    book.authors.append(authors)
            if category:
                for c in category:
                    categories = Category.query.filter_by(name=c).first()
                    if categories is None:
                        categories = Category(name=c)
                        db.session.add(categories)
                        db.session.commit()
                    categories.qtd += 1
                    book.categories.append(categories)

            if (args['user_id'] and args['organization_id']) or ((not args['user_id'] and not args['organization_id'])):
                return { 'message': 'Bad Request' }, log__(400,g.user)
            if args['user_id'] and (not User.query.get(args['user_id'])):
                return { 'message': 'User not found' }, log__(404,g.user)
            if args['organization_id']:
                org = Organization.query.get(args['organization_id'])
            if args['organization_id'] and ((org is None) or (g.user not in org.managers and g.user.admin == 0)):
                if org is None:
                    return { 'message': 'Organization not found' }, log__(404,g.user)
                if g.user not in org.managers and g.user.admin == 0:
                    return {'message': 'You are not authorized to access this area.'},log__(401,g.user)
            elif args['user_id']!=g.user.id and g.user.admin==0:
                return {'message': 'You are not authorized to access this area.'},log__(401,g.user)
            elif args['user_id']:
                book.is_organization = False
                user = User.query.get_or_404(args['user_id'])
                user.points_update(10)
            else:
                book.is_organization = True

            db.session.add(book)
            db.session.commit()
            return { 'data': book.serialize }, log__(201,g.user)
        except Exception as error:
            print(error)
            return { 'message': 'Bad Request' }, log__(400,g.user)

class CategoriesAPI(Resource):
    decorators = [auth.login_required]

    def get(self):
        categories = Category.query.order_by(desc(Category.qtd)).limit(10).all()
        return {'data': [c.serialize for c in categories]}, log__(200,g.user)

class ModifyBooksApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("subtitle", type=str, location='json')
        self.reqparse.add_argument("isbn10", type=str, location = 'json')
        self.reqparse.add_argument("isbn13", type=str, location = 'json')
        self.reqparse.add_argument("avatarBase64", type=str, location = 'json')
        self.reqparse.add_argument("avatarUrl", type=str, location = 'json')
        self.reqparse.add_argument("synopsis", type=str, location='json')
        self.reqparse.add_argument("publisher", type=str, location='json')
        self.reqparse.add_argument("publisherDate", type=str, location='json')
        self.reqparse.add_argument("description", type=str, location='json')
        self.reqparse.add_argument("authors", type=list, location='json')
        self.reqparse.add_argument("categories", type=list, location='json')
        self.reqparse.add_argument("edition", type=int, location='json')
        self.reqparse.add_argument("year", type=int)
        self.reqparse.add_argument("language", type=str, location='json')
        self.reqparse.add_argument("user_id", type=int, location='json')
        self.reqparse.add_argument("organization_id", type=int, location='json')
        super(ModifyBooksApi, self).__init__()

    def get(self, id):
        book = Book.query.get_or_404(id)
        book_topsearches = Topsearches.query.filter_by(isbn10=book.isbn10).first()
        book_topsearches += Topsearches.query.filter_by(isbn13=book.isbn13).first()
        try:
            if book_topsearches is not None:
                book_topsearches.times += 1
                db.session.commit()
            else:
                book_topsearches = Topsearches(isbn10=book.isbn10,isbn13=book.isbn13, title=book.title, times=1)
                db.session.add(book_topsearches)
                db.session.commit()
            return {'data': book.serialize}, log__(200,g.user)
        except Exception as error:
            if str(error)=="404: Not Found":
                return { 'message': 'The object you are looking for was not found'}, log__(404,g.user)
            else:
                return {'message': 'Unexpected error'}, log__(500,g.user)

    def put(self, id):
        try:
            book = Book.query.get_or_404(id)
            if book.is_organization:
                org = Organization.query.get(book.organization_id)
                if g.user not in org.managers and g.user.admin == 0:
                    return {'message': 'You are not authorized to access this area.'},log__(401,g.user)
            else:
                if g.user.id != book.user_id and g.user.admin == 0:
                    return {'message': 'You are not authorized to access this area.'},log__(401,g.user)

            args = self.reqparse.parse_args()

            for key, value in args.items():
                if value is not None:
                    if key is 'authors':
                        for b in book.authors:
                            b.qtd -= 1
                            book.authors.remove(b)
                        for a in args['authors']:
                            authors = Author.query.filter_by(name=a).first()
                            if authors is None:
                                authors = Author(name=a)
                                db.session.add(authors)
                                db.session.commit()
                            authors.qtd += 1
                            book.authors.append(authors)
                    elif key is 'categories':
                        for b in book.categories:
                            b.qtd -= 1
                            book.categories.remove(b)
                        for c in args['categories']:
                            categories = Category.query.filter_by(name=c).first()
                            if categories is None:
                                categories = Category(name=c)
                                db.session.add(categories)
                                db.session.commit()
                            categories.qtd += 1
                            book.categories.append(categories)
                    else:
                        setattr(book, key, value)

            db.session.commit()
            return {'data': book.serialize}, log__(200,g.user)
        except Exception as error:
            if str(error)=="404: Not Found":
                return { 'message': 'The object you are looking for was not found'}, log__(404,g.user)
            else:
                return { 'message': 'Unexpected Error' }, log__(500,g.user)
    @is_admin_id
    def delete(self, id):
        try:
            book = Book.query.get_or_404(id)
            if book.is_organization:
                user = User.query.get_or_404(book.organization_id)
            else:
                user = User.query.get_or_404(book.user_id)
            for b in book.authors:
                b.qtd -= 1
            for b in book.categories:
                b.qtd -= 1
            user.points_update(-10)
            db.session.delete(book)
            db.session.commit()
            return log__(204,g.user)
        except Exception as error:
            if str(error)=="404: Not Found":
                return { 'message': 'The object you are looking for was not found'}, log__(404,g.user)
            else:
                return { 'message': 'Unexpected Error' }, log__(500,g.user)

class LoanRequestApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("book_id", type=int, required=True,
                                    location='json')
        super(LoanRequestApi,self).__init__()

    def get(self):
        try:
            args = {}
            args['user_id'] = request.args.get("user_id")
            args['book_id'] = request.args.get("book_id")
            args['open'] = request.args.get("open")
            args['user_type'] = request.args.get("user_type")
            args['is_org'] = request.args.get("is_org")

            if args['user_id'] and args['book_id']:
                return {'message': 'Choose only one argument'}, log__(400,g.user)
            elif args['user_id'] and args['open']:
                if args['user_type'].lower() == 'owner':
                    if args['is_org']:
                        loans = Book_loan.query.filter_by(organization_id=args['user_id'],
                                                        loan_status='requested').all()
                    else:
                        loans = Book_loan.query.filter_by(owner_id=args['user_id'],
                                                        loan_status='requested').all()
                    return {'data': [l.serialize for l in loans]}, log__(200,g.user)
                elif args['user_type'].lower() == "user":
                    loans = Book_loan.query.filter_by(user_id=args['user_id'],
                                                        loan_status='requested').all()
                    return {'data': [l.serialize for l in loans]}, log__(200,g.user)
                print("DEU RUIM")
                return {'message': 'Bad Request'}, log__(400,g.user)
            elif args['user_id']:
                if args['user_type'].lower() == 'owner':
                    if args['is_org']:
                        loans = Book_loan.query.filter_by(organization_id=args['user_id']).all()
                    else:
                        loans = Book_loan.query.filter_by(owner_id=args['user_id']).all()
                    return {'data': [l.serialize for l in loans]}, log__(200,g.user)
                elif args['user_type'].lower() == "user":
                    loans = Book_loan.query.filter_by(user_id=args['user_id'],).all()
                    return {'data': [l.serialize for l in loans]}, log__(200,g.user)
                print("DEU RUIM")
                return {'message': 'Bad Request'}, log__(400,g.user)
            elif args['book_id']:
                loans = Book_loan.query.filter_by(book_id=args['book_id']).all()
                return {'data': [l.serialize for l in loans]}, log__(200,g.user)
            else:
                return {'message': 'Bad Request'}, log__(400,g.user)

        except Exception as error:
            print(error)
            return {'message': 'Unexpected Error'}, log__(500,g.user)

    def post(self):
        args = self.reqparse.parse_args()
        # Checks if book_loan already exists
        try:
            l = Book_loan.query.filter_by(book_id=args['book_id'],
                                          user_id=g.user.id,
                                          loan_status='requested').first()
            book = Book.query.get_or_404(args['book_id'])
            if l==None and not (not book.is_organization and g.user.id==book.user_id):
                if book.is_organization:
                    loan = Book_loan(book_id=args['book_id'],user_id=g.user.id,
                                        organization_id=book.organization_id)
                else:
                    loan = Book_loan(book_id=args['book_id'],user_id=g.user.id,owner_id=book.user_id)
                loan.loan_status = 'requested'
                loan.scored = False

                # Get the book's owner whether it's an organization or a user
                if book.is_organization:
                    owner = Organization.query.get_or_404(book.organization_id)
                else:
                    owner = User.query.get_or_404(book.user_id)

                #Thread(target=notification.send([owner],"loanrequest.html","Loan Request",book)).start()

                db.session.add(loan)
                db.session.commit()
                return { 'data': loan.serialize }, log__(201,g.user)
            elif not book.is_organization and g.user.id==book.user_id:
                return { 'message': 'The book owner can not borrow it'},log__(400,g.user)
            return { 'message': 'Request already made' }, log__(500,g.user)
        except Exception as error:
            print(error)
            if str(error)=="404: Not Found":
                return { 'message': 'The object you are looking for was not found'}, log__(404,g.user)
            else:
                return { 'message': 'Unexpected Error' }, log__(500,g.user)


class LoanReplyApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("loan_status", type=str,
                                    location='json')
        super(LoanReplyApi,self).__init__()

    def get(self,id):
        try:
            loan =  Book_loan.query.get_or_404(id)
            book = Book.query.get_or_404(loan.book_id)

            # Verify user logged in
            if g.user.id != book.user_id and g.user.id!=loan.user_id:
                return {'message': 'You are not authorized to access this area'}, log__(401,g.user)

            loan = Book_loan.query.get_or_404(id)
            return { 'data': loan.serialize }, log__(200,g.user)
        except Exception as error:
            if str(error)=="404: Not Found":
                return { 'message': 'The object you are looking for was not found'}, log__(404,g.user)
            else:
                return {'message': 'Unexpected Error'}, log__(500,g.user)

    def post(self,id):
        args = self.reqparse.parse_args()

        loan =  Book_loan.query.get_or_404(id)
        book = Book.query.get_or_404(loan.book_id)

        # Verify user logged in
        if book.is_organization:
            org = Organization.query.get(book.organization_id)
            if g.user not in org.managers and g.user.admin==0:
                return {'message': 'You are not authorized to access this area'}, log__(401,g.user)
        elif g.user.id != book.user_id and g.user.admin == 0:
            return {'message': 'You are not authorized to access this area'}, log__(401,g.user)

        if args['loan_status'] == "requested" or loan.loan_status == "done" or \
                args['loan_status'] == None or loan.loan_status=="accepted":
            return {'message': 'Bad Request'}, log__(400,g.user)
        if loan.loan_status != args['loan_status']:
            try:
                user = User.query.get_or_404(loan.user_id)

                loan.loan_status = args['loan_status']

                # Create the date of return
                if loan.loan_status == 'accepted' and book.available:
                    loan.loan_date = date.today()
                    return_day = date.today() + timedelta(days=10)
                    book.available = False
                    book.loan_user = user.id

                    # If it falls on a weekend it updates the date
                    # for the next Monday of this weekend
                    if return_day.strftime('%A') == 'Sunday':
                        return_day += timedelta(days=1)
                    elif return_day.strftime('%A') == 'Saturday':
                        return_day += timedelta(days=2)
                    loan.return_date = return_day

                    # Gamefication
                    if not loan.scored:
                        user.points_update(5)
                        loan.scored = True
                    print(loan.loan_date,"\n",loan.return_date)

                    #Thread(target=notification.send([user],"accepted.html","Loan Reply",book,loan.return_date)).start()
                    db.session.commit()
                elif loan.loan_status == 'refused':
                    #Thread(target=notification.send([user],"refused.html","Loan Reply",book)).start()
                    db.session.commit()
                elif loan.loan_status == 'queue':
                    #Thread(target=notification.send([user],"queue.html","Loan Reply",book)).start()
                    db.session.commit()
                else:
                    return {'data':'Bad Request'}, log__(400,g.user)
                print(loan.book)
                return { 'data': loan.serialize }, log__(201,g.user)
            except Exception as error:
                if str(error)=="404: Not Found":
                    return { 'message': 'The object you are looking for was not found'}, log__(404,g.user)
                else:
                    print(error)
                    return {'message': 'Unexpected Error'}, log__(500,g.user)
        return {'message': 'Request already answered'}, log__(409,g.user)


class ReturnApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("loan_id", type=int, required=True,
                                   location='json')
        super(ReturnApi, self).__init__()

    def get(self):
        try:
            args = {}
            args['loan_id'] = request.args.get("loan_id")
            args['user_id'] = request.args.get("user_id")
            args['owner_id'] = request.args.get("owner_id")

            if (args['loan_id'] and args['user_id']) or (args['loan_id'] and
                args['owner_id']) or (args['user_id'] and args['owner_id']):
                return {'message': 'Choose only one argument'}, log__(400,g.user)
            elif args['loan_id']:
                loan_record_search = Book_loan.query.filter_by(id=args['loan_id']).first()
                if loan_record_search:
                    return_record_search = Book_return.query.filter_by(book_loan_id=loan_record_search.id).first()
                    if return_record_search:
                        book = Book.query.get(loan_record_search.book_id)
                        if ((g.user.id != return_record_search.user_id) and g.user.admin==0):
                            return {'message': 'You are not authorized to access this area'}, log__(401,g.user)
                        if book.is_organization:
                            org = Organization.query.get(book.organization_id)
                            if g.user not in org.managers and g.user.admin == 0:
                                return {'message': 'You are not authorized to access this area'}, log__(401,g.user)
                        else:
                            if g.user.id != book.user_id and g.user.admin == 0:
                                return {'message': 'You are not authorized to access this area'}, log__(401,g.user)
                        return {'data': [return_record_search.serialize]}, log__(200,g.user)
            elif args['user_id']:
                if g.user.id == int(args['user_id']) or g.user.admin!=0:
                    return_books = Book_return.query.filter_by(user_id=args['user_id']).all()
                    return {'data': [r.serialize for r in return_books]},log__(200,g.user)
                else:
                    return {'message': 'You are not authorized to access this area'}, log__(401,g.user)
            elif args['owner_id']:
                if g.user.id == int(args['owner_id']) or g.user.admin!=0:
                    return_books = Book_return.query.filter_by(user_owner=args['owner_id']).all()
                    return {'data': [r.serialize for r in return_books]},log__(200,g.user)
                else:
                    return {'message': 'You are not authorized to access this area'}, log__(401,g.user)

            return {'message': 'Bad Request'}, log__(400,g.user)
        except Exception as error:
            print(error)
            return {'message': 'Unexpected Error'},log__(500,g.user)

    def post(self):
        try:
            args = self.reqparse.parse_args()
            loan_record = Book_loan.query.filter_by(id=args['loan_id']).first()
            if not loan_record.loan_status == 'accepted':
                return { 'message': 'Bad Request' }, log__(400,g.user)
            return_record = Book_return.query.filter_by(book_loan_id =
                                                        loan_record.id).first()
            book = Book.query.get_or_404(loan_record.book_id)
            if not (return_record):
                return_record = Book_return(book_loan_id = loan_record.id,
                                            returned_date = date.today())
                if not book.is_organization:
                    return_record.user_owner = book.user_id
                else:
                    return_record.org_owner = book.organization_id
                return_record.user_id = loan_record.user_id

            if loan_record.user_id==g.user.id:
                return_record.user_confirmation=True
                db.session.add(return_record)
            elif book.is_organization:
                org = Organization.query.get(book.organization_id)
                if g.user in org.managers:
                    return_record.owner_confirmation=True
                    db.session.add(return_record)
            elif not book.is_organization and g.user.id == book.user_id:
                return_record.owner_confirmation=True
                db.session.add(return_record)
            else:
                return { 'data': { 'message': 'Bad Request' } }, log__(400,g.user)
            if return_record.owner_confirmation and return_record.user_confirmation:
                loan_record.loan_status = 'done'
                book.available = True
                book.loan_user = None
            else:
                loan_record.loan_status = 'accepted'

            db.session.commit()
            return { 'data': return_record.serialize }, log__(201,g.user)
        except Exception as error:
            print(error)
            if str(error)=="404: Not Found":
                return { 'message': 'The object you are looking for was not found'}, log__(404,g.user)
            else:
                return {'message': 'Unexpected Error'}, log__(500,g.user)


class DelayApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("loan_id",type=int, location='json')
        self.reqparse.add_argument("status", type=str, location='json')
        super(DelayApi, self).__init__()

    def get(self):
        #args = self.reqparse.parse_args()
        args = {}
        args['loan_id'] = request.args.get("loan_id")

        try:
            loan_delay = Delayed_return.query.filter_by(book_loan_id=args['loan_id']).first()

            if loan_delay is None:
                return {'message': 'The object you are looking for was not found.'}, log__(404,g.user)

            loan = Book_loan.query.get_or_404(args['loan_id'])
            book = Book.query.get_or_404(loan.book_id)

            if book.is_organization:
                org = Organization.query.get_or_404(book.organization_id)
            if book.is_organization and g.user in org.managers:
                return {'data': [loan_delay.serialize]}, log__(201,g.user)
            elif g.user.id == book.user_id or g.user.admin!=0:
                return {'data': [loan_delay.serialize]}, log__(201,g.user)
            elif g.user.id == loan.user_id or g.user.admin!=0:
                return {'data': [loan_delay.serialize]}, log__(201,g.user)

            return {'message': 'You are not authorized to access this area'}, log__(401,g.user)
        except Exception as error:
            if str(error)=="404: Not Found":
                return { 'message': 'The object you are looking for was not found'}, log__(404,g.user)
            else:
                return {'message': 'Unexpected Error'}, log__(500,g.user)

    def post(self):
        try:
            args = self.reqparse.parse_args()
            loan_delay = Book_loan.query.get_or_404(args['loan_id'])
            delay_record= Delayed_return.query.filter_by(book_loan_id =
                                                        loan_delay.id).first()
            if loan_delay.loan_status is not "done":
                book = Book.query.get_or_404(loan_delay.book_id)
                if g.user.id == loan_delay.user_id:
                    if not delay_record:
                        delay_record = Delayed_return(book_loan_id = loan_delay.id,
                                                        requested_date = loan_delay.return_date+timedelta(days=7))
                        db.session.add(delay_record)
                    elif delay_record.status is not "waiting":
                        return {'message': 'Request already answered'}, log__(409,g.user)

                elif book.is_organization:
                    org = Organization.query.get_or_404(book.organization_id)
                    if g.user in org.managers:
                        if args['status']=="accepted":
                            delay_record.status='accepted'
                            loan_delay.return_date = delay_record.requested_date
                        elif args['status']=="refused":
                            delay_record.status='refused'
                        else:
                            return { 'message': 'Bad Request' }, log__(400,g.user)
                    else:
                        return {'message': 'You are not authorized to access this area'}, log__(401,g.user)
                elif g.user.id == book.user_id:
                    if args['status']=="accepted":
                        delay_record.status='accepted'
                        loan_delay.return_date = delay_record.requested_date
                    elif args['status']=="refused":
                        delay_record.status='refused'
                    else:
                        return { 'message': 'Bad Request' }, log__(400,g.user)
                else:
                    return {'message': 'You are not authorized to access this area'}, log__(401,g.user)
                db.session.commit()
                users_mail = User.query.filter_by(id=loan_delay.user_id).first()

                #Thread(target=notification.send([users_mail], "email.html",
                #                                delay_record.status,
                #                                book,delay_record.requested_date)).start()

                return { 'data': delay_record.serialize }, log__(201,g.user)
            else:
                return {'message': 'Book returned'},log__(409,g.user)
        except Exception as error:
            if str(error)=="404: Not Found":
                return { 'message': 'The object you are looking for was not found'}, log__(404,g.user)
            else:
                return { 'message': 'Unexpected Error' }, log__(500,g.user)


class BooksAvailabilityApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        super(BooksAvailabilityApi, self).__init__()

    def get(self, id):
        book = Book.query.filter_by(id=id).first()

        if(book): # Book found
            book_loans = Book_loan.query.filter_by(book_id=book.id).all()
            if(book_loans): # If there's any book loan
                for loan in book_loans: # Sweep all loans
                    book_return = Book_return.query.filter_by(book_loan_id=loan.id).first()
                    if(book_return):
                        if(not book_return.user_confirmation or not book_return.owner_confirmation):
                            return {'data': {'status': 'Unavailable'}}, log__(200,g.user)
                    else: # Book not returned yet
                        return {'data': {'status': 'Unavailable'}}, log__(200,g.user)
                return {'data': {'status': 'Available'}}, log__(200,g.user) # All loans returned
            else: # Book not loaned yet
                return {'data': {'status': 'Available'}}, log__(200,g.user)
        else: # Book not found
            return {'data': {'message': 'Book not found'}}, log__(404,g.user)

class WishlistApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("title", type=str, location='json')
        self.reqparse.add_argument("user_id", type=int, location='json')
        super(WishlistApi, self).__init__()

    def get(self):
        # Required arguments
        #self.reqparse.add_argument("user_id", type=int, required=True, location='json')

        #args = self.reqparse.parse_args()
        args = {}
        args['user_id'] = request.args.get("user_id")

        user = User.query.filter_by(id=args['user_id']).first()

        if(not user):
            return {'data': {'message': 'User not found'}}, log__(404,g.user)

        try:
            wishlist = Wishlist.query.filter_by(user_id=args['user_id']).all()
            if wishlist:
                return {'data': [wish.serialize for wish in wishlist]}, log__(200,g.user)
            else: # Wishlist is empty
                return {'data': []}, log__(200,g.user)
        except Exception:
            return {'message': 'Unexpected Error'}, log__(500,g.user)

    def post(self):
        # Required arguments
        self.reqparse.add_argument("title", type=str, required=True, location='json')
        self.reqparse.add_argument("isbn", type=str, required=True, location='json')

        args = self.reqparse.parse_args()

        user = g.user
        if not user: # User not found
            return {'message': 'User not found'}, log__(404,g.user)
        try:
            wish = Wishlist.query.filter_by(isbn=args['isbn'], user_id=user.id).first()

            if wish: # Book already in the wishlist
                return {'data': wish.serialize}, log__(200,g.user)
            else: # If book not in the wishlist
                new_wish = Wishlist(isbn=args['isbn'], title=args['title'], user_id=user.id)
                db.session.add(new_wish)
                db.session.commit()
                return {'data': new_wish.serialize}, log__(201,g.user)
        except Exception as error:
            print(error)
            return {'message': 'Unexpected Error'}, log__(500,g.user)


class TopsearchesAPI(Resource):

    def get(self):
        top_searches = [t.serialize for t in Topsearches.query.all()]
        # Sorting first by the times, after by the alfabetic order of the title
        return { 'data' :
                sorted(top_searches, key=lambda t: (-t['times'], t['title'])) }, log__(200)


api.add_resource(BooksApi, '/api/v1/books', endpoint='books')
api.add_resource(TopsearchesAPI, '/api/v1/books/top', endpoint='top')
api.add_resource(ModifyBooksApi, '/api/v1/books/<int:id>', endpoint='modify_books')
api.add_resource(LoanRequestApi, '/api/v1/books/borrow', endpoint='loan_request')
api.add_resource(LoanReplyApi, '/api/v1/books/borrow/<int:id>', endpoint='loan_reply')
api.add_resource(ReturnApi, '/api/v1/books/return', endpoint='return')
api.add_resource(DelayApi, '/api/v1/books/delay', endpoint='delay')
api.add_resource(BooksAvailabilityApi, '/api/v1/books/availability/<int:id>', endpoint='books_availability')
api.add_resource(WishlistApi, '/api/v1/wish', endpoint='wish')
api.add_resource(CategoriesAPI,'/api/v1/books/categories',endpoint='categories')
