from flask import jsonify
from flask_restful import Resource, reqparse
from app import app, db, auth
from app.models.tables import Book_loan, Book_return




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
                db.session.add(book_return)

            if(args['confirmed_by']=='owner'):
                return_record.owner_confirmation=True
            else if(args['confirmed_by']=='user'):
                return_record.user_confirmation=True
            else:
                abort(400)
            db.session.commit()

            return 204

        def get(self):
            args = self.reqparse.parse_args()
            loan_record_search = Book_loan.query.filter_by(book_id=args['book_id'],
                                                      owner_id=args['owner_id'],
                                                      user_id= args['user_id']).
                                                      first()
            return_record_search = Book_return.query.filter_by(book_loan_id =
                                                        loan_record.id).first()

            return {'data': [return_record_search.serialize]}, 200


    api.add_resource(ReturnApi, '/api/v1/books/return', endpoint='return')
