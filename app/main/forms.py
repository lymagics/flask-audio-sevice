from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm 
from flask_wtf.file import FileRequired
from wtforms import BooleanField, FileField, StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp, ValidationError

from ..models import User, Role


class EditProfileForm(FlaskForm):
    """Edit profile form.
    
    :param name: user real name field.
    :param about_me: information about user.
    :param location: user location.
    :param submit: submit button.
    """
    
    name = StringField(_l("Real Name"), validators=[Length(0, 64)])
    about_me = TextAreaField(_l("About me"))
    location = StringField(_l("Location"), validators=[Length(0, 64)])
    submit = SubmitField(_l("Save"))


class EditProfileAdminForm(FlaskForm):
    """Edit profile as admin form.
    
    :param username: user nickname field.
    :param email: user email field.
    :param about_me: information about user field.
    :param confirmed: user account confirmation status field.
    :param location: user location field.
    :param name: user real name field.
    :param role: user role with permissions field.
    :param submit: submit button.
    """
    
    username = StringField(_l("Username"), validators=[DataRequired(), Length(1, 64),
                                                   Regexp("^[A-Za-z][A-Za-z0-9._]*$",
                                                          0, _l("Usernames must have only \
                                                              letters, numbers, dots and underscores."))])
    email = StringField(_l("Email"), validators=[DataRequired(), Length(1, 64), Email()])
    about_me = TextAreaField(_l("About me"))
    confirmed = BooleanField(_l("Confirmed"))
    location = StringField(_l("Location"), validators=[Length(0, 64)])
    name = StringField(_l("Real Name"), validators=[Length(0, 64)])
    role = SelectField(_l("Role"), coerce=int)
    submit = SubmitField(_l("Edit"))

    def __init__(self, user, *args, **kwargs):
        """Constructor for form to inster roles in select field."""
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.role_id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        """Validate email to prevent duplicates."""
        if self.user.email != field.data and User.query.filter_by(email=field.data).first():
            raise ValidationError(_l("Account with this email already exists."))
        
    def validate_username(self, field):
        """Validate username to prevent duplicates."""
        if self.user.username != field.data and User.query.filter_by(username=field.data).first():
            raise ValidationError(_l("Username already in use."))


class UploadSongForm(FlaskForm):
    """Upload song form.
    
    :param name: song name field.
    :param song: song file.
    :param lyrics: song lyrics field.
    :param submit: submit button.
    """
    name = StringField(_l("Song name"), validators=[DataRequired(), Length(1, 64)])
    song = FileField(_l("Song"), validators=[FileRequired()])
    lyrics = TextAreaField(_l("Lyrics"))
    submit = SubmitField(_l("Upload"))
    
    def validate_song(self, field):
        """Validate song format."""
        if not field.data.filename.endswith(".mp3"):
            raise ValidationError(_l("Uncnown file format."))
  
  
class UpdateSongForm(FlaskForm):
    """Update song form.
    
    :param name: song name field.
    :param lyrics: song lyrics field.
    :param submit: submit button.
    """
    name = StringField(_l("Song name"), validators=[DataRequired()])
    lyrics = TextAreaField(_l("Lyrics"))
    submit = SubmitField(_l("Update"))
    
    
class CommentForm(FlaskForm):
    """Comment form.
    
    :param body: comment body field.
    :param submit: submit button.
    """
    body = TextAreaField(_l("What do you think on this song?"), validators=[DataRequired()])
    submit = SubmitField(_l("Comment"))
    