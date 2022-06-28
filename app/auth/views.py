from flask import flash, g, redirect, render_template, request, url_for
from flask_babel import gettext, get_locale
from flask_login import current_user, login_user, login_required, logout_user

from . import auth
from .forms import ChangeEmailForm, ChangePasswordForm, LoginForm, RegistrationForm,  \
    RequsetResetPasswordForm, ResetPasswordForm, SearchForm
from .. import db
from ..email import send_mail
from ..models import User


@auth.before_app_request
def before_request():
    """Before request handler.
    
    If user don't confirm his account redirect to "auth/unconfirmed".
    """
    g.search_form = SearchForm()
    g.locale = str(get_locale())
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and \
             request.blueprint != "auth" and \
                request.endpoint != "static" and \
                    request.url != url_for("main.set_language", lang=request.args.get("lang", ""), _external=True):
                    return redirect(url_for("auth.unconfirmed"))


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Login page route handler.
    
    :GET landing page: "auth/login".
    :POST login user to the site. redirect to "index".
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get("next") or url_for("main.index"))
        flash(gettext("Invalid username or password."))
        return redirect(url_for("auth.login"))
    return render_template("auth/login.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    """Logout route handler.
    
    :GET logout user. redirect to index page.
    """
    logout_user()
    flash(gettext("You have been logged out."))
    return redirect(request.referrer or url_for("main.index"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    """Registration route handler.
    
    :GET landing page: "auth/register".
    :POST create user account. redirect to "auth/login".
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_mail(user.email, "Confirm your account", "auth/mail/confirm", user=user, token=token)
        flash(gettext("An confirmation email with instructions has been sent you."))
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth.route("/unconfirmed")
@login_required
def unconfirmed():
    """Unconfirmed route handler.
    
    :GET landing page: "auth/unconfirmed"
    """
    return render_template("auth/unconfirmed.html")


@auth.route("/confirm/<token>")
@login_required 
def confirm(token):
    """Confirm route handler.
    
    :GET confirm account and redirect to "main/index".
    """
    if current_user.confirmed:
        return redirect(url_for("main.index"))
    if current_user.validate_confirmation_token(token):
        db.session.commit()
        flash(gettext("Your account successfully confirmed! Thanks!"))
    return redirect(url_for("main.index"))


@auth.route("/confirm")
@login_required
def send_confirm():
    """Resend confirmation token.
    
    :GET send user new confirmation token and redirect to index page.
    """
    if current_user.confirmed:
        return redirect(url_for("main.index"))
    token = current_user.generate_confirmation_token()
    send_mail(current_user.email, "Confirm your account", "auth/mail/confirm", user=current_user, token=token)
    flash(gettext("An confirmation email with instructions has been sent you."))
    return redirect(url_for("main.index"))


@auth.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change password route handler.
    
    :GET landing page: "auth/change_password".
    :POST change user password and redirect to "main/index".
    """
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data 
            db.session.add(current_user)
            db.session.commit()
            flash(gettext("You password has been changed.")) 
            return redirect(url_for("main.index"))
        else:
            flash(gettext("Invalid password."))
            return redirect(url_for("auth.change_password"))
    return render_template("auth/change_password.html", form=form)


@auth.route("/change-email", methods=["GET", "POST"])
@login_required
def change_email():
    """Change email route handler.
    
    :GET landing page: "auth/change_email".
    :POST send user email change token and redirect to "main/index".
    """
    form = ChangeEmailForm()
    if form.validate_on_submit():
        token = current_user.generate_email_change_token(form.email.data)
        send_mail(form.email.data, "Email change confirmation", 
                  "auth/mail/change_email", token=token, user=current_user)
        flash(gettext("An email with instructions has been sent to you."))
        return redirect(url_for("main.index"))
    return render_template("auth/change_email.html", form=form)


@auth.route("/change_email/<token>")
@login_required
def confirm_change_email(token):
    """Change email route handler.
    
    :GET change user email and redirect to "main/index".
    """
    if current_user.validate_email_change_token(token):
        db.session.commit()
        flash(gettext("You email successfully changed."))
    else:
        flash(gettext("Invalid token."))
    return redirect(url_for("main.index"))


@auth.route("/reset", methods=["GET", "POST"])
def reset():
    """Request password reset route handler.
    
    :GET landing page: "auth/reset".
    :POST send user reset token and redirect to "auth.login".
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RequsetResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_password_reset_token()
            send_mail(form.email.data, "Reset password",
                  "auth/mail/reset", token=token, user=user)
            flash(gettext("An email with instructions has been sent to you."))
            return redirect(url_for("auth.login"))
        else:
            flash(gettext("Account with this email doesn't exist."))
            return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", form=form)
            
            
@auth.route("/reset/<token>", methods=["GET", "POST"])
def confirm_reset(token):
    """Password reset token route handler.
    
    :GET landing page: "auth/confirm_reset".
    :POST reset user password and redirect to "auth.login".
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash(gettext("Password has been changed."))
            return redirect(url_for("auth.login"))
        flash(gettext("Invalid token."))
        return redirect(url_for("auth.login"))
    return render_template("auth/confirm_reset.html", form=form)
            