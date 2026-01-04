from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates"
    )

    app.config["SECRET_KEY"] = "funzone-secret-key"
    app.config.from_object("app.src.config.Config")

    db.init_app(app)

    
    from .Controllers.auth_controller import auth_bp

    app.register_blueprint(auth_bp)

    @app.route("/")
    def home():
        return "FunZone is alive"

    return app
