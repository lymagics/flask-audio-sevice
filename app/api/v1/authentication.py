from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth

from . import api
from .errors import unauthorized
from ...models import AnonymousUser, User


auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username_or_token, password):
    """API credentials verification.
    
    :param username_or_token: user nick name or auth token.
    :param password: user password.
    """
    if username_or_token == "":
        print("Here")
        g.current_user = AnonymousUser()
        return True 
    if password == "":
        g.current_user = User.validate_auth_token(username_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(username=username_or_token).first()
    if user is None:
        return False 
    g.current_user = user 
    g.token_used = False 
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    """API auth error."""
    return unauthorized("Invalid credentials.")


@api.before_request
@auth.login_required
def before_request():
    """API validaion for confirmed user."""
    if not g.current_user.is_anonymous \
        and not g.current_user.confirmed:
            unauthorized("Unconfirmed user.")


@api.route("/tokens/", methods=["POST"])
def get_token():
    """Get API authentication token."""
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized("Invalid credentials.")
    return jsonify({"token": g.current_user.generate_auth_token(), "expiration": 3600})
