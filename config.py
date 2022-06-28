import os

import firebase_admin
from firebase_admin import credentials


def generate_basedir():
    """Generate base directory path."""
    return os.path.abspath(os.path.dirname(__file__))


class Config:
    """Config class."""
    
    # Setting cridentials for firebase storage.
    cred = credentials.Certificate(os.environ.get("FIREBASE_KEY"))
     
    ELASTICSEARCH = os.environ.get("ELASTICSEARCH_URL")
    FIREBASE = firebase_admin.initialize_app(cred, {
        "storageBucket": os.environ.get("FIREBASE_BUCKET")
    })
    MAIL_ADMIN = os.environ.get("MAIL_ADMIN")
    MAIL_SENDER = "Development Team"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or "smtp.googlemail.com"
    MAIL_PORT = os.environ.get("MAIL_PORT") or 587
    MAIL_USE_TLS = True
    SECRET_KEY = os.environ.get("SECTER_KEY") or "password"
    COMMENTS_PER_PAGE = 5
    COMMENTS_PER_MODERATE_PAGE = 10
    COMMENTS_PER_REQUEST = 10
    FOLLOW_PER_PAGE = 10
    SONGS_PER_PAGE = 9
    SONGS_PER_USER_PAGE = 3
    SEARCH_PER_PAGE = 6
    USERS_PER_REQUEST = 10
    LANGUAGES = {
        "en": "EN",
        "ru": "РУС",
        "uk_UA": "УКР"
    }
    
    @staticmethod
    def init_app(app):
        pass
    
    
class DevelopmentConfig(Config):
    """Development config class."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URL") or \
        "sqlite:///" + os.path.join(generate_basedir(), "dev-database.sqlite")


class TestingConfig(Config):
    """Testing config class."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL") or \
        "sqlite:///" + os.path.join(generate_basedir(), "test-database.sqlite")


class ProductionConfig(Config):
    """Production config class."""
    
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "").replace('postgres://', 'postgresql://') or \
        "sqlite:///" + os.path.join(generate_basedir(), "prod-database.sqlite")


# Config factory.
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    
    "default": DevelopmentConfig
}
