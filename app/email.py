from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from . import mail 


def async_send_mail(app, msg):
    """Send message asynchronous.
    
    :param app: flask application instance.
    :param msg: message to send.
    """
    with app.app_context():
        mail.send(msg)


def send_mail(to, subject, template, **kwargs):
    """Send email message to client.
    
    :param to: recipient.
    :param subject: message subject.
    :param template: template from templates folder to send.
    :param **kwargs: template keyword arguments. 
    """
    app = current_app._get_current_object()
    msg = Message(subject, sender=app.config["MAIL_SENDER"],
                  recipients=[to])
    msg.body = render_template(f"{template}.txt", **kwargs)
    msg.html = render_template(f"{template}.html", **kwargs)

    thr = Thread(target=async_send_mail, args=[app, msg])
    thr.start()
    return thr
