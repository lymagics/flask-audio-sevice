from flask import current_app, g, jsonify, request, url_for

from . import api
from .authentication import auth
from .decorators import permission_required
from .errors import forbidden
from ...models import Comment, Song, Permission, db


@api.route("/songs/", methods=["GET"])
def get_songs():
    """API songs route handler.
    
    :GET get all songs.
    """
    page = request.args.get("page", 1, type=int)
    pagination = Song.query.paginate(
        page, per_page=current_app.config["SONGS_PER_PAGE"],
        error_out=False
    )
    prev_url = None 
    if pagination.has_prev:
        prev_url = url_for("api.get_songs", page=page-1, _external=True)
    next_url = None 
    if pagination.has_next:
        next_url = url_for("api.get_songs", page=page+1, _external=True)
    songs = pagination.items
    resp = {
        "prev_url": prev_url,
        "songs": [url_for("api.get_song", song_id=song.song_id, _external=True) for song in songs],
        "next_url": next_url
    }
    return jsonify(resp)


@api.route("/songs/<int:song_id>", methods=["GET"])
def get_song(song_id):
    """API song route handler.
    
    :param song_id: unqiue song identifier.
    :GET return song info.
    """
    song = Song.query.get_or_404(song_id)
    return jsonify(song.to_json())


@api.route("/songs/<int:song_id>/comments", methods=["GET"])
def get_song_comments(song_id):
    """API song comments route handler.
    
    :param song_id: unique song identifier.
    :GET return all song comments.
    """
    song = Song.query.get_or_404(song_id)
    page = request.args.get("page", 1, type=int)
    pagination = song.comments.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config["COMMENTS_PER_REQUEST"],
        error_out=False
    )
    prev_url = None 
    if pagination.has_prev:
        prev_url = url_for("api.get_song_comments", song_id=song.song_id, page=page-1, _external=True)
    next_url = None 
    if pagination.has_next:
        next_url = url_for("api.get_song_comments", song_id=song.song_id, page=page+1, _external=True)
    comments = pagination.items 
    resp = {
        "prev_url": prev_url,
        "comments": [url_for("api.get_comment", comment_id=comment.comment_id, _external=True) for comment in comments],
        "next_url": next_url
    }
    return jsonify(resp)


@api.route("/songs/<int:song_id>/comments/", methods=["POST"])
@auth.login_required
@permission_required(Permission.COMMENT)
def new_song_comment(song_id):
    """API new comment route handler.
    
    :param song_id: unique song identifier.
    :GET add new comment for song.
    """
    song = Song.query.get_or_404(song_id)
    comment = Comment.from_json(request.json)
    comment.author = g.current_user
    comment.song = song 
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201, \
        {"comment_location": url_for("api.get_comment", comment_id=comment.comment_id, _external=True)}


@api.route("/songs/<int:song_id>", methods=["PUT"])
@auth.login_required
@permission_required(Permission.PUBLISH)
def update_song(song_id):
    """Update song route handler.
    
    :param song_id: unique song identifier.
    :PUT update song name and lyrics.
    """
    song = Song.query.get_or_404(song_id)
    if song.author != g.current_user:
        return forbidden("Can't update someone else song.")
    song.update_json(request.json)
    return jsonify(song.to_json()), 200, \
        {"song_location": url_for("api.get_song", song_id=song.song_id, _external=True)}
