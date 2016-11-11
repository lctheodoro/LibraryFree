from flask import g, jsonify
from flask_restful import Resource, reqparse
from app import app, db, auth, api
from app.models.tables import Book
from sqlalchemy.sql import and_, or_


class BooksApi(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("title", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("synopsis", type=str, location='json')
        self.reqparse.add_argument("author", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("publisher", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("edition", type=int, location='json')
        self.reqparse.add_argument("year", type=int, location='json')
        self.reqparse.add_argument("language", type=str, location='json')
        self.reqparse.add_argument("genre", type=str, location='json')
        super(BooksApi, self).__init__()

    def get(self):
        # This parameters are specific to the GET method
        # because they are not mandatory
        search_reqparse = reqparse.RequestParser()
        search_reqparse.add_argument("title", type=str, location='json')
        search_reqparse.add_argument("author", type=str, location='json')
        search_reqparse.add_argument("publisher", type=str, location='json')
        search_reqparse.add_argument("genre", type=str, location='json')

        # retrieving the values
        args = search_reqparse.parse_args()

        filters_list = []

        if args['title']:
            filters_list.append(Book.title.ilike("%{0}%".format(args['title'])))

        if args['author']:
            filters_list.append(
                Book.author.ilike("%{0}%".format(args['author']))
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
        db.session.add(book)
        db.session.commit()
        return {'data': book.serialize}, 200


class ModifyBooksApi(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("title", type=str, location='json')
        self.reqparse.add_argument("synopsis", type=str, location='json')
        self.reqparse.add_argument("author", type=str, location='json')
        self.reqparse.add_argument("publisher", type=str, location='json')
        self.reqparse.add_argument("edition", type=int, location='json')
        self.reqparse.add_argument("year", type=int, location='json')
        self.reqparse.add_argument("language", type=str, location='json')
        self.reqparse.add_argument("genre", type=str, location='json')
        super(ModifyBooksApi, self).__init__()

    def get(self, id):
        book = Book.query.get_or_404(id)
        return {'data': book.serialize}, 200

    def put(self, id):
        book = Book.query.get_or_404(id)
        args = self.reqparse.parse_args()

        for key, value in args.items():
            if value is not None:
                setattr(book, key, value)

        db.session.commit()
        return {'data': book.serialize}, 200

    def delete(self, id):
        book = Book.query.get_or_404(id)
        db.session.delete(book)
        db.session.commit()
        return 204

api.add_resource(BooksApi, '/api/v1/books', endpoint='books')
api.add_resource(ModifyBooksApi, '/api/v1/books/<int:id>',
                 endpoint='modify_books')
