from datetime import datetime, timezone, timedelta
from hashlib import md5
from typing import NamedTuple

import jwt
from flask import current_app, url_for
from flask_login import AnonymousUserMixin, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager
from .exceptions import ValidationError
from .search import add_to_index, remove_from_index, query_index
from .storage import get_public_url


class PermissionTuple(NamedTuple):
    """Named tuple to represent full permissions with flag are they default.
    
    :param permissions: complited permission integer.
    :param default: are this permissions default.
    """
    permissions: int
    default: bool


class Permission:
    """Class to represent permissions in hex code.
    
    :param FOLLOW: permission to follow other users.
    :param PUBLISH: permission to publish content.
    :param COMMENT: permission to make comments.
    :param MODERATE: permission to moderate site.
    :param ADMIN: permission to administrate site.
    """
    FOLLOW = 0x1
    PUBLISH = 0x2
    COMMENT = 0x4
    MODERATE = 0x8
    ADMIN = 0x80


class Role(db.Model):
    """SQLAlchemy model to represent roles table.
    
    :param role_id: unique role identifier.
    :param name: unique role name.
    :param permissions: permissions assigned to role.
    :param default: specify if role is default.
    :param users: users attached to role.S
    """
    __tablename__ = "roles"
    
    role_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    permissions = db.Column(db.Integer, nullable=False)
    default = db.Column(db.Boolean, default=False, index=True)
    
    users = db.relationship("User", backref="role", lazy="dynamic")
    
    @staticmethod
    def insert_roles():
        """Insert roles to database."""
        roles = {
            "User": PermissionTuple(Permission.FOLLOW|
                                    Permission.PUBLISH|
                                    Permission.COMMENT,
                                    True),
            "Moderator": PermissionTuple(Permission.FOLLOW|
                                         Permission.PUBLISH|
                                         Permission.COMMENT|
                                         Permission.MODERATE,
                                         False),
            "Administrator": PermissionTuple(0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r].permissions
            role.default = roles[r].default
            db.session.add(role)
        db.session.commit()
    
    def __repr__(self):
        return f"<Role name={self.name}>"


class SearchableMixin:
    @classmethod
    def search(cls, expression, page, per_page):
        """Search in class.
        
        :param expression: expression to search for.
        :param page: current pagination page.
        :param per_page: amount of per page items.
        """
        ids, total = query_index(cls.__tablename__,
                                 expression, page, per_page)
        if total == 0:
            if cls == Song:
                return cls.query.filter_by(song_id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        if cls == Song:
            return cls.query.filter(cls.song_id.in_(ids)).order_by(db.case(when, value=(cls.song_id))), total
    
    @classmethod 
    def before_commit(cls, session):
        """Register changes before commit.
        
        :param session: sqlalchemy session.
        """
        session._changes = {
            "add": list(session.new),
            "update": list(session.dirty),
            "delete": list(session.deleted)
        }
    
    @classmethod 
    def after_commit(cls, session):
        """Apply changes after commit.
        
        :param session: sqlalchemy session.
        """
        for obj in session._changes["add"]:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        
        for obj in session._changes["update"]:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
                
        for obj in session._changes["delete"]:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
    
    @classmethod
    def reindex(cls):
        """Update index for model."""
        for obj in cls.query:
            add_to_index(obj.__tablename__, obj)


class Comment(db.Model):
    """SQLAlchemy model to represent comments table.
    
    :param comment_id: unique comment identifier.
    :param body: comment body.
    :param timestamp: comment publish date.
    :param disabled: is comment disabled by moderator.
    :param auhtor_id: foreing key to comment author.
    :param song_id: foreign key to comment song page.
    """
    __tablename__ = "comments"
    
    comment_id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    song_id = db.Column(db.Integer, db.ForeignKey("songs.song_id"))
    
    @staticmethod
    def from_json(json_comment):
        """Convert json to Comment object.
        
        :param json_comment: comment in json format.
        """
        body = json_comment.get("body")
        if body is None or body == "":
            raise ValidationError("Comment doesn't have a body.")
        return Comment(body=body)
    
    def to_json(self):
        """Convert comment object to json.
        
        :param url: url for comment.
        :param body: comment body.
        :param timestamp: date comment was published.
        :param author: url for comment author.
        :param song: url for comment song.
        """
        json_comment = {
            "url": url_for("api.get_comment", comment_id=self.comment_id, _external=True),
            "body": self.body,
            "timestamp": self.timestamp,
            "author": url_for("api.get_user", username=self.author.username, _external=True),
            "song": url_for("api.get_song", song_id=self.song.song_id, _external=True)
        }
        return json_comment
    
    def __repr__(self):
        return f"<Comment id={self.comment_id}>"


class Follow(db.Model):
    """SQLAlchemy model to represent follows table.
    
    :param follower_id: foreign key to user who is a follower.
    :param followed_id: foreign key to user who has been followed.
    :param timestamp: data when user followed another user.
    """
    __tablename__ = "follows"
    
    follower_id = db.Column(db.Integer, db.ForeignKey("users.user_id"),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("users.user_id"),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class SongLike(db.Model):
    """SQLAlchemy model to represent songlikes table.
    
    :param like_id: unique like identifier.
    :param song_id: foreign key song identifier.
    :param user_id: foreign key user identifier.
    """
    __tablename__ = "songlikes"
    
    like_id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.song_id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))


class Song(SearchableMixin, db.Model):
    """SQLAlchemy model to represent songs table.
    
    :param song_id: uniquer song identifier.
    :param name: song name.
    :param url: unique song url.
    :param lyrics: song lyrics.
    :param timestamp: song publish date.
    :param author_id: song author identifier.
    """
    __tablename__ = "songs"
    __searchable__ = ["name"]
    
    song_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    url = db.Column(db.String(128))
    lyrics = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    
    comments = db.relationship("Comment", backref="song", cascade="all,delete", lazy="dynamic")
    likes = db.relationship("SongLike", backref="song", cascade="all,delete", lazy="dynamic")
    
    def is_liked_by(self, user):
        """Check if song liked by user.
        
        :param user: application user. 
        """
        l = self.likes.filter_by(user_id=user.user_id).first()
        return l is not None
    
    def like(self, user):
        """Like song.
        
        :param user: user who wants to like a song.
        """
        if not self.is_liked_by(user):
            l = SongLike(song=self, user=user)
            db.session.add(l)
    
    def unlike(self, user):
        """Unlike song.
        
        :param user: user who wants to unlike a song.
        """
        if self.is_liked_by(user):
            l = SongLike.query.filter(SongLike.song_id == self.song_id and SongLike.user_id == user.user_id).first()
            if l:
                db.session.delete(l)
    
    def get_url(self):
        """Getter for url."""
        if self.url is None:
            try:
                self.url = get_public_url(str(self.song_id))
                db.session.add(self)
                db.session.commit()
            except:
                pass
        return self.url
    
    def to_json(self):
        """Convert song object to json.
        
        :param url: url representation of song.
        :param html_url: url to user in source html tag.
        :param name: song name.
        :param tiestamp: time song was published.
        :param published_by: user who has published song.
        :param comment: url for song comments.
        :param comments_count: number of song comments.
        :param likes_count: number of song likes.
        """
        json_song = {
            "url": url_for("api.get_song", song_id=self.song_id, _external=True),
            "html_url": self.url,
            "name": self.name,
            "timestamp": self.timestamp,
            "published_by": url_for("api.get_user", username=self.author.username, _external=True),
            "comments": url_for("api.get_song_comments", song_id=self.song_id, _external=True),
            "comments_count": self.comments.count(),
            "likes_count": self.likes.count()
        }
        return json_song
    
    def update_json(self, json_song):
        """Update song from json.
        
        :param json_song: song data in json format.
        """
        name = json_song.get("name")
        if name is not None and name != "":
            self.name = name 
        lyrics = json_song.get("lyrics")
        if lyrics is not None and lyrics != "":
            self.lyrics = lyrics
        db.session.add(self)
        db.session.commit()
    
    def __getattr__(self, attr):
        if attr == "id":
            return self.song_id 
        raise AttributeError(f"Model song has no attribute {attr}.")
    
    def __repr__(self):
        return f"<Song name={self.name}>"


class User(UserMixin, db.Model):
    """SQLAlchemy model to represent users table.
    
    :param user_id: unique user identifier.
    :param username: unique user nickname.
    :param about_me: information about user.
    :param confirmed: is user account confirmed with email. default - false.
    :param email: unique user email address.
    :param last_seen: date and time since user last visited site.
    :param location: user location.
    :param member_since: date and time since user registered.
    :param name: user real name.
    :param password: user password. can't be readed.
    :param password_hash: user password hash.
    """
    __tablename__ = "users"
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, index=True)
    about_me = db.Column(db.Text)
    avatar_hash = db.Column(db.String(32))
    confirmed = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(64), index=True)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    location = db.Column(db.String(64))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    name = db.Column(db.String(64))
    password = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"))
    
    songs = db.relationship("Song", backref="author", cascade="all,delete", lazy="dynamic")
    comments = db.relationship("Comment", backref="author", cascade="all,delete", lazy="dynamic")
    followed = db.relationship("Follow",
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref("follower", lazy="joined"),
                               lazy="dynamic",
                               cascade="all, delete-orphan")
    followers = db.relationship("Follow",
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref("followed", lazy="joined"),
                                lazy="dynamic",
                                cascade="all, delete-orphan")
    likes = db.relationship("SongLike", backref="user", cascade="all,delete", lazy="dynamic")
    
    def __init__(self, **kwargs):
        """User model constructor.
        Set role to admin if user email is admin email, else - default role.
        """
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config["MAIL_ADMIN"]:
                self.role = Role.query.filter_by(name="Administrator").first()
            else:
                self.role = Role.query.filter_by(default=True).first()
            self.avatar_hash = md5(self.email.encode('utf-8')).hexdigest()
        self.follow(self)
    
    def can(self, permissions):
        """Check if user has specified permissions or not."""
        return self.role is not None \
            and (self.role.permissions & permissions) == permissions
    
    def is_administrator(self):
        """Check if user has admin permissions or not."""
        return self.can(Permission.ADMIN)
    
    def follow(self, user):
        """Follow user.
        
        :param user: user to follow.
        """
        if not self.is_following(user):
            follow = Follow(followed=user, follower=self)
            db.session.add(follow)
     
    @property     
    def followed_songs(self):
        """Get all song with authors followed by user."""
        return Song.query.join(Follow, Follow.followed_id == Song.author_id).filter(Follow.follower_id == self.user_id)
            
    def unfollow(self, user):
        """Unfollow user.
        
        :param user: user to unfollow.
        """
        follow = self.followed.filter_by(followed_id=user.user_id).first()
        if follow:
            db.session.delete(follow)
    
    def is_following(self, user):
        """Check if current_user following user.
        
        :param user: another user.
        """
        f = self.followed.filter_by(followed_id=user.user_id).first()
        return f is not None
    
    def is_followed_by(self, user):
        """Check if current_user is followed by user.
        
        :param user: another user.
        """
        f = self.followers.filter_by(follower_id=user.user_id).first()
        return f is not None
    
    def gravatar(self, size=100, default="identicon", rating="g"):
        """Generate gravatar url for user photoes.
        
        :param size: image size.
        :param default: default image if user doesn't have account on gravatar.
        possible values:
        ["mm", "identicon", "monsterid", "wavatar", "retro", "blank"]
        :param rating: image rating. 
        possible values:
        ["g", "pg", "r", "x"]
        """
        url = "https://secure.gravatar.com/avatar"
        img_hash = self.avatar_hash or md5(self.email.encode('utf-8')).hexdigest()
        return f"{url}/{img_hash}?s={size}&d={default}&r={rating}"
    
    def generate_confirmation_token(self, expiration=3600):
        """Generate confirmation token.
        
        :param expiration: time until token is valid.
        """
        return jwt.encode(
            {
                "confirm": self.user_id,
                "exp": datetime.now(timezone.utc) + \
                    timedelta(seconds=expiration)
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256" 
        )
    
    def generate_email_change_token(self, new_email, expiration=3600):
        """Generate token to change email.
        
        :param new_email: new user email address.
        :param expiration: time until token is valid.
        """
        return jwt.encode(
            {
                "confirm": self.user_id,
                "new_email": new_email,
                "exp": datetime.now(timezone.utc) + \
                    timedelta(seconds=expiration)
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )
    
    def generate_password_reset_token(self, expiration=3600):
        """Generate token to reset password.
        
        :param expiration: time until token is valid.
        """
        return jwt.encode(
            {
                "reset": self.user_id,
                "exp": datetime.now(timezone.utc) + \
                    timedelta(seconds=expiration)
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )
    
    def generate_auth_token(self, expiration=3600):
        """Generate API suth token.
        
        :param expiration: time until token is valid.
        """
        return jwt.encode(
            {
                "user_id": self.user_id,
                "exp": datetime.now(timezone.utc) + \
                    timedelta(seconds=expiration)
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )
    
    def validate_confirmation_token(self, token):
        """Validate confirmation token. 
        
        :param token: confirmation token to confirm account.
        """
        try:
            data = jwt.decode(
                token, 
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
        except:
            return False
        if data.get("confirm") != self.user_id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True
    
    def validate_email_change_token(self, token):
        """Validate email change token.
        
        :param token: confirmation token to confirm email change.
        """
        try:
            data = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
        except:
            return False
        if data.get("confirm") != self.user_id:
            return False
        if not data.get("new_email"):
            return False
        self.email = data.get("new_email")
        db.session.add(self)
        return True
    
    @staticmethod
    def validate_auth_token(token):
        """Validate API auth token.
        
        :param token: confrimation token to confim authentication.
        """
        try:
            data = jwt.decode(
                token, 
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
            print("Here")
        except:
            print("here2")
            return None
        return User.query.get(data.get("user_id"))
    
    @staticmethod
    def reset_password(token, new_password):
        """Reset password with token.
        
        :param token: token to reset password.
        :param new_password: new user password.
        """
        try:
            data = jwt.decode(
                token, 
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
        except:
            return False 
        user = User.query.get(data.get("reset"))
        if user is None:
            return False 
        user.password = new_password 
        db.session.add(user)
        return True
    
    def ping(self):
        """Recalculate user last seen value."""
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
    
    @property 
    def password(self):
        """Getter for user password."""
        raise AttributeError("Can't read user password.")
    
    @password.setter
    def password(self, password):
        """Setter for user password.
        
        :param password: user password.
        """
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        """Verify user password.
        
        :param password: user password.
        """
        return check_password_hash(self.password_hash, password)
    
    def to_json(self):
        """Convert user object to json.
        
        :param url: url for user.
        :param username: user nick name.
        :param member_since: date user joined site.
        :param last_seen: date user visited site last time.
        :param real_name: real user name.
        :param location: place where user lives.
        :param songs: url for user songs.
        "param songs_count: number of user songs.
        """
        json_user = {
            "url": url_for("api.get_user", username=self.username, _external=True),
            "username": self.username,
            "member_since": self.member_since,
            "last_seen": self.last_seen,
            "real_name": self.name,
            "location": self.location,
            "songs": url_for("api.get_user_songs", username=self.username, _external=True),
            "songs_count": self.songs.count()
        }
        return json_user
    
    def update_json(self, json_user):
        """Update user from json.
        
        :param json_user: data about user in json format.
        """
        if json_user.get("name") is not None:
            self.name = json_user.get("name")
        if json_user.get("location") is not None:
            self.location = json_user.get("location")
        if json_user.get("about_me") is not None:
            self.about_me = json_user.get("about_me")
        db.session.add(self)
        db.session.commit()
    
    def __getattr__(self, attr):
        if attr == "id":
            return self.user_id
        raise AttributeError(f"Attribute {attr} doesn't exist.")
    
    def __repr__(self):
        return f"<User name={self.username}>"
 

class AnonymousUser(AnonymousUserMixin):
    """Class to repersent anonymous user."""
    
    def can(self, permissions):
        """Check if anonymous user has specified permissions or not."""
        return False
    
    def is_administrator(self):
        """Check if anonymous user has admin permissions or not."""
        return False


login_manager.anonymous_user = AnonymousUser

db.event.listen(db.session, "before_commit", SearchableMixin.before_commit)
db.event.listen(db.session, "after_commit", SearchableMixin.after_commit)

@login_manager.user_loader
def load_user(user_id):
    """User loader for flask login.
    
    :param user_id: user identifier.
    """
    return User.query.get(int(user_id))
    