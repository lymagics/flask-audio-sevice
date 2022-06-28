from flask import current_app, Flask, request
from flask_babel import Babel, lazy_gettext as _l
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from config import config
from .search import init_search


babel = Babel()
bootstrap = Bootstrap()
db = SQLAlchemy()
mail = Mail()
moment = Moment()

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "auth.login"
login_manager.login_message = _l("You have to login to access this page.")


def create_app(config_name: str) -> Flask:
    """Flask application instance factory.
    
    :param config_name: the name of configuration type.
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    app.elasticsearch = init_search(config_name)
    
    babel.init_app(app)
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    
    from .api.v1 import api as apiv1_bluerint
    app.register_blueprint(apiv1_bluerint, url_prefix="/api/v1")
    
    return app 


@babel.localeselector
def get_locale():
    """Get local language for flask babel."""
    language = request.cookies.get("language", None)
    if language is not None:
        return language
    return request.accept_languages.best_match(current_app.config["LANGUAGES"].keys())
