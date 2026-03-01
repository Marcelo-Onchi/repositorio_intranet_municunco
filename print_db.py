# print_db.py
from app import create_app

app = create_app()
print("SQLALCHEMY_DATABASE_URI =", app.config.get("SQLALCHEMY_DATABASE_URI"))