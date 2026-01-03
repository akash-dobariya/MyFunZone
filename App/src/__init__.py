from flask import Flask

def create_app():
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates"
    )
    @app.route("/")
    def home():
        return "FunZone is alive"
    return app