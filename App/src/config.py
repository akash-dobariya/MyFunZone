class Config:
    SECRET_KEY = "funzone-secret"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:1234@localhost:5432/myfunzone"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
