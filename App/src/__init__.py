from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates"
    )

    app.config.from_object("config.Config")

    db.init_app(app)

    @app.route("/")
    def home():
        return "FunZone is alive"

    return app
