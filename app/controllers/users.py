from flask import g, jsonify
from app import app, db, auth
from app.models.tables import User


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
