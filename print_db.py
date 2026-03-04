from app import create_app

app = create_app()
print("SQLALCHEMY_DATABASE_URI =", app.config.get("SQLALCHEMY_DATABASE_URI"))
print("INSTANCE_PATH =", app.instance_path)