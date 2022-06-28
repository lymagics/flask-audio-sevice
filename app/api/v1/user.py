from flask import abort, current_app, g, jsonify, request, url_for

from . import api 
from .authentication import auth
from .decorators import permission_required
from .errors import forbidden
from ...models import User, Song, Permission


@api.route("/users/", methods=["GET"])
def get_users():
    """API users route handler.
    
    :GET get all application users.
    """
    page = request.args.get("page", 1, type=int)
    pagination = User.query.paginate(
        page, per_page=current_app.config["USERS_PER_REQUEST"],
        error_out=False
    )
    prev_url = None 
    if pagination.has_prev:
        prev_url = url_for("api.get_users", page=page-1, _extrnal=True)
    next_url = None 
    if pagination.has_next:
        next_url = url_for("api.get_users", page=page+1, _external=True)
    users = pagination.items
    resp = {
        "prev_url": prev_url,
        "users": [url_for("api.get_user", username=user.username, _external=True) for user in users],
        "next_url": next_url
    }
    return jsonify(resp)


@api.route("/users/<username>", methods=["GET"])
def get_user(username):
    """API user route handler.
    
    :param username: user nick name.
    :GET return user info.
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return jsonify(user.to_json())


@api.route("/users/<username>", methods=["PUT"])
@auth.login_required
def update_user(username):
    """Update user route handler.
    
    :param username: user nick name.
    :PUT update info about user.
    """
    user = User.query.filter_by(username=username).first()
    if g.current_user != user and not g.current_user.can(Permission.ADMIN):
        return forbidden("Can't update someone else account.")
    user.update_json(request.json)
    return jsonify(user.to_json()), 200, \
        {"user_location": url_for("api.get_user", username=user.username, _external=True)}


@api.route("/users/<username>/songs/", methods=["GET"])
def get_user_songs(username):
    """API user songs route handler.
    
    :param username: user nick name.
    :GET return user songs.
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get("page", 1, type=int)
    pagination = user.songs.order_by(Song.timestamp.desc()).paginate(
        page, per_page=current_app.config["SONGS_PER_PAGE"],
        error_out=False
    )
    prev_url = None
    if pagination.has_prev:
        prev_url = url_for("api.get_user_songs", username=username, page=page-1, _external=True)
    next_url = None 
    if pagination.has_next:
        next_url = url_for("api.get_user_songs", username=username, page=page+1, _external=True)
    songs = pagination.items
    resp = {
        "prev_url": prev_url,
        "songs": [url_for("api.get_song", song_id=song.song_id, _external=True) for song in songs],
        "next_url": next_url
    }
    return jsonify(resp)  
