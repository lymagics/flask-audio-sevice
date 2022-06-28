import os

from flask import abort, current_app, flash, g, make_response, redirect, request, render_template, url_for
from flask_babel import gettext
from flask_login import current_user, login_required

from . import main
from .forms import CommentForm, EditProfileAdminForm, EditProfileForm, UploadSongForm, UpdateSongForm
from .. import db
from ..decorators import admin_required, permission_required
from ..models import Comment, Permission, User, Role, Song
from ..storage import upload_to_storage, delete_from_storage


@main.route("/")
def index():
    show_followed = False 
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get("show_followed", ""))
    if show_followed:
        query = current_user.followed_songs
    else:
        query = Song.query
    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(Song.timestamp.desc()).paginate(
        page, per_page=current_app.config["SONGS_PER_PAGE"],
        error_out=False
    )
    songs = pagination.items
    processed_songs = []
    for i in range(0, 9, 3):
        processed_songs.append(songs[i:i+3])
    return render_template("index.html", songs=processed_songs, pagination=pagination, 
                           show_followed=show_followed)


@main.route("/user/<username>")
def user(username):
    """User profile route handler.
    
    :GET landing page: "main/user".
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get("page", 1, type=int)
    pagination = user.songs.order_by(Song.timestamp.desc()).paginate(
        page, per_page=current_app.config["SONGS_PER_USER_PAGE"],
        error_out=False
    )
    songs = pagination.items
    return render_template("user.html", user=user, songs=[songs], pagination=pagination)


@main.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Edit profile route handler.
    
    :GET landing page: "main/edit_profile".
    :POST update user profile and redirect to this profile.
    """
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash(gettext("Your profile successfully updated."))
        return redirect(url_for("main.user", username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location 
    form.about_me.data = current_user.about_me 
    return render_template("edit_profile.html", form=form)


@main.route("/edit-profile/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_profile_admin(user_id):
    """Edit profile as admin route handler.
    
    :GET landing page: "main/edit_profile_admin".
    :POST save user info edited by admin and redirect to user profile.
    """
    user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user)
    if form.validate_on_submit():
        user.username = form.username.data 
        user.email = form.email.data 
        user.about_me = form.about_me.data 
        user.confirmed = form.confirmed.data 
        user.location = form.location.data 
        user.name = form.name.data 
        user.role = Role.query.get(form.role.data)
        db.session.add(user)
        db.session.commit()
        flash(gettext("User profile updated."))
        return redirect(url_for("main.user", username=user.username))
    form.username.data = user.username   
    form.email.data = user.email  
    form.about_me.data  = user.about_me
    form.confirmed.data  = user.confirmed 
    form.location.data = user.location  
    form.name.data = user.name  
    form.role.data = user.role_id
    return render_template("edit_profile_admin.html", form=form)


@main.route("/upload-song", methods=["GET", "POST"])
@login_required
@permission_required(Permission.PUBLISH)
def upload_song():
    """Upload song route handler.
    
    :GET landing page: "main/upload_song".
    :POST upload song to the storage and redirect to "main/index".
    """
    form = UploadSongForm()
    if form.validate_on_submit():
        f = form.song.data
        
        song = Song(name=form.name.data, author=current_user, lyrics=form.lyrics.data)
        db.session.add(song)
        db.session.commit()
        
        f.save(str(song.song_id))
        if f.filename.endswith(".mp3"):
            upload_to_storage(str(song.song_id), content_type="audio/mpeg")
        flash(gettext("Your song has been uploaded!"))
        return redirect(url_for("main.index"))
    return render_template("upload_song.html", form=form)


@main.route("/song/<int:song_id>", methods=["GET", "POST"])
def song(song_id):
    """Song page route handler.
    
    :GET landing page: "main/song/<song_id>"
    """
    song = Song.query.get_or_404(song_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, author=current_user, 
                          song=song)
        db.session.add(comment)
        db.session.commit()
        flash(gettext("Your comment successfully added."))
        return redirect(url_for("main.song", song_id=song.song_id, page=-1))
    page = request.args.get("page", 1, type=int)
    pagination = song.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config["COMMENTS_PER_PAGE"],
        error_out=False
    )
    comments = pagination.items
    return render_template("song.html", song=song, comments=comments,
                           pagination=pagination, form=form)


@main.route("/update-song/<int:song_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.PUBLISH)
def update_song(song_id):
    """Update song route handler.
    
    :GET landing page: "main/update-song".
    :POST update user song and redirect to "main/song/<song_id>"
    """
    song = Song.query.get_or_404(song_id)
    if song.author != current_user and not current_user.is_administrator():
        abort(403)
    form = UpdateSongForm()
    if form.validate_on_submit():
        song.name = form.name.data 
        song.lyrics = form.lyrics.data 
        db.session.add(song)
        db.session.commit()
        flash(gettext("Song has been updated."))
        return redirect(url_for("main.song", song_id=song.song_id))
    form.name.data = song.name
    form.lyrics.data = song.lyrics
    return render_template("update_song.html", form=form)


@main.route("/delete-song/<int:song_id>")
@login_required
@permission_required(Permission.PUBLISH)
def delete_song(song_id):
    """Delete song route handler.
    
    :GET delete song from storage and redirect "main/index".
    """
    song = Song.query.get_or_404(song_id)
    if current_user != song.author and not current_user.can(Permission.ADMIN):
        abort(403)
    delete_from_storage(str(song.song_id))
    db.session.delete(song)
    db.session.commit()
    flash(gettext("Song has been deleted."))
    return redirect(url_for("main.index"))


@main.route("/moderate-comments")
@login_required
@permission_required(Permission.MODERATE)
def moderate_comments():
    """Comments moderation route handler.
    
    :GET landing page: "main/moderate_comments".
    """
    page = request.args.get("page", 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config["COMMENTS_PER_MODERATE_PAGE"],
        error_out=False
    )
    comments = pagination.items
    return render_template("moderate_comments.html", comments=comments, 
                           pagination=pagination)


@main.route("/disable-comment/<int:comment_id>")
@login_required
@permission_required(Permission.MODERATE)
def disable_comment(comment_id):
    """Disable comment route handler.
    
    :GET disable comment.
    """
    comment = Comment.query.get_or_404(comment_id)
    comment.disabled = True 
    db.session.add(comment)
    db.session.commit()
    flash(gettext("Comment has been disabled."))
    return redirect(url_for("main.moderate_comments"))


@main.route("/enable-comment/<int:comment_id>")
@login_required
@permission_required(Permission.MODERATE)
def enable_comment(comment_id):
    """Enable comment route handler.
    
    :GET enable comment.
    """
    comment = Comment.query.get_or_404(comment_id)
    comment.disabled = False 
    db.session.add(comment)
    db.session.commit()
    flash(gettext("Comment has been enabled."))
    return redirect(url_for("main.moderate_comments"))


@main.route("/follow/<username>")
@login_required 
@permission_required(Permission.FOLLOW)
def follow(username):
    """Follow user route handler.
    
    :GET follow user and redirect to "main/user/<username>.
    :param username: user to follow nickname.
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    if current_user == user:
        return redirect(url_for("main.user", username=user.username))
    if current_user.is_following(user):
        flash(gettext("You already follow %(username)s.", username=user.username))
        return redirect(url_for("main.user", username=user.username))
    current_user.follow(user)
    db.session.commit()
    flash(gettext("You now following %(username)s.", username=user.username))
    return redirect(url_for("main.user", username=user.username))


@main.route("/unfollow/<username>")
@login_required 
@permission_required(Permission.FOLLOW)
def unfollow(username):
    """Unfollow user route handler.
    
    :GET unfollow user and redirect to "main/user/<username>".
    :param username: user to unfollow nickname.
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    if current_user == user:
        return redirect(url_for("main.user", username=user.username))
    if not current_user.is_following(user):
        flash(gettext("You don't follow %(username)s.", username=user.username))
        return redirect(url_for("main.user", username=user.username))
    current_user.unfollow(user)
    db.session.commit()
    flash(gettext("You aren't following %(username)s anymore.", username=user.username))
    return redirect(url_for("main.user", username=user.username))


@main.route("/show-followed")
@login_required 
def show_followed():
    """Set cookie to show songs of followed users."""
    resp = make_response(redirect(url_for("main.index")))
    resp.set_cookie("show_followed", "1", max_age=30*24*60*90)
    return resp


@main.route("/show-all")
@login_required 
def show_all():
    """Set cookie to show songs of all users."""
    resp = make_response(redirect(url_for("main.index")))
    resp.set_cookie("show_followed", "", max_age=30*24*60*90)
    return resp


@main.route("/followers/<username>")
def followers(username):
    """User followers route handler.
    
    :GET landing page: "main/followers/<username>".
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get("page", 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config["FOLLOW_PER_PAGE"],
        error_out=False
    )
    follows = [{"user": item.follower, "timestamp": item.timestamp} for item in pagination.items]
    return render_template("follow.html", pagination=pagination,
                           follows=follows, title=gettext("Followers of"), user=user, endpoint="main.followers")


@main.route("/followed-by/<username>")
def followed_by(username):
    """User followed by route handler.
    
    :GET landing page: "main/followed-by/<username>".
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get("page", 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config["FOLLOW_PER_PAGE"],
        error_out=False
    )
    follows = [{"user": item.followed, "timestamp": item.timestamp} for item in pagination.items]
    return render_template("follow.html", pagination=pagination, user=user,
                           follows=follows, endpoint="main.followed_by", title=gettext("Followed by"))


@main.route("/like/<int:song_id>")
@login_required
def like(song_id):
    """Like song route handler.
    
    :GET like song and redirect to "main/song/<song_id>"
    """
    song = Song.query.get_or_404(song_id)
    if song is None:
        abort(404)
    if song.is_liked_by(current_user):
        return redirect(url_for("main.song", song_id=song.song_id))
    song.like(current_user)
    db.session.commit()
    flash(gettext("You liked %(name)s.", name=song.name))
    return redirect(request.referrer or url_for("main.song", song_id=song.song_id))


@main.route("/unlike/<int:song_id>")
@login_required 
def unlike(song_id):
    """Unlike song route handler.
    
    :GET unlike song and redirect to "main/song/<song_id>"
    """
    song = Song.query.get_or_404(song_id)
    if song is None:
        abort(404)
    if not song.is_liked_by(current_user):
        return redirect(url_for("main.song", song_id=song.song_id))
    song.unlike(current_user)
    db.session.commit()
    flash(gettext("You unliked %(name)s.", name=song.name))
    return redirect(request.referrer or url_for("main.song", song_id=song.song_id))


@main.route("/search")
def search():
    """Search route handler.
    
    :GET show results of search.
    """
    page = request.args.get("page", 1, type=int)
    songs, total = Song.search(g.search_form.q.data, page,
                               current_app.config["SEARCH_PER_PAGE"])
    next_url = url_for("main.search", q=g.search_form.q.data, page=page+1) \
        if total > page * current_app.config["SEARCH_PER_PAGE"] else None
    prev_url = url_for("main.search", q=g.search_form.q.data, page=page-1) \
        if page > 1 else None
    processed_songs = []
    for i in range(0, 6, 3):
        processed_songs.append(songs[i:i+3])
    return render_template("search.html", songs=processed_songs, next_url=next_url,
                           prev_url=prev_url, ask=g.search_form.q.data)


@main.route("/language")
def set_language():
    """Set language for user.
    
    :GET set user language and redirect to "main/index".
    """
    lang = request.args.get("lang", "en", type=str)
    if lang not in current_app.config["LANGUAGES"].keys():
        lang = "en"
    resp = make_response(redirect(request.referrer)) if request.referrer \
        else make_response(redirect(url_for("main.index")))        
    resp.set_cookie("language", lang, max_age=30*24*60*90)
    return resp
