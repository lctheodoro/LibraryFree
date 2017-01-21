from flask import g, jsonify,abort, request
from flask_restful import Resource, reqparse
from app import app, db, auth, api, log__
from app.models.tables import User, Organization, Feedback, Book_loan, Book, Book_return
from app.models.decorators import is_user, is_manager, is_admin, is_admin_id
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
            log__(401)
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
        
    def post(self):
        args = self.reqparse.parse_args()
        user = User(**args)
        # we will ALWAYS encrypt a new password
        user.hash_password(args['password'])
        db.session.add(user)

        try:
            db.session.commit()
            # Gamefication
            user.check_register()
            db.session.commit()

            return {'data': user.serialize}, log__(201)
        except Exception as error:
            print(error)
            if "duplicate key value in error":
                return { 'message': 'User already exists' }, log__(409)
            else:
                return { 'message': 'Could\'nt complete the request' }, log__(503)


class ModifyUsersApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("name", type=str, location='json')
        self.reqparse.add_argument("email", type=str, location='json')
        self.reqparse.add_argument("password", type=str, location='json')
        self.reqparse.add_argument("city", type=str, location='json')
        self.reqparse.add_argument("phone", type=str, location='json')
        self.reqparse.add_argument("admin",type=str,location='json')
        super(ModifyUsersApi, self).__init__()

    @is_user
    def get(self, id):
        user = User.query.get_or_404(id)
        return {'data': user.serialize}, log__(200,g.user)

    # this decorator verify if the object belongs to the user
    # if so, it can be edited, else the user is unauthorized
    @is_user
    def put(self, id):
        try:
            user = User.query.get_or_404(id)
            args = self.reqparse.parse_args()
            # when we have an update to do, we can't simply update all information
            # using the arguments from reqparse, because some may be empty
            # then we have to keep the information
            if g.user.admin == 2:
                administrator = True
            else:
                administrator = False
            for key, value in args.items():
                if key == 'admin' and value is not None and not administrator:
                    return {'message': 'You are not authorized to access this area.'},log__(401,g.user)
                # this will filter only valid values
                elif key == 'password' and value is not None:
                    # we will ALWAYS encrypt a new password
                    user.hash_password(value)
                elif value is not None:
                    if user.admin and not administrator and not user is g.user:
                        return {'message': 'You are not authorized to access this area.'},log__(401,g.user)
                    else:
                        setattr(user, key, value)
            user.check_register()
            db.session.commit()
            return {'data': user.serialize}, log__(200,g.user)
        except Exception as error:
            print("ERROR: " + str(error))
            return { 'message': 'Unexpected Error' }, log__(500,g.user)

    @is_admin_id
    def delete(self, id):
        user = User.query.get_or_404(id)
        if user.admin == 2 and not g.user.admin == 2:
            return {'message': 'You are not authorized to access this area.'},log__(401,g.user)
        db.session.delete(user)
        #db.session.commit()
        return log__(204,g.user)


class OrganizationsApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("name", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("email", type=str, required=True,
                                   location='json')
        self.reqparse.add_argument("description", type=str, location='json')
        self.reqparse.add_argument("managers", type=list, required=True,
                                   location='json')
        super(OrganizationsApi, self).__init__()

    @is_admin
    def get(self):
        organizations = Organization.query.all()
        return {'data': [org.serialize for org in organizations]}, log__(200,g.user)

    @is_admin
    def post(self):
        args = self.reqparse.parse_args()
        org = Organization(name=args['name'],
                           description=args['description'],
                           email=args['email'])
        db.session.add(org)

        # we receive a list of IDs and select all users that have one of them
        for user in User.query.filter(User.id.in_(args['managers'])).all():
            user.organization_id = org.id

        db.session.commit()

        return {'data': org.serialize}, log__(201,g.user)


class ModifyOrganizationsApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("name", type=str, location='json')
        self.reqparse.add_argument("description", type=str, location='json')
        self.reqparse.add_argument("managers", type=list, location='json')

        super(ModifyOrganizationsApi, self).__init__()

    @is_manager
    def get(self, id):
        org = Organization.query.get_or_404(id)
        return {'data': org.serialize}, log__(200,g.user)

    # this decorator verify if the user is one of the company managers
    # if so, it can be edited, else the user is unauthorized
    @is_manager
    def put(self, id):
        try:
            args = self.reqparse.parse_args()
            org = Organization.query.get_or_404(id)
            #for key, value in args.items():
            if args['name'] is not None:
                setattr(org, 'name', args['name'])
            if args['description'] is not None:
                setattr(org, 'description', args['description'])
            if args['managers'] is not None:
                for u in org.managers:
                    u.organization_id = None
                for m in User.query.filter(User.id.in_(args['managers'])).all():
                    m.organization_id = org.id
            db.session.commit()
            return {'data': org.serialize}, log__(200,g.user)
        except Exception as error:
            print("ERROR: " + str(error))
            return { 'message': 'Unexpected Error' }, log__(500,g.user)

    @is_admin_id
    def delete(self, id):
        org = Organization.query.get_or_404(id)
        db.session.delete(org)
        db.session.commit()
        return {}, log__(204,g.user)


class FeedbackApi(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("transaction_id", type=int, location='json')
        self.reqparse.add_argument("user_evaluation", type=int, location='json')
        self.reqparse.add_argument("time_evaluation", type=int, location='json')
        self.reqparse.add_argument("book_evaluation", type=int, location='json')
        self.reqparse.add_argument("interaction_evaluation", type=int, location='json')
        self.reqparse.add_argument("comments", type=str, location='json')

        super(FeedbackApi, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        feedback = Feedback(**args)
        try:
            book_return = Book_return.query.get_or_404(feedback.transaction_id)
            loan = Book_loan.query.get_or_404(book_return.book_loan_id)
            book = Book.query.get_or_404(loan.book_id)
            # Feedback from user to owner
            if g.user.id == loan.user_id:
                user = g.user
                db.session.add(feedback)
                feedback.user = "user"
            # Feedback from owner to user
            elif book.is_organization: # Must be user-to-user
                    return { 'message' : 'Organizations cannot be evaluated' }, log__(400,g.user)
            elif book.user_id == g.user.id:
                user = g.user
                db.session.add(feedback)
                feedback.user = "owner"
            else:
                return {'message': 'You are not authorized to access this area'}, log__(401,g.user)
            # Update user evaluation
            if user.evaluation == 0:
                user.evaluation = feedback.user_evaluation
            else:
                user.evaluation = ceil((user.evaluation +
                                   feedback.user_evaluation) / 2)
            # Gamefication
            if feedback.book_evaluation == 5:
                user.points_update(8)
                feedback.scored += 8
            if feedback.time_evaluation == 5:
                user.points_update(8)
                feedback.scored += 8

            db.session.commit()
            return { 'data': feedback.serialize }, log__(200,g.user)
        except Exception as error:
            print("ERROR: " + str(error))
            return { 'message': 'Unexpected Error' }, log__(500,g.user)


class ModifyFeedbackApi(Resource):
    decorators = [auth.login_required]

    def get(self, id):
        feedback = Feedback.query.get_or_404(id)
        return { 'data': feedback.serialize }, log__(200,g.user)

    def delete(self, id):
        feedback = Feedback.query.get_or_404(id)
        # Gamefication
        if feedback.user == "owner":
            book_return = Book_return.query.get_or_404(feedback.transaction_id)
            loan = Book_loan.query.get_or_404(book_return.book_loan_id)
            book = Book.query.get_or_404(loan.book_id)
            user = User.query.get_or_404(book.user_id)
            user.points_update(-feedback.scored)

        db.session.delete(feedback)
        db.session.commit()
        return {}, log__(204,g.user)


class Ranking(Resource):

    def get(self):
        users = [u.serialize for u in User.query.all()]
        # Sorting first by the points, after by the alfabetic order of the names
        return { 'data' : sorted(users, key=lambda t: (-t['points'], t['name'])) }, log__(200)


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
api.add_resource(Ranking, '/api/v1/ranking', endpoint='ranking')

# if you want to test any resource, try using CURL in the terminal, like:
# $ curl -u USERAME:PASSWORD -H "Content-Type: application/json" -d '{"key": "value", "key": "value"}' -X GET/POST/PUT/DELETE -i http://localhost:5000/RESOURCE_URI
# or try to use a visual tool like Postman
