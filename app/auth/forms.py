from flask import request
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, ValidationError

from ..models import User


class LoginForm(FlaskForm):
    """User login form.
    
    :param username: user nickname field.
    :param password: user password field.
    :param submit: submit button.
    """
    
    username = StringField(_l("Username"), validators=[DataRequired(), Length(1, 64)])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    remember_me = BooleanField(_l("Keep me logged in."))
    submit = SubmitField(_l("Login"))


class RegistrationForm(FlaskForm):
    """User registration form.
    
    :param email: user email field.
    :param username: user nickname field.
    :param password: user password field.
    :param password2: user password repeat field.
    :param submit: submit button.
    """
    
    email = StringField(_l("Email"), validators=[DataRequired(), Email(), 
                                             Length(1, 64)])
    username = StringField(_l("Username"), validators=[DataRequired(), Length(1, 64),
                                                   Regexp("^[A-Za-z][A-Za-z0-9._]*$",
                                                          0, _l("Usernames must have only letters, numbers, \
                                                          dots and underscores."))])
    password = PasswordField(_l("Password"), validators=[DataRequired(), EqualTo("password2",
                                                                             _l("Password must match."))])
    password2 = PasswordField(_l("Repeat password"), validators=[DataRequired()])
    submit = SubmitField(_l("Sign Up"))

    def validate_email(self, field):
        """Validate email to prevent duplicates."""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_l("Account with such email already registered."))
        
    def validate_username(self, field):
        """Validate username to prevent duplicates."""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(_l("Username already in use."))


class ChangePasswordForm(FlaskForm):
    """Change password form.
    
    :param old_password: user old password field.
    :param password: user new password field.
    :param password2: user new password confirmation.
    :param submit: submit button.
    """
    
    old_password = PasswordField(_l("Old password"), validators=[DataRequired()])
    password = PasswordField(_l("New Password"), validators=[DataRequired(), EqualTo("password2",
                                                                                 _l("Passwords must match."))])
    password2 = PasswordField(_l("Repeat password"), validators=[DataRequired()])
    submit = SubmitField(_l("Change password"))


class ChangeEmailForm(FlaskForm):
    """Change email form.
    
    :param email: new user email field.
    :param submit: submit button.
    """
    
    email = StringField(_l("New Email"), validators=[DataRequired(), Email(), 
                                                 Length(1, 64)])
    submit = SubmitField(_l("Change Email"))
    
    def validate_email(self, field):
        """Validate email to prevent duplicates."""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_l("Email already in use."))


class RequsetResetPasswordForm(FlaskForm):
    """Request to reset password form.
    
    :param email: user email field.
    :param submit: submit button.
    """
    
    email = StringField(_l("Email"), validators=[DataRequired(), Email(), 
                                             Length(1, 64)])
    submit = SubmitField(_l("Reset password"))
    
    def validate_email(self, field):
        """Validate email to prevent duplicates."""
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError(_l("Account with such email doesn't exist."))


class ResetPasswordForm(FlaskForm):
    """Reset password form.
    
    :param password: new user password field.
    :param password2: new user password confirm field.
    :param submit: submit button.
    """
    
    password = PasswordField(_l("New Password"), validators=[DataRequired(), EqualTo("password2",
                                                                                 _l("Passwords must match."))])
    password2 = PasswordField(_l("Repeat password"), validators=[DataRequired()])
    submit = SubmitField(_l("Reset"))


class SearchForm(FlaskForm):
    """Search form.
    
    :param q: query to search.
    """
    q = StringField(_l("Search"), validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        if "formdata" not in kwargs:
            kwargs["formdata"] = request.args
        if "csrf_enabled" not in kwargs:
            kwargs["csrf_enabled"] = False
        super(SearchForm, self).__init__(*args, **kwargs)
