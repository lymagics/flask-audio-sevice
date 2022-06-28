from flask import Blueprint

main = Blueprint("main", __name__)
from . import views, errors
from ..models import Permission


@main.app_context_processor
def inject_permissions():
    """Inject permissions to make it available in jinja2 templates without additional send."""
    return dict(Permission=Permission)
