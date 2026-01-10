from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates"
    )

    app.config.from_object("app.src.config.Config")
    db.init_app(app)

    # 🔹 Create default admin
    from app.src.models.user import User
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            admin = User(
                name="Admin",
                email="admin@funzone.com",
                password="admin123",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

    # Register Blueprint
    from app.src.Controllers.auth_Controller import auth_bp
    app.register_blueprint(auth_bp)
    from app.src.Controllers.game_Controller import game_bp
    app.register_blueprint(game_bp)


    # Default route → login
    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    return app
