from flask import g, jsonify
from flask_restful import Resource, reqparse
from app import app, db, auth, api
from app.models.tables import User, Organization, Feedback, Book_loan
from app.models.decorators import is_user, is_manager
from math import ceil

@auth.verify_password
def verify_password(email_or_token, password):
    """
    This function verify if the user has the correct credentials.
    If it has, we can confirm the login and every login_required
    decorator will pass.
    """
    # tries to get the user by token
    user = User.verify_auth_token(email_or_token)
    if not user:
        # tries to get the user by email and password
        user = User.query.filter_by(email=email_or_token).first()
        if not user or not user.verify_password(password):
            return False
    # saves the user in the global object 'user'
    g.user = user
    return True


@app.route('/api/v1/tokens', methods=['GET'])
@auth.login_required
def get_auth_token():
    """
        This function returns a token for authentication.
        It guarantees the security of user's information.
    """
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


class UsersApi(Resource):
    def __init__(self):
        # whenever we want to receive arguments from other parts
        # we need to use the RequestParser
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("name", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("email", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("password", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("city", type=str, location='json')
        self.reqparse.add_argument("phone", type=str, location='json')
        super(UsersApi, self).__init__()

    def get(self):
        # Table.query makes a search (select) in the database
        users = User.query.all()
        # we should return serialized objects because they are ready to
        # be converted to JSON
        # an HTTP status code is also important
        return {'data': [u.serialize for u in users]}, 200

    def post(self):
        args = self.reqparse.parse_args()
        user = User(**args)
        # we will ALWAYS encrypt a new password
        user.hash_password(args['password'])
        db.session.add(user)

        try:
            db.session.commit()
            user.check_register()
            db.session.commit()

            return {'data': user.serialize}, 201
        except Exception as error:
            print(error)
            if "duplicate key value in error":
                return {'data': {'message': 'User already exists'}}, 409
            else:
                return {'data':
                        {'message': 'Could\'nt complete the request'}}, 503


class ModifyUsersApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("name", type=str, location='json')
        self.reqparse.add_argument("email", type=str, location='json')
        self.reqparse.add_argument("password", type=str, location='json')
        self.reqparse.add_argument("city", type=str, location='json')
        self.reqparse.add_argument("phone", type=str, location='json')
        super(ModifyUsersApi, self).__init__()

    def get(self, id):
        user = User.query.get_or_404(id)
        return {'data': user.serialize}, 200

    # this decorator verify if the object belongs to the user
    # if so, it can be edited, else the user is unauthorized
    @is_user
    def put(self, id):
        user = User.query.get_or_404(id)
        args = self.reqparse.parse_args()
        # when we have an update to do, we can't simply update all information
        # using the arguments from reqparse, because some may be empty
        # then we have to keep the information
        for key, value in args.items():
            # this will filter only valid values
            if key == 'password' and value is not None:
                # we will ALWAYS encrypt a new password
                user.hash_password(value)
            elif value is not None:
                setattr(user, key, value)
        user.check_register(user.id)
        db.session.commit()
        return {'data': user.serialize}, 200

    @is_user
    def delete(self, id):
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        return 204


class OrganizationsApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("name", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("description", type=str, location='json')
        self.reqparse.add_argument("managers", type=list, required=True,
                                   location='json')
        super(OrganizationsApi, self).__init__()

    def get(self):
        organizations = Organization.query.all()
        return {'data': [org.serialize for org in organizations]}, 200

    def post(self):
        args = self.reqparse.parse_args()
        org = Organization(name=args['name'],
                           description=args['description'])
        db.session.add(org)

        # we receive a list of IDs and select all users that have one of them
        for user in User.query.filter(User.id.in_(args['managers'])).all():
            user.organization_id = org.id

        db.session.commit()

        return {'data': org.serialize}, 200


class ModifyOrganizationsApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("name", type=str, location='json')
        self.reqparse.add_argument("description", type=str, location='json')
        self.reqparse.add_argument("managers", type=str, location='json')

        super(ModifyOrganizationsApi, self).__init__()

    def get(self, id):
        org = Organization.query.get_or_404(id)
        return {'data': org.serialize}, 200

    # this decorator verify if the user is one of the company managers
    # if so, it can be edited, else the user is unauthorized
    @is_manager
    def put(self, id):
        args = self.reqparse.parse_args()
        org = Organization.query.get_or_404(id)
        for key, value in args.items():
            if value is not None:
                setattr(org, key, value)
        db.session.commit()
        return {'data': org.serialize}, 200

    @is_manager
    def delete(self, id):
        org = Organization.query.get_or_404(id)
        db.session.delete(org)
        db.session.commit()
        return 204


class FeedbackApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("transaction_id", type=int, location='json')
        self.reqparse.add_argument("user", type=str, location='json')
        self.reqparse.add_argument("user_evaluation", type=int, location='json')
        self.reqparse.add_argument("time_evaluation", type=int, location='json')
        self.reqparse.add_argument("book_evaluation", type=int, location='json')
        self.reqparse.add_argument("interaction_evaluation", type=int, location='json')
        self.reqparse.add_argument("comments", type=str, location='json')

        super(FeedbackApi, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        feedback = Feedback(**args)
        db.session.add(feedback)
        try:
            loan = Book_loan.query.filter_by(id=feedback.transaction_id).first()
            book = Book.query.filter_by(id=loan.book_id).first()
            if feedback.user == "user":
                if book.is_organization:
                    user = User.query.filter_by(id=book.organization_id).first()
                else:
                    user = User.query.filter_by(id=book.user_id).first()
            else:
                user = User.query.filter_by(id=loan.user_id).first()

            if user.evaluation == 0:
                user.evaluation = feedback.user_evaluation
            else:
                user.evaluation = ceil((user.evaluation +
                                   feedback.user_evaluation) / 2)
            if feedback.book_evaluation == 5:
                user.points_update(8,user.id)
                feedback.scored_update(8,user.id)
            if feedback.time_evaluation == 5:
                user.points_update(8,user.id)
                feedback.scored_update(8,user.id)
            db.session.commit()
            return { 'data': feedback.serialize }, 200
        except Exception as error:
            print(error)
            return { 'data': { 'message': 'Unexpected Error' } }, 500


class ModifyFeedbackApi(Resource):
    decorators = [auth.login_required]

    def get(self, id):
        feedback = Feedback.query.get_or_404(id)
        return { 'data': feedback.serialize }, 200

    def delete(self, id):
        feedback = Feedback.query.get_or_404(id)
        if feedback.user == "owner":
            
            loan = Book_loan.query.filter_by(id=feedback.transaction_id).first()
            book = Boook.query.filter_by(id=loan.book_id).all()

            if book.is_organization:
                user = User.query.filter_by(id=book.organization_id).first()
            else:
                user = User.query.filter_by(id=book.user_id).first()

            user.points_update(-feedback.points)

        db.session.delete(feedback)
        db.session.commit()
        return 204

# for each resource we need to specify an URI and an endpoint
# the endpoint is a "reference" to each resource
api.add_resource(UsersApi, '/api/v1/users', endpoint='users')
api.add_resource(ModifyUsersApi, '/api/v1/users/<int:id>',
                 endpoint='modify_users')
api.add_resource(OrganizationsApi, '/api/v1/organizations',
                 endpoint='organizations')
api.add_resource(ModifyOrganizationsApi, '/api/v1/organizations/<int:id>',
                 endpoint='modify_organizations')
api.add_resource(FeedbackApi, '/api/v1/feedbacks', endpoint='feedback')
api.add_resource(ModifyFeedbackApi, '/api/v1/feedbacks/<int:id>',
                 endpoint='modify_feedback')

# if you want to test any resource, try using CURL in the terminal, like:
# $ curl -u USERAME:PASSWORD -H "Content-Type: application/json" -d '{"key": "value", "key": "value"}' -X GET/POST/PUT/DELETE -i http://localhost:5000/RESOURCE_URI
# or try to use a visual tool like Postman
