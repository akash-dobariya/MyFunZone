from flask import Flask
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

    # ✅ DATABASE CONNECTION CHECK
    with app.app_context():
        try:
            db.engine.connect()
            print("✅ Database connected successfully")
        except Exception as e:
            print("❌ Database connection failed")
            print(e)

    @app.route("/")
    def home():
        return "FunZone is alive"

    return app
