import os

import click
from flask import g
from flask_migrate import Migrate

from app import create_app, db
from app.models import User, Role, Comment, Follow, Song, SongLike
from app.search import create_index


app = create_app(os.environ.get("FLASK_CONFIG") or "default")
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    """Make application variables available in python shell."""
    return dict(db=db, Comment=Comment, Follow=Follow, User=User, Role=Role, Song=Song, SongLike=SongLike)


@app.context_processor
def inject_conf_var():
    return dict(
        AVAILABLE_LANGUAGES=app.config["LANGUAGES"],
        CURRENT_LANGUAGE=app.config["LANGUAGES"][str(g.locale)]
    )


@app.cli.command()
@click.argument("test_names", nargs=-1)
def test(test_names):
    """Run tests with shell.
    
    :"flask test" - to run all tests.
    :"flask test test.*test_name" - to run test with test_name explicitly.
    """
    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover("tests")
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.cli.command()
def insert_roles():
    """Insert roles to database."""
    Role.insert_roles()


@app.cli.group()
def translate():
    """Group of translation cmd commands."""
    pass


@translate.command()
def update():
    """Update all languages."""
    if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
        raise RuntimeError("Extract command failed.")
    if os.system("pybabel update -i messages.pot -d app/translations"):
        raise RuntimeError("Update command failed.")
    os.remove("messages.pot")


@translate.command()
def compile():
    """Compile all languages."""
    if os.system("pybabel compile -d app/translations"):
        raise RuntimeError("Compile command failed.")
    

@translate.command()
@click.argument("lang")
def init(lang):
    """Initialize new language.
    
    :param lang: new app language.
    """
    if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
        raise RuntimeError("Extract command failed.")
    if os.system("pybabel init -i messages.pot -d app/translations -l " + lang):
        raise RuntimeError(f"Init {lang} language command failed.")
    os.remove(lang)


@app.cli.command()
@click.argument("class_names", nargs=-1)
def reindex(class_names):
    _classes = {
        "Song": Song,
        "User": User,
        "Comment": Comment
    }
    for class_name in class_names:
        if class_name in _classes:
            _classes[class_name].reindex()
  
  
@app.cli.command()
@click.argument("class_name", nargs=1)
def create_indx(class_name):
    """Create index.
    
    "param class_name: class to create index for.
    """
    _classes = {
        "Song": Song,
        "User": User,
        "Comment": Comment
    }
    create_index(_classes[class_name].__tablename__)
    
    
@app.cli.command()
@click.argument("song_name", nargs=1)
def delete_song(song_name):
    if song_name == "all":
        for song in Song.query.all():
            db.session.delete(song)
        db.session.commit()
    else:
        song = Song.query.filter_by(name=song_name).first()
        if song is not None:
            db.session.delete(song)
            db.session.commit()
            