from flask import Flask, redirect ,url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
print("LOADED: app/src/__init__.py")

def create_app():
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates"
    )

    # Config
    app.config.from_object("app.src.config.Config")

    # Init DB
    db.init_app(app)

    # Disable cache (logout + back button fix)
    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # Register Blueprint (ONLY ONCE)
    from app.src.Controllers.auth_Controller import auth_bp
    app.register_blueprint(auth_bp)

    # Home rou
    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    return app
