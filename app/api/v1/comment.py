from flask import current_app, url_for, jsonify, request

from . import api 
from ...models import Comment


@api.route("/comments/", methods=["GET"])
def get_comments():
    """API comments route handler.
    
    :GET get all comments.
    """
    page = request.args.get("page", 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config["COMMENTS_PER_REQUEST"],
        error_out=False
    )
    prev_url = None
    if pagination.has_prev:
        prev_url = url_for("api.get_comments", page=page-1, _external=True)
    next_url = None 
    if pagination.has_next:
        next_url = url_for("api.get_comments", page=page+1, _extrnal=True)
    comments = pagination.items 
    resp = {
        "prev_url": prev_url,
        "comments": [url_for("api.get_comment", comment_id=comment.comment_id, _external=True) for comment in comments],
        "next_url": next_url
    }
    return jsonify(resp)


@api.route("/comments/<int:comment_id>", methods=["GET"])
def get_comment(comment_id):
    """API comment route handler.
    
    :param comment_id: unique comment identifier.
    :GET get comment.
    """
    comment = Comment.query.get_or_404(comment_id)
    return jsonify(comment.to_json())
