from app.src import create_app, db
from app.src.models import user, game

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ Tables created successfully")
