from flask import request, jsonify 

from app.exceptions import ValidationError
from . import api


def forbidden(message):
    """API forbidden error.
    
    :return json with message and 403 code error.
    """
    resp = jsonify({"error": "forbidden", "message": message})
    resp.status_code = 403
    return resp 


def bad_request(message):
    """API bad request error.
    
    :return json with message and 400 code error.
    """
    resp = jsonify({"error": "bad request", "message": message})
    resp.status_code = 400
    return resp


def unauthorized(message):
    """API unauthorized error.
    
    :return json with message and 401 code error.
    """
    resp = jsonify({"error": "unauthorized", "message": message})
    resp.status_code = 401
    return resp


@api.errorhandler(ValidationError)
def validation_error(e):
    """API validation error."""
    return bad_request(e.args[0])
