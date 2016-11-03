from flask import g, jsonify
from flask_restful import Resource, reqparse
from app import app, db, auth, api
from app.models.tables import User, Organization
from app.models.decorators import is_user, is_manager


@auth.verify_password
def verify_password(email_or_token, password):
    """
    This function verifies if the user has the correct credentials.
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
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


class UsersApi(Resource):
    def __init__(self):
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
        users = User.query.all()
        return {'data': [u.serialize for u in users]}, 200

    def post(self):
        args = self.reqparse.parse_args()
        user = User(**args)
        user.hash_password(args['password'])
        db.session.add(user)
        try:
            db.session.commit()
            return {'data': user.serialize}, 201
        except Exception as error:
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

    @is_user
    def put(self, id):
        user = User.query.get_or_404(id)
        args = self.reqparse.parse_args()
        for key, value in args.items():
            if key == 'password' and value is not None:
                user.hash_password(value)
            elif value is not None:
                setattr(user, key, value)
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

api.add_resource(UsersApi, '/api/v1/users', endpoint='users')
api.add_resource(ModifyUsersApi, '/api/v1/users/<int:id>',
                 endpoint='modify_users')
api.add_resource(OrganizationsApi, '/api/v1/organizations',
                 endpoint='organizations')
api.add_resource(ModifyOrganizationsApi, '/api/v1/organizations/<int:id>',
                 endpoint='modify_organizations')
