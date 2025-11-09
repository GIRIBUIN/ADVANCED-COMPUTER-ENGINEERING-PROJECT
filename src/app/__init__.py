# src/app/__init__.py

from flask import Flask

def create_app():
    """ Flask app 생성 함수 """

    app = Flask(__name__)

    app.config.from_pyfile('config.py')

    from .db import db
    db.init_app(app)

    from . import routes
    app.register_blueprint(routes.bp)

    return app