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
